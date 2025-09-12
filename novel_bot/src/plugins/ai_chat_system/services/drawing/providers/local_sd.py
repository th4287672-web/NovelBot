# novel_bot/src/plugins/ai_chat_system/services/drawing/providers/local_sd.py

import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException

from ..config import AI_DRAWING_CONFIG

logger = logging.getLogger("nonebot")


async def call_sd_webui_api(payload: Dict[str, Any], mode: str) -> str:
    config = AI_DRAWING_CONFIG["local_sd_webui"]
    api_url = config['api_url']
    
    # [核心修改] 新增 override_settings 以便切换模型
    override_settings = {
        "sd_model_checkpoint": payload.get("model")
    }

    base_payload = {
        "prompt": payload["prompt"],
        "negative_prompt": payload.get("negative_prompt", ""),
        "steps": payload.get("steps", 20),
        "cfg_scale": payload.get("cfg_scale", 7),
        "sampler_index": "DPM++ 2M Karras",
        "seed": payload.get("seed", -1),
        "override_settings": override_settings, # 添加到基础payload
    }

    if mode == "txt2img":
        endpoint = f"{api_url}/txt2img"
        final_payload = {
            **base_payload,
            "width": payload.get("width", 512),
            "height": payload.get("height", 768),
        }
    elif mode == "img2img":
        endpoint = f"{api_url}/img2img"
        final_payload = {
            **base_payload,
            "init_images": [payload.get("image_base64", "").split(",", 1)[1]],
            "denoising_strength": payload.get("denoising_strength", 0.75),
            "width": payload.get("width", 512),
            "height": payload.get("height", 768),
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported mode for Local SD-WebUI: {mode}")

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(endpoint, json=final_payload)
            response.raise_for_status()
            data = response.json()
            if data.get("images") and data["images"][0]:
                return f"data:image/png;base64,{data['images'][0]}"
            raise HTTPException(
                status_code=500, detail="Local SD-WebUI API returned no images."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"AIGC (Local): HTTP error: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Local SD-WebUI error: {e.response.text}",
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Could not connect to Local SD-WebUI. Is it running with --api flag?",
            )