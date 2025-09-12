# novel_bot/src/plugins/ai_chat_system/api_routes/user_profile.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Body, BackgroundTasks
from pydantic import BaseModel
import tempfile
import shutil
from pathlib import Path

from ..database.session import get_db_session
from ..services.user_service import UserService, get_user_service
from ..services.task_manager import TaskManager, get_task_manager
from nonebot import logger

router = APIRouter(prefix="/user", tags=["User Profile"])

class UsernameUpdatePayload(BaseModel):
    new_username: str
    password: str

async def _run_avatar_upload_task(task_id: str, user_id: str, temp_file_path: str, original_filename: str, task_manager_instance: TaskManager):
    """后台执行头像上传和处理的任务，确保数据持久化。"""
    temp_path = Path(temp_file_path)
    # [诊断日志] 记录后台任务开始
    logger.info(f"[DIAG][Task:{task_id}] Avatar upload task started for user '{user_id}'.")
    
    async for db in get_db_session():
        try:
            await task_manager_instance.update_task_progress(task_id, 25, "上传文件中")
            
            service = UserService(db)
            avatar_url = await service.update_user_avatar(user_id, temp_path, original_filename)
            # [诊断日志] 记录从UserService返回的URL
            logger.info(f"[DIAG][Task:{task_id}] UserService returned new avatar URL: {avatar_url}")
            
            await task_manager_instance.update_task_progress(task_id, 100, "成功")
            
            success_payload = {"image_url": avatar_url}
            # [诊断日志] 记录最终发送给任务管理器的成功载荷
            logger.info(f"[DIAG][Task:{task_id}] Updating task to 'success' with payload: {success_payload}")
            await task_manager_instance.update_task(task_id, "success", success_payload)
            logger.info(f"头像上传任务 {task_id} 成功，返回URL: {avatar_url}")
        except Exception as e:
            # [诊断日志] 记录数据库回滚
            logger.error(f"[DIAG][Task:{task_id}] An error occurred in avatar upload task.")
            logger.error(f"头像上传失败 for user {user_id}: {e}", exc_info=True)
            error_detail = str(e)
            await task_manager_instance.update_task(task_id, "failed", {"error": f"头像上传失败: {error_detail}"})
        finally:
            if temp_path.exists():
                temp_path.unlink()

@router.post("/{user_id}/avatar")
async def upload_avatar(
    user_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: UserService = Depends(get_user_service),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """为指定用户上传或更新头像"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件。")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
    finally:
        await file.close()

    task_id = await task_manager.create_task("upload_avatar", user_id)
    background_tasks.add_task(_run_avatar_upload_task, task_id, user_id, temp_file_path, file.filename, task_manager)
    return {"status": "processing", "task_id": task_id}

@router.put("/{user_id}/username")
async def update_username(
    user_id: str,
    payload: UsernameUpdatePayload,
    service: UserService = Depends(get_user_service)
):
    """更新用户的用户名"""
    try:
        success = await service.update_username(user_id, payload.new_username, payload.password)
        if not success:
            raise HTTPException(status_code=401, detail="密码不正确，无法修改用户名。")
        return {"status": "success", "message": "用户名已更新。", "new_username": payload.new_username}
    except ValueError as e: 
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户名失败: {e}")