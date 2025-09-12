# novel_bot/src/plugins/ai_chat_system/services/data_persistence.py

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .. import global_state
from ..database.models import ContentItem

logger = logging.getLogger("nonebot")

_PROJECT_ROOT = Path(__file__).resolve().parents[5]
BASE_DATA_PATH = _PROJECT_ROOT / "novel_bot" / "data" / "ai_chat"
_USER_DATA_PATH = BASE_DATA_PATH / "users"

def get_user_data_path(user_id: str, data_type: str) -> Path:
    """获取并确保用户特定数据类型的目录存在"""
    dir_map = {
        "character": "characters", 
        "preset": "presets", 
        "world_info": "world_info", 
        "group": "groups",
        "memory": "memories"
    }
    dir_name = dir_map.get(data_type)
    if not dir_name: raise ValueError(f"Invalid data_type '{data_type}'")
    path = _USER_DATA_PATH / user_id / dir_name
    path.mkdir(parents=True, exist_ok=True)
    return path

# [核心重构] 将所有文件操作替换为数据库操作
# -------------------------------------------------------------------------
async def save_content_item_to_db(db: AsyncSession, user_id: str, data_type: str, filename: str, data: Dict, is_editing: bool) -> Dict[str, Any]:
    try:
        if is_editing:
            # 更新现有条目
            stmt = update(ContentItem).where(
                ContentItem.owner_id == user_id,
                ContentItem.data_type == data_type,
                ContentItem.filename == filename
            ).values(data=data)
            await db.execute(stmt)
        else:
            # 创建新条目
            # 检查是否存在同名项
            existing_item_query = select(ContentItem).where(
                ContentItem.owner_id == user_id,
                ContentItem.data_type == data_type,
                ContentItem.filename == filename
            )
            existing_item = await db.execute(existing_item_query)
            if existing_item.scalar_one_or_none():
                # 如果已存在，则转为更新操作以避免冲突
                stmt = update(ContentItem).where(
                    ContentItem.owner_id == user_id,
                    ContentItem.data_type == data_type,
                    ContentItem.filename == filename
                ).values(data=data)
                await db.execute(stmt)
            else:
                new_item = ContentItem(owner_id=user_id, data_type=data_type, filename=filename, data=data)
                db.add(new_item)
        
        await db.commit()
        return {"success": True, "filename": filename, "data": data}
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"DB Persistence: Integrity error saving item for {user_id} - {data_type}/{filename}: {e}")
        return {"success": False, "error": f"A unique constraint was violated. An item with this name might already exist."}
    except Exception as e:
        await db.rollback()
        logger.error(f"DB Persistence: Error saving item for {user_id} - {data_type}/{filename}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

async def delete_content_item_from_db(db: AsyncSession, user_id: str, data_type: str, filename: str) -> str:
    try:
        stmt = delete(ContentItem).where(
            ContentItem.owner_id == user_id,
            ContentItem.data_type == data_type,
            ContentItem.filename == filename
        )
        result = await db.execute(stmt)
        await db.commit()
        if result.rowcount > 0:
            return f"成功删除您的私有{data_type} '{filename}'。"
        else:
            return f"错误: 未找到您名为 '{filename}' 的私有{data_type}。"
    except Exception as e:
        await db.rollback()
        return f"从数据库删除时发生错误: {e}"

async def rename_content_item_in_db(db: AsyncSession, user_id: str, data_type: str, old_filename: str, new_filename: str) -> str:
    try:
        # 检查新文件名是否已存在
        existing_item_query = select(ContentItem).where(
            ContentItem.owner_id == user_id,
            ContentItem.data_type == data_type,
            ContentItem.filename == new_filename
        )
        if (await db.execute(existing_item_query)).scalar_one_or_none():
            return f"❌ 错误：名称 '{new_filename}' 已被占用。"

        # 更新文件名
        stmt = update(ContentItem).where(
            ContentItem.owner_id == user_id,
            ContentItem.data_type == data_type,
            ContentItem.filename == old_filename
        ).values(filename=new_filename)
        
        result = await db.execute(stmt)
        if result.rowcount == 0:
            await db.rollback()
            return f"❌ 错误：找不到名为 '{old_filename}' 的私有数据。"
            
        await db.commit()
        return f"✅ 成功将 '{old_filename}' 重命名为 '{new_filename}'。"
    except Exception as e:
        await db.rollback()
        return f"❌ 重命名时发生严重错误: {e}"