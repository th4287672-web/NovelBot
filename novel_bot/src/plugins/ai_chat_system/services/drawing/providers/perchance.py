# novel_bot/src/plugins/ai_chat_system/services/drawing/providers/perchance.py

import base64
import logging
from typing import Any, Dict
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

# [核心修正] 更新导入路径，从上一级的 config 模块导入
from ..config import AI_DRAWING_CONFIG

logger = logging.getLogger("nonebot")


async def call_perchance_api(payload: Dict[str, Any]) -> str:
    config = AI_DRAWING_CONFIG["perchance"]
    params = {
        "prompt": f"{payload.get('prompt', '')}, {payload.get('model', '')}",
        "negativePrompt": payload.get("negative_prompt", ""),
        "resolution": f"{payload.get('width', 512)}x{payload.get('height', 768)}",
        "guidanceScale": payload.get("cfg_scale", 7.0),
        "seed": payload.get("seed", -1),
    }
    full_url = f"{config['api_url']}?{urlencode(params)}"
    logger.info(f"AIGC (Perchance): Sending generation request...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(full_url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "success":
                raise HTTPException(
                    status_code=500,
                    detail=f"Perchance API returned an error: {data.get('status')}",
                )
            image_id = data.get("imageId")
            extension = data.get("fileExtension", "jpeg")
            if not image_id:
                raise HTTPException(
                    status_code=500, detail="Perchance API did not return an imageId."
                )
            logger.info(f"AIGC (Perchance): Got imageId: {image_id[:10]}...")
            image_url = f"{config['image_base_url']}/{image_id}.{extension}"
            logger.info(f"AIGC (Perchance): Downloading from {image_url}")
            image_response = await client.get(image_url)
            image_response.raise_for_status()
            image_bytes = image_response.content
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            return f"data:image/{extension};base64,{base64_image}"
        except httpx.HTTPStatusError as e:
            logger.error(f"AIGC (Perchance): Error: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Perchance API error: {e.response.text}",
            )
        except Exception as e:
            logger.error(
                f"AIGC (Perchance): An unexpected error occurred: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred with Perchance API: {str(e)}",
            )