# novel_bot/src/plugins/ai_chat_system/services/user_service.py

import json
import random
import string
import uuid
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from passlib.context import CryptContext
from nonebot import logger
from fastapi import UploadFile, Depends
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import DBSession
from ..database.models import User
from .. import global_state
from .data_persistence import _USER_DATA_PATH

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def create_user(
        self, username: str, password: str, account_digits: int, 
        security_questions: List[Dict], anonymous_user_id: str
    ) -> Dict:
        existing_user = await self.db.execute(select(User).where(User.username == username))
        if existing_user.scalar_one_or_none():
            raise ValueError(f"用户名 '{username}' 已被注册。")

        while True:
            account_number = ''.join(random.choices(string.digits, k=account_digits))
            existing_account = await self.db.execute(select(User).where(User.account_number == account_number))
            if not existing_account.scalar_one_or_none():
                break
        
        permanent_user_id = str(uuid.uuid4())
        password_hash = self.get_password_hash(password)
        questions_hash = self.get_password_hash(json.dumps(security_questions, sort_keys=True))

        new_user = User(
            user_id=permanent_user_id,
            username=username,
            account_number=account_number,
            password_hash=password_hash,
            security_questions_hash=questions_hash
        )
        self.db.add(new_user)
        await self.db.commit()
        
        logger.info(f"New user created: {username} ({account_number})")
        return {"user_id": permanent_user_id, "username": username, "account_number": account_number}

    async def authenticate_user(self, username_or_account: str, password: str) -> Optional[Dict]:
        query = select(User).where((User.username == username_or_account) | (User.account_number == username_or_account))
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Login attempt failed for '{username_or_account}': User not found.")
            return None
        
        if self.verify_password(password, user.password_hash):
            logger.info(f"User '{username_or_account}' authenticated successfully.")
            return {
                "user_id": user.user_id, "username": user.username,
                "account_number": user.account_number, "avatar": user.avatar
            }
        else:
            logger.warning(f"Login attempt failed for '{username_or_account}': Password mismatch.")
            return None

    async def update_username(self, user_id: str, new_username: str, password: str) -> bool:
        existing_user = await self.db.execute(select(User).where(User.username == new_username, User.user_id != user_id))
        if existing_user.scalar_one_or_none():
            raise ValueError(f"用户名 '{new_username}' 已被占用。")

        user_result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalar_one_or_none()
        if not user or not self.verify_password(password, user.password_hash):
            return False

        user.username = new_username
        await self.db.commit()
        logger.info(f"User {user_id} successfully changed username to '{new_username}'.")
        return True

    async def delete_user(self, user_id: str, password: str) -> bool:
        user_result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalar_one_or_none()

        if not user or not self.verify_password(password, user.password_hash):
            logger.warning(f"Account deletion attempt failed for user ID '{user_id}': Incorrect password or user not found.")
            return False

        username = user.username
        if user.avatar:
            try:
                user_avatar_path = _USER_DATA_PATH / user_id / "avatars"
                avatar_filename = Path(user.avatar).name
                avatar_full_path = user_avatar_path / avatar_filename
                if avatar_full_path.exists():
                    avatar_full_path.unlink()
            except Exception as e: 
                logger.error(f"Error deleting avatar file for user {username}: {e}")

        await self.db.delete(user)
        await self.db.commit()
        
        logger.info(f"User '{username}' (ID: {user_id}) has been successfully deleted from database.")
        return True

    async def get_user_security_questions(self, account_number: str) -> Optional[List[str]]:
        return ["系统安全升级，请联系管理员重置密码。", "System security upgraded.", "Please contact admin for password reset."]

    async def reset_password_with_answers(self, account_number: str, answers: List[str], new_password: str) -> bool:
        logger.warning(f"Password reset attempted for account {account_number}. This method is deprecated.")
        return False

    async def update_user_avatar(self, user_id: str, avatar_file_path: Path, original_filename: str) -> str:
        user_avatar_dir = _USER_DATA_PATH / user_id / "avatars"
        user_avatar_dir.mkdir(parents=True, exist_ok=True)
        
        file_extension = Path(original_filename).suffix or '.webp'
        avatar_filename = f"{uuid.uuid4().hex[:12]}{file_extension}"
        avatar_path = user_avatar_dir / avatar_filename

        shutil.move(str(avatar_file_path), avatar_path)
        
        avatar_url = f"/api/{user_id}/avatars/{avatar_filename}"
        
        user_result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            logger.info(f"[DIAG] Updating avatar for user '{user.username}'. Old URL: {user.avatar}")

            if user.avatar:
                try:
                    old_avatar_filename = Path(user.avatar).name
                    old_avatar_path = user_avatar_dir / old_avatar_filename
                    if old_avatar_path.exists() and old_avatar_path.is_file():
                        old_avatar_path.unlink()
                        logger.info(f"[DIAG] Successfully deleted old avatar file: {old_avatar_path.name}")
                except Exception as e:
                    logger.warning(f"[DIAG] Could not delete old avatar file {user.avatar}: {e}")
            
            user.avatar = avatar_url
            logger.info(f"[DIAG] Staged change for DB commit. New avatar URL: {user.avatar}")
            await self.db.commit()
            logger.info(f"[DIAG] DB commit successful for avatar update.")
        
        return avatar_url

def get_user_service(db: AsyncSession = DBSession):
    return UserService(db)