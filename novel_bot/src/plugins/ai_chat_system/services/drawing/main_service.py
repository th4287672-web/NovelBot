# novel_bot/src/plugins/ai_chat_system/services/drawing/main_service.py

import logging
from typing import Any, Dict

from fastapi import HTTPException

from .config import AI_DRAWING_CONFIG
from .providers import SERVICE_MAP

logger = logging.getLogger("nonebot")


async def generate_image(payload: Dict[str, Any], mode: str = "txt2img") -> str:
    """
    根据全局配置，调度并执行AI图像生成任务。

    Args:
        payload (Dict[str, Any]): 来自API路由的请求载荷。
        mode (str): 生成模式, 'txt2img' 或 'img2img'。

    Returns:
        str: 生成的图像URL或Base64数据。
    
    Raises:
        HTTPException: 如果发生配置错误或生成失败。
    """
    prompt = payload.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")
        
    service_to_use = AI_DRAWING_CONFIG.get("service_to_use")
    logger.info(
        f"AIGC ({mode}): Received image generation request for service '{service_to_use}' with prompt: '{prompt[:50]}...'"
    )

    handler = SERVICE_MAP.get(service_to_use)
    if not handler:
        raise HTTPException(
            status_code=400, detail=f"Invalid drawing service configured: {service_to_use}"
        )

    try:
        # 将模式信息也传递给服务处理器
        image_url = await handler(payload, mode)
        logger.info(f"AIGC ({mode}): Image generated successfully via {service_to_use}.")
        return image_url
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(
            f"AIGC ({mode}): Image generation process failed for service '{service_to_use}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Image generation failed: {str(e)}"
        )