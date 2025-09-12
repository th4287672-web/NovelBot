# novel_bot/src/plugins/ai_chat_system/llm_services/google_gemini.py

import logging
from typing import Any, List, Optional, Tuple, AsyncGenerator, Dict

import google.generativeai as genai
from google.generativeai.types import generation_types
from google.generativeai import retriever

from ..api_manager import ApiManager
from .. import global_state
from .base import LLMService

logger = logging.getLogger("nonebot")

class GoogleGeminiService(LLMService):
    """Google Gemini 服务的实现。"""

    async def call_api(
        self,
        user_id: str,
        service_config: Dict,
        model_pool: List[str],
        contents: List[Any],
        system_instruction: Optional[str] = None,
        generation_config: Optional[genai.types.GenerationConfig] = None,
        tools: Optional[List[genai.protos.Tool]] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> Tuple[Any, str] | AsyncGenerator[Dict[str, Any], None]:
        
        # [核心修复] 确保 api_keys 是列表
        api_keys_raw = service_config.get("api_keys", [])
        api_keys = api_keys_raw if isinstance(api_keys_raw, list) else []

        use_user_keys = bool(api_keys)
        
        if use_user_keys:
            # [核心修复] 检查 api_keys 是否为字典列表，如果是，则提取 'key' 字段
            if api_keys and isinstance(api_keys[0], dict):
                string_keys = [item.get('key', '') for item in api_keys if isinstance(item, dict) and item.get('key')]
            else:
                string_keys = api_keys

            if user_id not in global_state.user_api_managers or global_state.user_api_managers[user_id].keys != string_keys:
                global_state.user_api_managers[user_id] = ApiManager(string_keys)
            api_manager = global_state.user_api_managers[user_id]
        else:
            api_manager = global_state.api_manager

        if not api_manager or not api_manager.keys:
            raise RuntimeError("Google Gemini service failed: No API keys available.")
        
        if use_user_keys and not api_manager.verified_models:
             await api_manager.initialize_available_models()

        last_exception = None
        available_models = api_manager.verified_models or [m for m in model_pool if m in api_manager.model_fallback_order] or model_pool
        if not available_models:
            raise RuntimeError("No available Gemini models found after checking user keys.")

        final_tools = tools or []
        if kwargs.get('aqa_tool'):
            final_tools.append(kwargs['aqa_tool'])
            
        tool_config = None
        if kwargs.get('thinking_budget') is not None:
            thinking_config = genai.types.ThinkingConfig(thinking_budget=kwargs['thinking_budget'], mode=genai.types.ThinkingConfig.Mode.AUTO)
            tool_config = genai.types.ToolConfig(thinking_config=thinking_config)
        elif kwargs.get('aqa_tool'):
            tool_config = genai.types.ToolConfig(function_calling_config=genai.types.FunctionCallingConfig(mode=genai.types.FunctionCallingConfig.Mode.ONE_TURN))

        safety_settings = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
        
        indices_to_try = api_manager.get_prioritized_and_available_indices()
        if not indices_to_try:
            raise RuntimeError("All provided Google API keys are currently in cooldown.")

        for model_name in available_models:
            for key_index in indices_to_try:
                current_key = api_manager.keys[key_index]
                try:
                    genai.configure(api_key=current_key)
                    model = genai.GenerativeModel(
                        model_name,
                        system_instruction=system_instruction,
                        generation_config=generation_config,
                        tools=final_tools,
                        tool_config=tool_config,
                        safety_settings=safety_settings
                    )
                    
                    # [核心修复] 在调用API前，确保所有历史记录都是正确的 parts 格式
                    formatted_contents = [
                        {"role": msg["role"], "parts": msg["parts"]}
                        for msg in contents if "role" in msg and "parts" in msg
                    ]

                    if stream:
                        response_stream = await model.generate_content_async(contents=formatted_contents, stream=True)
                        return self._stream_wrapper(response_stream), model_name
                    else:
                        response = await model.generate_content_async(contents=formatted_contents, stream=False)
                        api_manager.report_key_success(key_index)
                        return response, model_name

                except Exception as e:
                    last_exception = e
                    logger.warning(f"❌ GEMINI_SERVICE: Call failed. Model: '{model_name}', Key Index: {key_index}, Error: {repr(e)}")
                    api_manager.report_key_failure(key_index)
            
        raise RuntimeError(f"All Gemini models and API Keys failed. Last error: {last_exception}")

    async def _stream_wrapper(self, stream: AsyncGenerator) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            async for chunk in stream:
                yield chunk
        except Exception as e:
            logger.error(f"GEMINI_SERVICE: Error during streaming: {e}", exc_info=True)
            raise