# novel_bot/src/plugins/ai_chat_system/api_routes/community.py

from fastapi import APIRouter, Body, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

from ..services.community_service import CommunityService, get_community_service
from .. import global_state

router = APIRouter(prefix="/community", tags=["Community Hub"])

class SharePayload(BaseModel):
    user_id: str
    data_type: Literal['character', 'preset', 'world_info']
    filename: str
    description: str = Field(..., max_length=500)
    tags: List[str] = Field(default_factory=list)

@router.post("/share")
async def share_content(
    payload: SharePayload, 
    service: CommunityService = Depends(get_community_service)
):
    """
    用户分享私有内容到社区中心。
    """
    if not global_state.data_manager:
        raise HTTPException(status_code=503, detail="DataManager not initialized.")
    
    all_data = global_state.data_manager.get_available_data(payload.user_id, payload.data_type)
    content_data = all_data.get(payload.filename)

    if not content_data or not content_data.get('is_private'):
        raise HTTPException(status_code=404, detail=f"未找到用户 '{payload.user_id}' 的私有内容 '{payload.filename}'。")
    
    try:
        # 移除is_private等前端特定字段
        data_to_share = {k: v for k, v in content_data.items() if k not in ['is_private', 'filename']}
        
        shared_item = await service.share_content(
            user_id=payload.user_id,
            data_type=payload.data_type,
            filename=payload.filename,
            data=data_to_share,
            description=payload.description,
            tags=payload.tags
        )
        return {"status": "success", "message": "内容已成功分享至社区！", "item": shared_item}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分享失败: {e}")

@router.get("/browse")
async def browse_content(
    data_type: Literal['character', 'preset', 'world_info'] = 'character',
    sort_by: Literal['hot', 'new'] = 'new',
    page: int = 1,
    limit: int = 20,
    service: CommunityService = Depends(get_community_service)
):
    """
    浏览社区分享的内容。
    """
    items, total = await service.browse_content(data_type, sort_by, page, limit)
    return {"status": "success", "items": items, "total": total, "page": page, "limit": limit}

@router.post("/import/{item_id}")
async def import_content(
    item_id: int,
    payload: Dict[str, str] = Body(...),
    service: CommunityService = Depends(get_community_service)
):
    """
    用户从社区导入内容到自己的私有数据中。
    """
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required.")
        
    if not global_state.data_manager:
        raise HTTPException(status_code=503, detail="DataManager not initialized.")
        
    try:
        item = await service.get_content_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Content not found.")
        
        # 调用 DataManager 保存数据
        save_result = global_state.data_manager.save_user_data(
            user_id=user_id,
            data_type=item['data_type'],
            name=item['name'],
            data=item['data']
        )

        if save_result["success"]:
            # 导入成功后，增加下载计数
            await service.increment_download_count(item_id)
            return {"status": "success", "message": f"'{item['name']}' 已成功导入！", "filename": save_result["filename"]}
        else:
            raise HTTPException(status_code=500, detail=save_result.get("error", "保存导入数据时失败。"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {e}")