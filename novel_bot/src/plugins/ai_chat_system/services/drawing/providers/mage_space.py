# novel_bot/src/plugins/ai_chat_system/services/drawing/providers/mage_space.py

import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException

from ..config import AI_DRAWING_CONFIG

logger = logging.getLogger("nonebot")


async def call_mage_space_api(payload: Dict[str, Any], mode: str) -> str:
    if mode != 'txt2img':
        raise HTTPException(status_code=400, detail="Mage.space provider currently only supports txt2img mode.")
        
    config = AI_DRAWING_CONFIG["mage_space"]
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    mage_payload = {
        "model": payload.get("model", config["default_model"]),
        "prompt": payload["prompt"],
        "negative_prompt": payload.get("negative_prompt", ""),
        "steps": payload.get("steps", 30),
        "cfg_scale": payload.get("cfg_scale", 7.5),
        "width": payload.get("width", 512),
        "height": payload.get("height", 768),
        "seed": payload.get("seed", -1),
        "n": 1,
        "nologo": True,
        "nocluster": True,
    }
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{config['api_url']}/production", json=mage_payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
            if data and data[0].get("base64"):
                return f"data:image/jpeg;base64,{data[0]['base64']}"
            raise HTTPException(
                status_code=500, detail="Mage.space API returned no images."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"AIGC (Mage): Error: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Mage.space error: {e.response.text}",
            )