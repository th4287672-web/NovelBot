# novel_bot/src/plugins/ai_chat_system/api_routes/tts.py

from fastapi import APIRouter, Body, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
import base64
import logging
from typing import Dict, List, Tuple, Optional

from ..services.tts_service import tts_client
from ..services.tts_merger import synthesize_and_merge_audio
from ..services.task_manager import TaskManager, get_task_manager

router = APIRouter(prefix="/tts", tags=["TTS"])
logger = logging.getLogger("nonebot")

class SynthesizeParams(BaseModel):
    rate: Optional[int] = Field(default=50, description="语速 (0-100, 50为默认)")
    volume: Optional[int] = Field(default=50, description="音量 (0-100, 50为默认)")
    pitch: Optional[int] = Field(default=50, description="音调 (0-100, 50为默认)")

class SynthesizeBatchRequest(BaseModel):
    user_id: str
    segments: List[Tuple[str, str]] = Field(..., description="A list of (text, voice_name) tuples")
    params: Optional[SynthesizeParams] = Field(default_factory=SynthesizeParams)

@router.get("/voices")
async def get_available_voices():
    try:
        voices = await tts_client.get_voices()
        return {"status": "success", "voices": voices}
    except Exception as e:
        logger.error(f"TTS API: Failed to get voices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(payload: Dict = Body(...)):
    text = payload.get("text")
    voice = payload.get("voice", "zh-CN-XiaoxiaoNeural")
    user_id = payload.get("user_id")

    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required.")

    try:
        audio_bytes = await tts_client.get_audio(user_id, text, voice)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        return {
            "status": "success",
            "audio_data": f"data:audio/mp3;base64,{audio_base64}",
        }
    except Exception as e:
        logger.error(f"TTS API: Failed to synthesize audio: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to synthesize audio: {str(e)}"
        )

async def run_synthesize_batch_task(task_id: str, payload: SynthesizeBatchRequest, task_manager_instance: TaskManager):
    try:
        await task_manager_instance.update_task_progress(task_id, 20, "初始化合成")
        
        merged_audio_bytes = await synthesize_and_merge_audio(
            user_id=payload.user_id,
            segments=payload.segments,
            rate=payload.params.rate,
            volume=payload.params.volume,
            pitch=payload.params.pitch,
            task_id=task_id,
            task_manager_instance=task_manager_instance
        )
        audio_base64 = base64.b64encode(merged_audio_bytes).decode("utf-8")
        result = {"audio_data": f"data:audio/mp3;base64,{audio_base64}"}
        
        await task_manager_instance.update_task_progress(task_id, 100, "成功")
        await task_manager_instance.update_task(task_id, "success", result)
    except Exception as e:
        logger.error(f"TTS API: Failed to batch synthesize audio in background: {e}", exc_info=True)
        await task_manager_instance.update_task(task_id, "failed", {"error": str(e)})


@router.post("/synthesize-batch")
async def synthesize_batch_speech(
    payload: SynthesizeBatchRequest, 
    background_tasks: BackgroundTasks,
    task_manager: TaskManager = Depends(get_task_manager)
):
    if not payload.segments:
        raise HTTPException(status_code=400, detail="Segments list cannot be empty.")
    
    task_id = await task_manager.create_task("tts_batch", payload.user_id)
    background_tasks.add_task(run_synthesize_batch_task, task_id, payload, task_manager)
    return {"status": "processing", "task_id": task_id}