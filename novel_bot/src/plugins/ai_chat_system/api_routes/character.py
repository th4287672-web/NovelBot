# novel_bot/src/plugins/ai_chat_system/api_routes/character.py

import json
import shutil
import uuid
import time
from pathlib import Path
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends, BackgroundTasks
from nonebot import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from .. import global_state
from ..database.session import get_db_session, DBSession
from ..database.models import ContentItem
from ..services.task_manager import TaskManager, get_task_manager
from ..services.connection_manager import broadcast_status_update
from ..services.data_persistence import _USER_DATA_PATH

router = APIRouter(prefix="/character", tags=["Character Management"])

async def _run_upload_task(task_id: str, user_id: str, filename: str, temp_file_path: str, original_filename: str, task_manager_instance: TaskManager):
    temp_path = Path(temp_file_path)
    
    user_specific_dir = _USER_DATA_PATH / user_id
    image_dir = user_specific_dir / "character_images"
    
    logger.info(f"[DIAG][Task:{task_id}] Character image upload task started. Target directory: {image_dir}")
    
    async for db in get_db_session():
        try:
            await task_manager_instance.update_task_progress(task_id, 25, "上传文件中")
            
            image_dir.mkdir(parents=True, exist_ok=True)
            
            file_extension = Path(original_filename).suffix if Path(original_filename).suffix else '.webp'
            image_filename = f"{uuid.uuid4().hex[:12]}{file_extension}"
            image_path = image_dir / image_filename
            
            shutil.move(temp_path, image_path)
            
            await task_manager_instance.update_task_progress(task_id, 75, "更新数据库")
            
            image_url = f"/api/{user_id}/character_images/{image_filename}"
            logger.info(f"[DIAG][Task:{task_id}] Generated image URL: {image_url}")

            item_query = select(ContentItem).where(
                ContentItem.owner_id == user_id,
                ContentItem.data_type == 'character',
                ContentItem.filename == filename
            )
            result = await db.execute(item_query)
            item = result.scalar_one_or_none()

            if not item:
                raise FileNotFoundError(f"未在数据库中找到名为 '{filename}' 的角色或人设卡。")

            logger.info(f"[DIAG][Task:{task_id}] Found character item. Old image URL: {item.data.get('image')}")

            if item.data.get('image'):
                try:
                    old_image_filename = Path(item.data['image']).name
                    old_paths_to_check = [
                        image_dir / old_image_filename,
                        Path(__file__).resolve().parents[4] / "data" / "ai_chat" / "users" / "character_images" / old_image_filename
                    ]
                    for old_path in old_paths_to_check:
                        if old_path.exists() and old_path.is_file():
                            old_path.unlink()
                            logger.info(f"[DIAG][Task:{task_id}] Successfully deleted old image file: {old_path}")
                            break
                except Exception as e:
                    logger.warning(f"[DIAG][Task:{task_id}] Could not delete old image file {item.data['image']}: {e}")

            item.data['image'] = image_url
            flag_modified(item, "data")
            
            logger.info(f"[DIAG][Task:{task_id}] Staged change for DB commit. New image URL: {item.data['image']}")
            await db.commit()
            logger.info(f"[DIAG][Task:{task_id}] DB commit successful.")
            
            await broadcast_status_update({
                "event": "update", "dataType": "character", "filename": filename
            }, "data_update")
            
            logger.info(f"成功更新角色 '{filename}' 的图片URL到数据库: {image_url}")

            await task_manager_instance.update_task_progress(task_id, 100, "成功")
            
            success_payload = {"image_url": image_url, "filename": filename}
            logger.info(f"[DIAG][Task:{task_id}] Updating task to 'success' with payload: {success_payload}")
            await task_manager_instance.update_task(task_id, "success", success_payload)

        except Exception as e:
            await db.rollback()
            logger.error(f"[DIAG][Task:{task_id}] An error occurred, rolling back DB transaction.")
            logger.error(f"为角色 '{filename}' 上传图片失败: {e}", exc_info=True)
            error_detail = str(e)
            await task_manager_instance.update_task(task_id, "failed", {"error": error_detail})
        finally:
            if temp_path.exists():
                temp_path.unlink()

@router.post("/{user_id}/{filename}/image")
async def upload_character_image(
    user_id: str,
    filename: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    task_manager: TaskManager = Depends(get_task_manager)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件。")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
    finally:
        await file.close()

    task_id = await task_manager.create_task("upload_character_image", user_id)
    
    background_tasks.add_task(_run_upload_task, task_id, user_id, filename, temp_file_path, file.filename, task_manager)

    return {"status": "processing", "task_id": task_id}