# novel_bot/src/plugins/ai_chat_system/services/drawing/providers/stable_horde.py

import asyncio
import logging
import time
from typing import Any, Dict

import httpx
from fastapi import HTTPException

# [核心修正] 更新导入路径，从上一级的 config 模块导入
from ..config import AI_DRAWING_CONFIG

logger = logging.getLogger("nonebot")


async def call_stable_horde_api(payload: Dict[str, Any]) -> str:
    config = AI_DRAWING_CONFIG["stable_horde"]
    headers = {
        "apikey": config["api_key"],
        "Content-Type": "application/json",
        "Client-Agent": "MyNovelBot:1.0:AINovelBot",
    }
    horde_payload = {
        "prompt": f"{payload['prompt']} ### {payload.get('negative_prompt', '')}",
        "params": {
            "sampler_name": "k_dpmpp_2s_a",
            "cfg_scale": payload.get("cfg_scale", 7.0),
            "steps": payload.get("steps", 25),
            "width": payload.get("width", 512),
            "height": payload.get("height", 768),
            "seed": str(payload.get("seed", -1)),
        },
        "models": [payload.get("model", config["default_model"])],
        "nsfw": True,
        "censor_nsfw": False,
    }
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{config['api_url']}/v2/generate/async",
                json=horde_payload,
                headers=headers,
            )
            response.raise_for_status()
            request_id = response.json().get("id")
            if not request_id:
                raise HTTPException(
                    status_code=500, detail="Stable Horde did not return a job ID."
                )
            logger.info(f"AIGC (Horde): Submitted job with ID: {request_id}")
            check_url = f"{config['api_url']}/v2/generate/check/{request_id}"
            status_start_time = time.time()
            while time.time() - status_start_time < 280:
                await asyncio.sleep(5)
                status_response = await client.get(check_url)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get("done"):
                        logger.info(f"AIGC (Horde): Job {request_id} finished.")
                        result_response = await client.get(
                            f"{config['api_url']}/v2/generate/status/{request_id}"
                        )
                        generations = result_response.json().get("generations", [])
                        if generations:
                            return generations[0]["img"]
                        raise HTTPException(
                            status_code=404,
                            detail="Job finished but no image was generated.",
                        )
            raise HTTPException(
                status_code=408, detail="Image generation timed out on Stable Horde."
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"AIGC (Horde): Error: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Stable Horde error: {e.response.text}",
            )