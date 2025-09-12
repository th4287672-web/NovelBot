# novel_bot/src/plugins/ai_chat_system/api_routes/tasks.py

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List

from ..services.task_manager import TaskManager, get_task_manager

router = APIRouter(prefix="/tasks", tags=["Background Tasks"])

@router.get("/user/{user_id}")
async def get_tasks_for_user(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    task_manager: TaskManager = Depends(get_task_manager)
) -> List[dict]:
    """获取指定用户的所有历史任务列表，支持分页。"""
    tasks = await task_manager.get_tasks_by_user(user_id, limit, offset)
    return tasks

@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    根据任务ID获取后台任务的状态和结果。
    """
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task