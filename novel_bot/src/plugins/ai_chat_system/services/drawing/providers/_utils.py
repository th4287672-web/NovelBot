# novel_bot/src/plugins/ai_chat_system/services/drawing/providers/_utils.py
# 职责: 存放被多个provider共享的辅助函数。

import asyncio
import logging
import time
from typing import Dict

import httpx
from fastapi import HTTPException

logger = logging.getLogger("nonebot")


async def poll_for_result(
    client: httpx.AsyncClient, job_url: str, headers: Dict, timeout: int = 280
) -> Dict:
    """
    一个通用的轮询函数，用于检查异步任务的状态。
    被 Prodia 等服务使用。
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        await asyncio.sleep(3)
        try:
            response = await client.get(job_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "succeeded":
                return data
            if data.get("status") in ["failed", "canceled"]:
                error_detail = data.get("error", "Job failed without specific error.")
                raise HTTPException(
                    status_code=500,
                    detail=f"Image generation failed on provider: {error_detail}",
                )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"AIGC Polling: HTTP error checking job status: {e.response.text}"
            )
    raise HTTPException(status_code=408, detail="Image generation timed out.")