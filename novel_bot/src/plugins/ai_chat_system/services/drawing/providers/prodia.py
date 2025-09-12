# novel_bot/src/plugins/ai_chat_system/services/drawing/providers/prodia.py

import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException

# [核心修正] 更新导入路径，从上一级的 config 模块导入
from ..config import AI_DRAWING_CONFIG
from ._utils import poll_for_result

logger = logging.getLogger("nonebot")


async def call_prodia_api(payload: Dict[str, Any]) -> str:
    config = AI_DRAWING_CONFIG["prodia"]
    headers = {"X-Prodia-Key": config["api_key"], "Content-Type": "application/json"}
    prodia_payload = {
        "model": payload.get("model", config["default_model"]),
        "prompt": payload["prompt"],
        "negative_prompt": payload.get("negative_prompt", ""),
        "steps": payload.get("steps", 25),
        "cfg_scale": payload.get("cfg_scale", 7.0),
        "sampler": "DPM++ 2M Karras",
        "width": payload.get("width", 512),
        "height": payload.get("height", 768),
        "seed": payload.get("seed", -1),
    }
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{config['api_url']}/sd/generate", json=prodia_payload, headers=headers
            )
            response.raise_for_status()
            job_data = response.json()
            job_id = job_data.get("job")
            if not job_id:
                raise HTTPException(
                    status_code=500, detail="Prodia did not return a job ID."
                )
            logger.info(f"AIGC (Prodia): Submitted job with ID: {job_id}")
            job_url = f"{config['api_url']}/job/{job_id}"
            result = await poll_for_result(client, job_url, headers)
            return result.get("imageUrl")
        except httpx.HTTPStatusError as e:
            logger.error(f"AIGC (Prodia): Error: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Prodia error: {e.response.text}",
            )