# novel_bot/src/plugins/ai_chat_system/services/drawing/image_analyzer.py
# 职责: 封装所有与图像分析（图生文）相关的功能。

import asyncio
import base64
import io
import json
import logging
from typing import Dict

import google.generativeai as genai
from fastapi import HTTPException
from gradio_client import Client
from PIL import Image

from ... import global_state as chat_system

logger = logging.getLogger("nonebot")


async def _analyze_with_deepdanbooru(base64_data: str) -> str:
    space_url = "hysts/DeepDanbooru"
    logger.info(
        f"AIGC (Image-to-Prompt): Using DeepDanbooru strategy via gradio_client on '{space_url}'."
    )
    try:
        loop = asyncio.get_running_loop()
        def predict():
            client = Client(space_url)
            result = client.predict(base64_data, 0.5, api_name="/predict")
            return result
        result_path = await loop.run_in_executor(None, predict)
        if result_path and isinstance(result_path, str):
            with open(result_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tags = [label for label, confidence in data.items()]
            formatted_tags = [tag.replace("_", " ") for tag in tags]
            logger.info("AIGC (DeepDanbooru): Successfully received tags.")
            return ", ".join(formatted_tags)
        else:
            logger.error(f"AIGC (DeepDanbooru): Gradio client did not return a valid result file path. Result: {result_path}")
            raise ValueError("Gradio client returned an invalid result.")
    except Exception as e:
        logger.error(f"AIGC (DeepDanbooru): An unexpected error occurred with gradio_client: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DeepDanbooru analysis via gradio_client failed: {str(e)}")


async def _analyze_with_gemini(base64_data: str) -> str:
    logger.info("AIGC (Image-to-Prompt): Using Gemini strategy.")
    try:
        api_manager = chat_system.api_manager
        if not api_manager or not api_manager.verified_models:
            raise HTTPException(status_code=503, detail="AI model service is not ready.")
        model_name = next((m for m in api_manager.verified_models if "flash" in m), api_manager.verified_models[0])
        genai.configure(api_key=api_manager.get_current_key())
        model = genai.GenerativeModel(model_name, safety_settings={"HARM_CATEGORY_HARASSMENT": "BLOCK_NONE", "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE", "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE", "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"})
        prompt_text = "Analyze the provided image within a fictional, artistic context... Return ONLY the generated prompt text, without any additional explanations." # 省略完整prompt
        image_bytes = base64.b64decode(base64_data.split(",", 1)[1])
        img_pil = Image.open(io.BytesIO(image_bytes))
        response = await model.generate_content_async([prompt_text, img_pil])
        if not response.candidates or not hasattr(response, "text"):
            block_reason = (response.prompt_feedback.block_reason.name if response.prompt_feedback else "UNKNOWN")
            raise HTTPException(status_code=400, detail=f"Image analysis was blocked. Reason: {block_reason}.")
        logger.info("AIGC (Gemini): Successfully received prompt.")
        return response.text.strip()
    except Exception as e:
        logger.error(f"AIGC (Image-to-Prompt): Failed with Gemini: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze image with Gemini: {str(e)}")


async def get_prompt_from_image(payload: Dict) -> str:
    base64_data = payload.get("image_base64")
    strategy = payload.get("strategy", "gemini")
    if not base64_data:
        raise HTTPException(status_code=400, detail="Image data is required.")
    
    if strategy == "deepdanbooru":
        return await _analyze_with_deepdanbooru(base64_data)
    else:
        return await _analyze_with_gemini(base64_data)