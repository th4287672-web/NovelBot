# novel_bot/src/plugins/ai_chat_system/data_manager.py

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database.models import User, ContentItem 
# [核心修复] 导入新的数据库持久化函数，并移除对旧文件操作函数的导入
from .services.data_persistence import (
    save_content_item_to_db, 
    delete_content_item_from_db, 
    rename_content_item_in_db
)
from .constants import DEFAULT_CHARACTER_NAME, DEFAULT_PRESET_NAME, DEFAULT_USER_PERSONA_NAME

logger = logging.getLogger("nonebot")

class DataManager:
    def __init__(self):
        # DataManager 现在是纯粹的服务协调者
        pass

    async def get_user_config(self, user_id: str, db: AsyncSession, db_user: Optional[User] = None) -> Dict[str, Any]:
        """
        从数据库获取用户配置。
        """
        if user_id == 'anonymous-user':
            return self._get_default_anonymous_config()

        user = db_user
        if not user:
            result = await db.execute(select(User).where(User.user_id == user_id))
            user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        return {
            "active_character": user.active_character_filename or DEFAULT_CHARACTER_NAME,
            "active_session_id": user.active_session_id,
            "user_persona": user.user_persona_filename or DEFAULT_USER_PERSONA_NAME,
            "preset": user.preset_filename or DEFAULT_PRESET_NAME,
            "active_modules": user.active_modules or {},
            "max_tokens": user.max_tokens or 4096,
            "world_info": user.session_world_info or [],
            "display_order": user.display_order or {},
            "regex_rules": user.regex_rules or [],
            "generation_profiles": user.generation_profiles or {},
            "deleted_public_items": user.deleted_public_items or [],
            "tts_voice_assignments": user.tts_voice_assignments or {},
            "tts_service_config": user.tts_service_config or {},
            "api_keys": user.api_keys or [],
            "llm_service_config": user.llm_service_config or {},
            "has_completed_onboarding": user.has_completed_onboarding or False,
        }

    def _get_default_anonymous_config(self) -> Dict[str, Any]:
        """为匿名用户提供一个默认的、只读的配置。"""
        return {
            "active_character": DEFAULT_CHARACTER_NAME,
            "active_session_id": None,
            "user_persona": DEFAULT_USER_PERSONA_NAME,
            "preset": DEFAULT_PRESET_NAME,
            "active_modules": {}, "max_tokens": 4096, "world_info": [],
            "display_order": {}, "regex_rules": [], "generation_profiles": {},
            "deleted_public_items": [], "tts_voice_assignments": {},
            "tts_service_config": {}, "api_keys": [], "llm_service_config": {},
            "has_completed_onboarding": True,
        }

    async def save_user_config(self, user_id: str, config_data: Dict, db: AsyncSession):
        """将配置数据保存回数据库中的 User 对象。"""
        if user_id == 'anonymous-user':
            logger.warning("Attempted to save config for anonymous user. Operation skipped.")
            return

        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"Cannot save config for non-existent user {user_id}")

        user.active_character_filename = config_data.get("active_character")
        user.active_session_id = config_data.get("active_session_id")
        user.user_persona_filename = config_data.get("user_persona")
        user.preset_filename = config_data.get("preset")
        user.active_modules = config_data.get("active_modules", {})
        user.max_tokens = config_data.get("max_tokens", 4096)
        user.session_world_info = config_data.get("world_info", [])
        user.display_order = config_data.get("display_order", {})
        user.regex_rules = config_data.get("regex_rules", [])
        user.generation_profiles = config_data.get("generation_profiles", {})
        user.deleted_public_items = config_data.get("deleted_public_items", [])
        user.tts_voice_assignments = config_data.get("tts_voice_assignments", {})
        user.tts_service_config = config_data.get("tts_service_config", {})
        user.api_keys = config_data.get("api_keys", [])
        user.llm_service_config = config_data.get("llm_service_config", {})
        user.has_completed_onboarding = config_data.get("has_completed_onboarding", False)
        
        await db.commit()

    async def get_all_public_data(self, db: AsyncSession) -> Dict[str, Dict]:
        """获取所有公共数据项。"""
        query = select(ContentItem).where(ContentItem.owner_id.is_(None))
        result = await db.execute(query)
        items = result.scalars().all()
        
        public_data: Dict[str, Dict] = {
            'character': {}, 'preset': {}, 'world_info': {}, 'group': {}
        }
        for item in items:
            if item.data_type in public_data:
                public_data[item.data_type][item.filename] = item.data
        return public_data

    # [核心重构] 将所有数据操作方法改为异步，并直接调用新的数据库持久化函数
    # 这些方法现在需要一个数据库会话 (db: AsyncSession) 作为参数
    async def save_user_data(self, db: AsyncSession, user_id: str, data_type: str, name: str, data: Dict, is_editing: bool = False) -> Dict[str, Any]:
        logger.info(f"DataManager: Saving '{name}' ({data_type}) for user '{user_id}' to DB.")
        return await save_content_item_to_db(db, user_id, data_type, name, data, is_editing)
        
    async def delete_user_data(self, db: AsyncSession, user_id: str, data_type: str, name: str) -> str:
        logger.info(f"DataManager: Deleting '{name}' ({data_type}) for user '{user_id}' from DB.")
        return await delete_content_item_from_db(db, user_id, data_type, name)
        
    async def rename_user_data(self, db: AsyncSession, user_id: str, data_type: str, old_name: str, new_name: str) -> str:
        logger.info(f"DataManager: Renaming '{old_name}' to '{new_name}' ({data_type}) for user '{user_id}' in DB.")
        return await rename_content_item_in_db(db, user_id, data_type, old_name, new_name)