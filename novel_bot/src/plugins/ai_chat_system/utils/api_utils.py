# novel_bot/src/plugins/ai_chat_system/utils/api_utils.py

import logging
from typing import Any, List, Optional, Tuple, AsyncGenerator, Dict

from ..llm_services import get_llm_service

logger = logging.getLogger("nonebot")

async def call_llm_service(
    user_id: str,
    service_config: Dict,
    model_pool: List[str],
    contents: List[Any],
    system_instruction: Optional[str] = None,
    generation_config: Optional[Any] = None,
    tools: Optional[List[Any]] = None,
    stream: bool = False,
    **kwargs: Any
) -> Tuple[Any, str] | AsyncGenerator[Dict[str, Any], None]:
    
    service_name = service_config.get("provider", "google_gemini")
    
    try:
        service_class = get_llm_service(service_name)
        service_instance = service_class()
        
        return await service_instance.call_api(
            user_id=user_id,
            service_config=service_config,
            model_pool=model_pool,
            contents=contents,
            system_instruction=system_instruction,
            generation_config=generation_config,
            tools=tools,
            stream=stream,
            **kwargs
        )
    except ValueError as e:
        logger.error(f"LLM_DISPATCHER: {e}")
        raise
    except Exception as e:
        logger.critical(f"LLM_DISPATCHER: Unhandled exception in service '{service_name}': {e}", exc_info=True)
        raise