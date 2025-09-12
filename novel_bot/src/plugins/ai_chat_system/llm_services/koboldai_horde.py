# novel_bot/src/plugins/ai_chat_system/llm_services/koboldai_horde.py

import httpx
import json
import logging
from typing import Any, List, Optional, AsyncGenerator, Dict, Tuple

from .base import LLMService

logger = logging.getLogger("nonebot")

HORDE_API_URL = "https://koboldai.net/api"
DEFAULT_API_KEY = "0000000000"

def _convert_history_to_kobold_format(history: List[Dict], system_prompt: str) -> str:
    full_prompt = f"{system_prompt.strip()}\n\n"
    for message in history:
        role = message.get("role")
        content = "".join(part.get('text', '') for part in message.get("parts", []))
        if role == "user":
            full_prompt += f"You: {content}\n"
        elif role == "model" or role == "assistant":
            full_prompt += f"AI: {content}\n"
    full_prompt += "AI:"
    return full_prompt

class KoboldAIHordeService(LLMService):
    """KoboldAI Horde 服务的实现。"""

    async def call_api(
        self,
        user_id: str,
        service_config: Dict,
        model_pool: List[str],
        contents: List[Any],
        system_instruction: Optional[str] = None,
        generation_config: Optional[Any] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> Tuple[Any, str] | AsyncGenerator[Dict[str, Any], None]:
        
        if not stream:
            raise NotImplementedError("KoboldAI Horde service currently only supports streaming.")

        api_key = service_config.get("api_key") or DEFAULT_API_KEY
        headers = {"apikey": api_key, "Content-Type": "application/json"}
        
        prompt = _convert_history_to_kobold_format(contents, system_instruction or "")

        params = {
            "temperature": getattr(generation_config, 'temperature', 0.8),
            "top_p": getattr(generation_config, 'top_p', 0.9),
            "max_context_length": 4096,
            "max_length": 1024,
        }

        payload = { "prompt": prompt, "models": model_pool, "params": params, "stream": True }

        return self._stream_wrapper(payload, headers, service_config), (model_pool[0] if model_pool else "Unknown Horde Model")

    async def _stream_wrapper(self, payload: Dict, headers: Dict, service_config: Dict) -> AsyncGenerator[Dict[str, Any], None]:
        transport = self.get_proxy_transport(service_config)
        async with httpx.AsyncClient(timeout=300.0, transport=transport) as client:
            try:
                async with client.stream("POST", f"{HORDE_API_URL}/v2/generate/text/async", json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if "generation" in data:
                                    yield {"type": "chunk", "content": data["generation"]}
                                elif "finished" in data:
                                    break
                            except json.JSONDecodeError:
                                continue
            except httpx.HTTPStatusError as e:
                error_text = await e.response.aread()
                logger.error(f"KOBOLD_SERVICE: HTTP error: {e.response.status_code} - {error_text.decode()}")
                yield {"type": "error", "content": f"KoboldAI Horde Error: {error_text.decode()}"}
            except Exception as e:
                logger.error(f"KOBOLD_SERVICE: An unexpected error occurred: {e}", exc_info=True)
                yield {"type": "error", "content": f"An unexpected error occurred with KoboldAI Horde: {str(e)}"}