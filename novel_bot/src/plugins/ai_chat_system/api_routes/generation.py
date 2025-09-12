# novel_bot/src/plugins/ai_chat_system/api_routes/generation.py

import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse
from nonebot.adapters.onebot.v11 import Message, PrivateMessageEvent
from nonebot.adapters.onebot.v11.event import Sender

# [核心修复] 将相对导入路径从 `.` 改为 `..`
from .. import generators, global_state
from ..generation_pipeline import perform_message_action_generation
from ..prompt_builder import build_system_prompt

logger = logging.getLogger("nonebot")

router = APIRouter(prefix="/generation", tags=["AI Generation"])

@router.post("/character")
async def handle_generate_character(payload: Dict[str, Any] = Body(...)):
    prompt = payload.get("prompt")
    user_id = payload.get("user_id")
    selected_presets = payload.get("selected_presets")
    selected_worlds = payload.get("selected_worlds")

    if not prompt or not user_id:
        raise HTTPException(status_code=400, detail="Prompt and user_id are required.")
    try:
        generated_data = await generators.generate_character_from_prompt(
            prompt=prompt, 
            user_id=user_id, 
            selected_presets=selected_presets,
            selected_worlds=selected_worlds
        )
        return {"status": "success", "data": generated_data}
    except Exception as e:
        logger.error(f"Failed to generate character card: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/world_info")
async def handle_generate_world_info(payload: Dict[str, Any] = Body(...)):
    prompt = payload.get("prompt")
    user_id = payload.get("user_id")
    selected_presets = payload.get("selected_presets")
    selected_worlds = payload.get("selected_worlds")

    if not prompt or not user_id:
        raise HTTPException(status_code=400, detail="Prompt and user_id are required.")
    try:
        generated_data = await generators.generate_world_info_from_prompt(
            prompt=prompt, 
            user_id=user_id,
            selected_presets=selected_presets,
            selected_worlds=selected_worlds
        )
        return {"status": "success", "data": generated_data}
    except Exception as e:
        logger.error(f"Failed to generate world info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract_memory")
async def handle_extract_memory(payload: Dict[str, Any] = Body(...)):
    """从对话历史中提取关键记忆点。"""
    user_id = payload.get("user_id")
    history = payload.get("history")

    if not user_id or history is None:
        raise HTTPException(status_code=400, detail="user_id and history are required.")

    try:
        extracted_memories = await generators.generate_memory_from_history(user_id, history)
        return {"status": "success", "data": extracted_memories}
    except Exception as e:
        logger.error(f"Failed to extract memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/weave_story")
async def handle_weave_story(payload: Dict[str, Any] = Body(...)):
    """接收核心概念，并由AI生成一套完整的角色、世界观和开场。"""
    prompt = payload.get("prompt")
    user_id = payload.get("user_id")
    if not prompt or not user_id:
        raise HTTPException(status_code=400, detail="Prompt and user_id are required.")
    
    try:
        story_package = await generators.generate_story_package_from_prompt(prompt, user_id)
        return {"status": "success", "data": story_package}
    except Exception as e:
        logger.error(f"Failed to weave story package: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/message_action")
async def handle_message_action(payload: Dict[str, Any] = Body(...)):
    """处理消息的特定操作，如重写或继续。"""
    user_id = payload.get("user_id")
    action = payload.get("action")
    history = payload.get("history")
    target_message = payload.get("target_message")
    
    if not all([user_id, action, history, target_message]):
        raise HTTPException(status_code=400, detail="Missing required fields for message action.")

    async def stream_generator():
        try:
            async for chunk in perform_message_action_generation(user_id, action, history, target_message):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            error_payload = {"type": "error", "payload": {"code": "PIPELINE_ERROR", "message": f"处理消息操作时发生错误: {e}"}}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@router.post("/debug-prompt")
async def debug_prompt_generation(payload: Dict[str, Any] = Body(...)):
    """
    接收用户配置和模拟输入，返回最终生成的系统提示，用于调试。
    """
    user_config = payload.get("userConfig")
    user_message = payload.get("userMessage")

    if not user_config or user_message is None:
        raise HTTPException(status_code=400, detail="userConfig and userMessage are required.")

    if not global_state.data_manager:
        raise HTTPException(status_code=503, detail="DataManager is not initialized.")

    try:
        user_id_str = user_config.get("user_id", "12345")
        mock_sender = Sender(user_id=int(user_id_str), nickname="Debugger")
        mock_event = PrivateMessageEvent(
            time=0, self_id=0, post_type="message", message_type="private", sub_type="friend",
            user_id=int(user_id_str), message_id=0, message=Message(user_message),
            original_message=Message(user_message), raw_message=user_message, font=0, sender=mock_sender, to_me=True,
        )
        
        # [核心修复] 直接使用传入的 user_config，不再与全局状态交互，使其成为一个纯函数式、无副作用的调试端点。
        final_prompt = build_system_prompt(
            user_config=user_config,
            user_message=user_message,
            event=mock_event,
            request_story_options=False
        )
        
        return {"status": "success", "prompt": final_prompt}
    except Exception as e:
        logger.error(f"Failed to debug prompt generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during prompt generation: {str(e)}")