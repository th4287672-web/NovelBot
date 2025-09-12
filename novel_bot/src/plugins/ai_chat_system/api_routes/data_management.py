import json
from typing import Dict, Any
import zipfile
from io import BytesIO
from pathlib import Path
import tempfile
import os

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from nonebot import logger

from .. import global_state
from ..services.task_manager import TaskManager, get_task_manager

router = APIRouter(prefix="/data", tags=["Data Import/Export"])

async def run_export_task(task_id: str, user_id: str, task_manager_instance: TaskManager):
    dm = global_state.data_manager
    if not dm:
        await task_manager_instance.update_task(task_id, "failed", {"error": "DataManager not initialized."})
        return

    try:
        await task_manager_instance.update_task_progress(task_id, 10, "初始化导出...")

        temp_dir = Path(tempfile.gettempdir()) / "mynovelbot_exports"
        temp_dir.mkdir(exist_ok=True)
        zip_path = temp_dir / f"{task_id}.zip"

        data_types_to_export = ["character", "preset", "world_info", "group"]
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            processed_count = 0
            total_count = len(data_types_to_export)

            for data_type in data_types_to_export:
                await task_manager_instance.update_task_progress(
                    task_id, 
                    10 + int((processed_count / total_count) * 80), 
                    f"正在打包 {data_type}..."
                )
                
                user_data_path = dm._get_user_data_path(user_id, data_type)
                if user_data_path.exists():
                    for json_file in user_data_path.glob("*.json"):
                        zf.write(json_file, arcname=f"{data_type}s/{json_file.name}")
                
                processed_count += 1
        
        download_url = f"/api/data/download/{task_id}"
        await task_manager_instance.update_task_progress(task_id, 100, "打包完成")
        await task_manager_instance.update_task(
            task_id, 
            "success", 
            {"message": "数据打包完成，可以下载。", "download_url": download_url}
        )
        logger.info(f"Data export task {task_id} for user {user_id} completed successfully.")

    except Exception as e:
        logger.error(f"Failed to export data for user {user_id}: {e}", exc_info=True)
        await task_manager_instance.update_task(task_id, "failed", {"error": f"导出处理失败: {str(e)}"})


@router.post("/export/{user_id}")
async def export_all_user_data(
    user_id: str, 
    background_tasks: BackgroundTasks,
    task_manager: TaskManager = Depends(get_task_manager)
):
    task_id = await task_manager.create_task("export_data", user_id)
    background_tasks.add_task(run_export_task, task_id, user_id, task_manager)
    return {"status": "processing", "task_id": task_id}


@router.get("/download/{task_id}")
async def download_exported_data(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    task = await task_manager.get_task(task_id)
    if not task or task['status'] != 'success':
        raise HTTPException(status_code=404, detail="任务不存在、未完成或已失败。")

    temp_dir = Path(tempfile.gettempdir()) / "mynovelbot_exports"
    file_path = temp_dir / f"{task_id}.zip"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="导出文件已过期或被清理。")

    filename = f"MyNovelBot_backup_{task['user_id']}_{int(task['created_at'])}.zip"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/zip',
        background=BackgroundTask(os.remove, file_path)
    )


async def run_import_task(task_id: str, user_id: str, file_content: bytes, task_manager_instance: TaskManager):
    dm = global_state.data_manager
    if not dm:
        await task_manager_instance.update_task(task_id, "failed", {"error": "DataManager not initialized."})
        return

    try:
        await task_manager_instance.update_task_progress(task_id, 20, "解析文件中")
        import_data = json.loads(file_content)
    except json.JSONDecodeError:
        await task_manager_instance.update_task(task_id, "failed", {"error": "解析JSON失败，文件可能已损坏。"})
        return
    
    report = {
        "characters": {"imported": 0, "skipped": 0},
        "presets": {"imported": 0, "skipped": 0},
        "world_info": {"imported": 0, "skipped": 0},
        "groups": {"imported": 0, "skipped": 0},
    }
    data_map = {
        "characters": "character", "presets": "preset",
        "world_info": "world_info", "groups": "group",
    }
    
    total_items = sum(len(import_data.get(key, [])) for key in data_map.keys())
    processed_items = 0

    try:
        for data_key, data_type in data_map.items():
            if data_key in import_data:
                current_data = dm.get_available_data(user_id, data_type)
                for name, data in import_data[data_key].items():
                    if name not in current_data:
                        data['is_private'] = True
                        dm.save_user_data(user_id, data_type, name, data, is_editing=False)
                        report[data_key]["imported"] += 1
                    else:
                        report[data_key]["skipped"] += 1
                    
                    processed_items += 1
                    progress = 20 + int((processed_items / total_items) * 75) if total_items > 0 else 95
                    await task_manager_instance.update_task_progress(task_id, progress, f"正在处理 {data_type}...")

        await task_manager_instance.update_task_progress(task_id, 100, "完成")
        await task_manager_instance.update_task(task_id, "success", {"report": report})

    except Exception as e:
        logger.error(f"Failed to import data for user {user_id}: {e}", exc_info=True)
        await task_manager_instance.update_task(task_id, "failed", {"error": f"导入处理失败: {str(e)}"})


@router.post("/import/{user_id}")
async def import_all_user_data(
    user_id: str, 
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    task_manager: TaskManager = Depends(get_task_manager)
):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .json file.")

    content = await file.read()
    
    task_id = await task_manager.create_task("import_data", user_id)
    background_tasks.add_task(run_import_task, task_id, user_id, content, task_manager)

    return {"status": "processing", "task_id": task_id}