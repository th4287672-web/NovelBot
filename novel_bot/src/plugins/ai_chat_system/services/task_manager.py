# novel_bot/src/plugins/ai_chat_system/services/task_manager.py

import uuid
import time
import json
from typing import Dict, Any, Literal, List, Optional
from pathlib import Path
from nonebot import logger
from fastapi import HTTPException, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import DBSession
from ..database.models import Task

TaskStatus = Literal["pending", "processing", "success", "failed"]

class TaskManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_type: str, user_id: str) -> str:
        task_id = str(uuid.uuid4())
        current_time = time.time()
        new_task = Task(
            id=task_id,
            user_id=user_id,
            task_type=task_type,
            status="processing",
            created_at=current_time,
            updated_at=current_time,
            start_time=current_time
        )
        self.db.add(new_task)
        await self.db.commit()
        logger.info(f"Task created: ID={task_id}, Type={task_type}, User={user_id}")
        return task_id

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        query = select(Task).where(Task.id == task_id)
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task: return None
        return self._task_to_dict(task)

    async def get_tasks_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        query = select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        return [self._task_to_dict(task) for task in tasks]

    async def update_task(self, task_id: str, status: TaskStatus, data: Any = None):
        current_time = time.time()
        values_to_update = {"status": status, "updated_at": current_time}
        
        if status in ["success", "failed"]:
            values_to_update["end_time"] = current_time
            if status == "success":
                values_to_update["result"] = data
            else:
                values_to_update["error"] = data
        
        stmt = update(Task).where(Task.id == task_id).values(**values_to_update)
        await self.db.execute(stmt)
        await self.db.commit()
        logger.info(f"Task updated: ID={task_id}, Status={status}")
        
    async def update_task_progress(self, task_id: str, progress: int, status_text: str):
        current_time = time.time()
        stmt = update(Task).where(Task.id == task_id).values(
            progress=progress, 
            status_text=status_text, 
            updated_at=current_time
        )
        await self.db.execute(stmt)
        await self.db.commit()
        logger.debug(f"Task progress: ID={task_id}, Progress={progress}%, Status Text='{status_text}'")

    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        return {
            "id": task.id, "user_id": task.user_id, "task_type": task.task_type,
            "status": task.status, "progress": task.progress, "status_text": task.status_text,
            "created_at": task.created_at, "updated_at": task.updated_at,
            "start_time": task.start_time, "end_time": task.end_time,
            "result": task.result, "error": task.error
        }

def get_task_manager(db: AsyncSession = DBSession) -> TaskManager:
    return TaskManager(db)