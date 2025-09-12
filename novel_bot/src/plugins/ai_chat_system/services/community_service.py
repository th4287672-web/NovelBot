# novel_bot/src/plugins/ai_chat_system/services/community_service.py

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Literal
from nonebot import logger
from fastapi import Depends
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import DBSession
from ..database.models import SharedContent
from .data_persistence import BASE_DATA_PATH

_COMMUNITY_PATH = BASE_DATA_PATH / "community"
_CONTENT_PATH = _COMMUNITY_PATH / "content"

class CommunityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def initialize_dirs(self):
        _COMMUNITY_PATH.mkdir(exist_ok=True)
        _CONTENT_PATH.mkdir(exist_ok=True)
        for sub in ["character", "preset", "world_info"]:
            (_CONTENT_PATH / sub).mkdir(exist_ok=True)
        logger.info("CommunityService: Directories verified.")

    async def share_content(self, user_id: str, data_type: str, filename: str, data: Dict, description: str, tags: List[str]) -> Dict:
        file_dir = _CONTENT_PATH / data_type
        new_filepath = file_dir / f"{filename}.json"
        
        query = select(SharedContent).where(SharedContent.data_type == data_type, SharedContent.name == filename)
        existing_item = await self.db.execute(query)
        if existing_item.scalar_one_or_none():
            raise ValueError(f"一个名为 '{filename}' 的 {data_type} 已存在于社区中心。")
            
        with open(new_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        new_item = SharedContent(
            user_id=user_id,
            data_type=data_type,
            name=filename,
            description=description,
            tags=tags,
            file_path=str(new_filepath.relative_to(_COMMUNITY_PATH)),
            is_approved=True
        )
        self.db.add(new_item)
        await self.db.commit()
        await self.db.refresh(new_item)
        
        return {"id": new_item.id, "name": new_item.name, "data_type": new_item.data_type}

    async def browse_content(self, data_type: str, sort_by: str, page: int, limit: int) -> Tuple[List[Dict], int]:
        order_clause = SharedContent.created_at.desc() if sort_by == 'new' else SharedContent.downloads.desc()
        offset = (page - 1) * limit
        
        total_query = select(func.count()).select_from(SharedContent).where(SharedContent.data_type == data_type, SharedContent.is_approved == True)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar_one()

        query = select(SharedContent).where(SharedContent.data_type == data_type, SharedContent.is_approved == True).order_by(order_clause).limit(limit).offset(offset)
        result = await self.db.execute(query)
        rows = result.scalars().all()
        
        items = [{
            "id": row.id, "name": row.name, "description": row.description, "tags": row.tags,
            "downloads": row.downloads, "rating": row.rating, "user_id": row.user_id,
            "created_at": row.created_at.isoformat()
        } for row in rows]
        return items, total

    async def get_content_by_id(self, item_id: int) -> Dict | None:
        query = select(SharedContent).where(SharedContent.id == item_id)
        result = await self.db.execute(query)
        row = result.scalar_one_or_none()
        
        if not row: return None
        
        item = {
            "id": row.id, "name": row.name, "data_type": row.data_type,
            "file_path": row.file_path
        }
        content_path = _COMMUNITY_PATH / item['file_path']
        with open(content_path, "r", encoding="utf-8") as f:
            item['data'] = json.load(f)
        return item
    
    async def increment_download_count(self, item_id: int):
        stmt = update(SharedContent).where(SharedContent.id == item_id).values(downloads=SharedContent.downloads + 1)
        await self.db.execute(stmt)
        await self.db.commit()

def get_community_service(db: AsyncSession = DBSession) -> CommunityService:
    return CommunityService(db)