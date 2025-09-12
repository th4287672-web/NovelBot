# novel_bot/src/plugins/ai_chat_system/api_routes/aigc.py

from fastapi import APIRouter, Body, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from ..services.drawing.image_analyzer import get_prompt_from_image
from ..services.drawing.main_service import generate_image
from ..services.drawing.config import AI_DRAWING_CONFIG
from ..services.task_manager import TaskManager, get_task_manager

router = APIRouter(prefix="/aigc", tags=["AI Drawing (AIGC)"])

class Txt2ImgRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    width: Optional[int] = 512
    height: Optional[int] = 768
    steps: Optional[int] = 25
    cfg_scale: Optional[float] = 7.0
    seed: Optional[int] = -1
    model: Optional[str] = None

class Img2ImgRequest(Txt2ImgRequest):
    image_base64: str = Field(..., description="Base64 encoded source image")
    denoising_strength: Optional[float] = Field(default=0.75, ge=0, le=1)

class ImageToPromptRequest(BaseModel):
    image_base64: str
    strategy: str = "gemini"

async def run_generate_image_task(task_id: str, user_id: str, payload: dict, mode: str, task_manager_instance: TaskManager):
    try:
        await task_manager_instance.update_task_progress(task_id, 25, "上传并处理中")
        image_url = await generate_image(payload, mode)
        await task_manager_instance.update_task_progress(task_id, 100, "成功")
        await task_manager_instance.update_task(task_id, "success", {"image_url": image_url})
    except Exception as e:
        error_detail = str(e.detail) if isinstance(e, HTTPException) else str(e)
        await task_manager_instance.update_task(task_id, "failed", {"error": error_detail})

@router.post("/txt2img")
async def handle_txt2img(
    payload: Txt2ImgRequest, 
    user_id: str = Body(...), 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """接收文生图参数，提交到后台任务队列，并立即返回任务ID。"""
    task_id = await task_manager.create_task("txt2img", user_id)
    background_tasks.add_task(run_generate_image_task, task_id, user_id, payload.model_dump(), "txt2img", task_manager)
    return {"status": "processing", "task_id": task_id}

@router.post("/img2img")
async def handle_img2img(
    payload: Img2ImgRequest, 
    user_id: str = Body(...), 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """接收图生图参数，提交到后台任务队列，并立即返回任务ID。"""
    task_id = await task_manager.create_task("img2img", user_id)
    background_tasks.add_task(run_generate_image_task, task_id, user_id, payload.model_dump(), "img2img", task_manager)
    return {"status": "processing", "task_id": task_id}

@router.post("/image-to-prompt")
async def handle_image_to_prompt(payload: ImageToPromptRequest):
    """接收图像数据，并委托给图像分析服务生成提示词。"""
    try:
        prompt = await get_prompt_from_image(payload.model_dump())
        return {"status": "success", "prompt": prompt}
    except HTTPException as e:
        raise e

@router.get("/config")
async def get_drawing_config():
    """获取并返回当前激活的AI绘画服务信息和模型列表。"""
    active_service_key = AI_DRAWING_CONFIG.get("service_to_use", "perchance")
    if active_service_key not in AI_DRAWING_CONFIG:
        raise HTTPException(status_code=500, detail="Backend drawing service is misconfigured.")
    
    active_service_config = AI_DRAWING_CONFIG[active_service_key]
    
    return {
        "service_name": active_service_config.get("name"),
        "description": active_service_config.get("description"),
        "api_key_url": active_service_config.get("api_key_url"),
        "docs_url": active_service_config.get("docs_url"),
        "available_models": active_service_config.get("available_models", [])
    }