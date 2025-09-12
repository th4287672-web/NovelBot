import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import os
import shutil
import uuid
import time
import logging

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database.models import Session, ChatMessage, User

logger = logging.getLogger("nonebot")

class SessionManager:
    async def get_sessions_for_character(self, user_id: str, char_filename: str, db: AsyncSession) -> List[Dict]:
        if user_id == 'anonymous-user':
            return []
            
        stmt = select(Session).where(
            Session.owner_id == user_id,
            Session.character_filename == char_filename
        ).order_by(Session.last_updated_at.desc())
        
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        
        return [
            {"id": s.id, "title": s.title, "created": s.created_at, "last_updated": s.last_updated_at}
            for s in sessions
        ]

    async def create_new_session(self, user_id: str, char_filename: str, db: AsyncSession) -> Optional[Dict]:
        if user_id == 'anonymous-user':
            logger.warning("Attempted to create session for anonymous user.")
            return None

        session_id = str(uuid.uuid4())
        timestamp = time.time()
        
        new_session = Session(
            id=session_id,
            owner_id=user_id,
            character_filename=char_filename,
            title="新对话",
            created_at=timestamp,
            last_updated_at=timestamp
        )
        
        try:
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            
            metadata = {"id": new_session.id, "title": new_session.title, "created": new_session.created_at, "last_updated": new_session.last_updated_at}
            return metadata
        except Exception as e:
            await db.rollback()
            logger.error(f"SessionManager: Failed to create new session in DB for user {user_id}: {e}", exc_info=True)
            return None

    async def get_session_history(self, user_id: str, session_id: str, db: AsyncSession) -> Optional[List[Dict]]:
        if user_id == 'anonymous-user':
            return []

        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp)
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        return [
            {"role": msg.role, "content": msg.content, "tokenUsage": msg.token_usage}
            for msg in messages
        ]

    async def update_session_history(self, user_id: str, session_id: str, history: List[Dict], db: AsyncSession) -> bool:
        if user_id == 'anonymous-user':
            return False

        try:
            async with db.begin_nested():
                del_stmt = delete(ChatMessage).where(ChatMessage.session_id == session_id)
                await db.execute(del_stmt)

                new_messages = [
                    ChatMessage(
                        session_id=session_id,
                        timestamp=time.time() + i * 0.001,
                        role=msg.get("role"),
                        content=msg.get("content"),
                        token_usage=msg.get("tokenUsage")
                    ) for i, msg in enumerate(history[-100:])
                ]
                db.add_all(new_messages)
                
                update_stmt = update(Session).where(Session.id == session_id).values(last_updated_at=time.time())
                await db.execute(update_stmt)
            
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"SessionManager: Failed to update session history in DB for session {session_id}: {e}", exc_info=True)
            return False

    async def delete_session(self, user_id: str, session_id: str, db: AsyncSession) -> bool:
        try:
            stmt = delete(Session).where(Session.id == session_id, Session.owner_id == user_id)
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"SessionManager: Failed to delete session {session_id} from DB: {e}", exc_info=True)
            return False

    async def delete_all_sessions_for_character(self, user_id: str, char_filename: str, db: AsyncSession) -> bool:
        try:
            stmt = delete(Session).where(Session.owner_id == user_id, Session.character_filename == char_filename)
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"SessionManager: Failed to delete all sessions for char {char_filename} from DB: {e}", exc_info=True)
            return False

    async def rename_character_sessions_dir(self, user_id: str, old_char_filename: str, new_char_filename: str, db: AsyncSession) -> bool:
        try:
            stmt = update(Session).where(
                Session.owner_id == user_id,
                Session.character_filename == old_char_filename
            ).values(character_filename=new_char_filename)
            await db.execute(stmt)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"SessionManager: Failed to rename character sessions in DB for {old_char_filename}: {e}", exc_info=True)
            return False

    async def rename_session(self, user_id: str, session_id: str, new_title: str, db: AsyncSession) -> bool:
        try:
            stmt = update(Session).where(
                Session.id == session_id,
                Session.owner_id == user_id
            ).values(title=new_title, last_updated_at=time.time())
            
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"SessionManager: Failed to rename session {session_id} in DB: {e}", exc_info=True)
            return False