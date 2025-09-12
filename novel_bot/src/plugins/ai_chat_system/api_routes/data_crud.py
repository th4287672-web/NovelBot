# novel_bot/src/plugins/ai_chat_system/api_routes/data_crud.py

from fastapi import APIRouter, Body, HTTPException, Query, Request, Response
from typing import Dict, List, Optional
import hashlib
import json
import time
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .. import global_state
from ..services.connection_manager import broadcast_status_update
from ..database.session import DBSession
from ..database.models import User, ContentItem
from ..services.data_persistence import save_content_item_to_db, delete_content_item_from_db, rename_content_item_in_db

router = APIRouter(tags=["Data CRUD"])

@router.get("/data/{user_id}/{data_type}")
async def get_paginated_data(
    request: Request,
    response: Response,
    user_id: str,
    data_type: str,
    db: AsyncSession = DBSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("name"),
    search: Optional[str] = Query(None)
):
    if data_type not in ["character", "preset", "world_info", "group", "persona"]:
        raise HTTPException(status_code=400, detail="Invalid data type specified.")

    if user_id == 'anonymous-user':
        return { "items": [], "total_items": 0, "total_pages": 1, "current_page": 1 }

    is_persona_request = data_type == "persona"
    actual_data_type = "character" if is_persona_request else data_type

    query = select(ContentItem).where(
        ContentItem.data_type == actual_data_type,
        or_(ContentItem.owner_id == user_id, ContentItem.owner_id.is_(None))
    )
    
    if is_persona_request:
        query = query.where(ContentItem.data['is_user_persona'].as_boolean() == True)
    else:
        query = query.where(ContentItem.data['is_user_persona'].as_boolean().isnot(True))

    if search:
        search_lower = f"%{search.lower()}%"
        query = query.where(
            or_(
                ContentItem.data['displayName'].as_string().ilike(search_lower),
                ContentItem.data['name'].as_string().ilike(search_lower),
                ContentItem.data['description'].as_string().ilike(search_lower)
            )
        )
        
    count_query = select(func.count()).select_from(query.alias())
    total_items_result = await db.execute(count_query)
    total_items = total_items_result.scalar_one()
    
    full_result = await db.execute(query)
    all_items = full_result.scalars().all()

    items = []
    for item in all_items:
        item_data = item.data
        item_data['filename'] = item.filename
        item_data['is_private'] = item.owner_id == user_id
        item_data['owner_id'] = item.owner_id
        items.append(item_data)
        
    user_config_result = await db.execute(select(User.display_order).where(User.user_id == user_id))
    display_order_dict = user_config_result.scalar_one_or_none() or {}
    
    display_order_key = "personas" if is_persona_request else f"{actual_data_type}s"
    order = display_order_dict.get(display_order_key, [])
    
    if order:
        order_map = {filename: i for i, filename in enumerate(order)}
        items.sort(key=lambda x: order_map.get(x['filename'], float('inf')))
    else:
        items.sort(key=lambda x: (not x['is_private'], x.get(sort_by, x['filename'])))

    total_pages = (total_items + limit - 1) // limit if limit > 0 else 1
    start = (page - 1) * limit
    end = start + limit
    paginated_items = items[start:end]
    
    content_json = json.dumps(paginated_items, sort_keys=True).encode('utf-8')
    unique_content = content_json + str(time.time()).encode('utf-8')
    current_etag = f'"{hashlib.md5(unique_content).hexdigest()}"'
    
    if request.headers.get('if-none-match') == current_etag:
        return Response(status_code=304)
        
    response.headers["ETag"] = current_etag

    return {
        "items": paginated_items,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
    }


@router.post("/data/{user_id}/{data_type}/{name}")
async def create_or_update_data(
    user_id: str, data_type: str, name: str, data: Dict = Body(...), db: AsyncSession = DBSession
):
    if data_type not in ["character", "preset", "world_info", "group"]:
        raise HTTPException(status_code=400, detail="Invalid data type specified.")

    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Data name cannot be empty.")
    
    is_editing = data.pop('_is_editing', False)

    save_result = await save_content_item_to_db(db, user_id, data_type, name, data, is_editing=is_editing)
    
    if save_result.get("success"):
        await broadcast_status_update({
            "event": "update",
            "dataType": data_type,
            "filename": save_result.get("filename")
        }, "data_update")
        return {
            "status": "success",
            "message": f"{data_type.capitalize()} '{name}' saved.",
            "filename": save_result.get("filename"),
            "data": save_result.get("data")
        }

    raise HTTPException(status_code=500, detail=save_result.get("error", f"Failed to save {data_type}."))


@router.delete("/data/{user_id}/{data_type}/{name}")
async def delete_data(user_id: str, data_type: str, name: str, db: AsyncSession = DBSession):
    if data_type not in ["character", "preset", "world_info", "group"]:
        raise HTTPException(status_code=400, detail="Invalid data type specified.")

    result_message = await delete_content_item_from_db(db, user_id, data_type, name)
    
    if "成功" in result_message:
        await broadcast_status_update({
            "event": "delete",
            "dataType": data_type,
            "filename": name
        }, "data_update")
        return {"status": "success", "message": result_message}
    else:
        raise HTTPException(status_code=404, detail=result_message)


@router.patch("/data/{user_id}/{data_type}/{old_name}")
async def rename_data(user_id: str, data_type: str, old_name: str, payload: Dict = Body(...), db: AsyncSession = DBSession):
    new_name = payload.get("new_name")
    if not new_name:
        raise HTTPException(status_code=400, detail="Missing 'new_name' in payload.")

    if data_type not in ["character", "preset", "world_info", "group"]:
        raise HTTPException(status_code=400, detail="Invalid data type specified.")
    
    result = await rename_content_item_in_db(db, user_id, data_type, old_name, new_name)

    if "成功" in result:
        await broadcast_status_update({
            "event": "rename",
            "dataType": data_type,
            "oldFilename": old_name,
            "newFilename": new_name
        }, "data_update")
        return {"status": "success", "message": result}
    else:
        if "已被占用" in result:
            raise HTTPException(status_code=409, detail=result)
        else:
            raise HTTPException(status_code=400, detail=result)