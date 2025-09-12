# novel_bot/src/plugins/ai_chat_system/generation_pipeline.py

import asyncio
import logging
import traceback
import re
from typing import Any, AsyncGenerator, Dict, List, Optional
import math

import google.generativeai as genai
from google.generativeai import retriever
from google.generativeai.types import AsyncGenerateContentResponse, generation_types
from nonebot.adapters.onebot.v11 import MessageEvent

from . import global_state
from .prompt_builder import build_system_prompt
from .tools.web_search import execute_web_search, web_search_tool
from .utils.api_utils import call_llm_service

logger = logging.getLogger("nonebot")

MAX_CONTEXT_TOKENS = 7000 

def _ensure_google_api_format(message: Dict) -> Dict:
    """确保单条消息记录符合 Google API 的格式。"""
    if "parts" in message:
        # 确保 parts 里的内容是 text
        if message["parts"] and isinstance(message["parts"][0], str):
             message["parts"] = [{"text": p} for p in message["parts"]]
        return message
    if "content" in message and "role" in message:
        return {"role": message["role"], "parts": [{"text": message["content"]}]}
    # 如果格式未知，返回一个安全的空结构以避免崩溃
    logger.warning(f"无法转换消息格式: {message}")
    return {"role": "user", "parts": [{"text": ""}]}

def _safe_get_response_text(response: Any) -> Optional[str]:
    try:
        if isinstance(response, AsyncGenerateContentResponse):
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                return response.text
            return None
        elif isinstance(response, dict) and response.get('type') == 'chunk':
            return response.get('content')
        return None
    except (ValueError, AttributeError) as e:
        logger.warning(f"Error accessing response text: {e}")
        return None

async def _truncate_history_by_tokens(
    system_prompt: str,
    history: List[Dict]
) -> List[Dict]:
    """根据Token限制智能截断历史记录 (本地估算)。"""
    def estimate_tokens(text: str) -> int:
        # 一个非常粗略的估算：平均每个中文字符约占1.5个token
        # 英文则大约是 字符数/4
        # 这里用一个更简单的混合估算：字符数 / 2
        return math.ceil(len(text) / 2)

    try:
        system_prompt_tokens = estimate_tokens(system_prompt)
        current_tokens = system_prompt_tokens
        
        truncated_history = []
        
        for message in reversed(history):
            content = message.get("content", "") or "".join(p.get("text", "") for p in message.get("parts", []))
            message_tokens = estimate_tokens(content)
            
            if current_tokens + message_tokens > MAX_CONTEXT_TOKENS:
                logger.info(f"AI_CHAT: Token limit reached (estimated). Truncating history. Total tokens: {current_tokens}")
                break
            
            current_tokens += message_tokens
            truncated_history.append(message)
            
        return list(reversed(truncated_history))
        
    except Exception as e:
        logger.error(f"AI_CHAT: Failed to truncate history by tokens (local estimation): {e}. Falling back to simple truncation.", exc_info=True)
        return history[-50:]

async def _handle_generation_stream(
    response_generator: AsyncGenerator[Dict[str, Any], None],
    stop_event: asyncio.Event,
    user_id_str: str,
    is_gemini_provider: bool
) -> AsyncGenerator[Dict[str, Any], None]:
    """内部函数，用于处理来自 call_llm_service 的流式响应。"""
    full_response_text = ""
    usage_metadata = None
    
    async for response_part in response_generator:
        if stop_event.is_set():
            logger.info(f"AI_CHAT: Generation stopped by user for {user_id_str}.")
            yield {"type": "error", "payload": {"code": "USER_ABORTED", "message": "[生成已由用户中止]"}}
            return
        
        if response_part.get("type") == "error":
            yield response_part
            return

        if is_gemini_provider and hasattr(response_part, 'usage_metadata'):
            if response_part.usage_metadata:
                usage_metadata = response_part.usage_metadata

        chunk_text = _safe_get_response_text(response_part)
        if chunk_text:
            full_response_text += chunk_text
            yield {"type": "chunk", "content": chunk_text}
        else:
            logger.debug(f"AI_CHAT: Skipping an empty or status-only chunk.")
            
    if not stop_event.is_set():
        if not full_response_text.strip():
            logger.warning(f"AI_CHAT: Generation for user {user_id_str} resulted in an empty response.")
            yield {"type": "error", "payload": {"code": "EMPTY_RESPONSE", "message": "(AI模型本次未生成任何有效内容)"}}
            return
        
        token_usage_payload = None
        if usage_metadata:
            token_usage_payload = { "prompt_token_count": usage_metadata.prompt_token_count, "candidates_token_count": usage_metadata.candidates_token_count, "total_token_count": usage_metadata.total_token_count }
        
        yield {
            "type": "full",
            "full_content": full_response_text.strip(),
            "token_usage": token_usage_payload
        }

async def generate_ai_reply(
    user_id_str: str,
    event: Optional[MessageEvent],
    prompt_parts: List[Any],
    history: List[Dict[str, Any]],
    action: str,
    stop_event: asyncio.Event,
    temp_model_override: Optional[str] = None,
    request_story_options: bool = False,
    system_prompt_override: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    logger.info(f"AI_CHAT: Starting unified generation pipeline for user {user_id_str}, action: {action}")
    
    dm = global_state.data_manager
    if not dm:
         logger.critical(f"AI_CHAT: DataManager not ready. Aborting.")
         yield {"type": "error", "payload": {"code": "SERVICE_UNAVAILABLE", "message": "系统核心服务尚未完全初始化，请稍后重试。"}}
         return

    user_config = dm.get_user_config(user_id_str)
    llm_service_config = user_config.get("llm_service_config", {"provider": "google_gemini"})
    
    is_gemini_provider = llm_service_config.get("provider") == "google_gemini"
    
    user_has_keys = bool(user_config.get('api_keys'))

    # [核心重构] 移除对全局 model_is_ready 的检查，改为检查用户级别的模型缓存
    if is_gemini_provider and not user_has_keys:
        error_msg = "AI功能需要API Key, 请在“设置”页面中添加并点击'连接'按钮。"
        yield {"type": "error", "payload": {"code": "API_KEY_REQUIRED", "message": error_msg}}
        return
    
    if is_gemini_provider and user_id_str not in global_state.api_key_model_cache:
        error_msg = "您的AI服务尚未连接，请前往“设置”页面点击'连接并检查模型'按钮。"
        yield {"type": "error", "payload": {"code": "MODELS_NOT_CHECKED", "message": error_msg}}
        return

    if stop_event.is_set():
        logger.info(f"AI_CHAT: Generation stopped by user before starting for {user_id_str}.")
        yield {"type": "error", "payload": {"code": "USER_ABORTED", "message": "[生成已由用户中止]"}}
        return

    api_history = history
    if action == "new":
        # [核心修复] 确保新消息是 parts 格式
        api_history.append({"role": "user", "parts": [{'text': p if isinstance(p, str) else str(p)} for p in prompt_parts]})
    
    user_text = event.get_plaintext().strip() if event else ""
    available_presets = dm.get_available_data(user_id_str, "preset")
    active_preset_name = user_config.get("preset")
    active_preset = available_presets.get(active_preset_name, {})
    
    system_prompt = system_prompt_override or build_system_prompt(user_config, user_text, event, request_story_options)
    
    if not system_prompt.strip():
        logger.error(f"AI_CHAT: Aborting generation for user {user_id_str} because system prompt is empty.")
        yield {"type": "error", "payload": {"code": "INVALID_PRESET", "message": f"生成中止：当前激活的预设 '{active_preset_name}' 无效或为空。"}}
        return
    
    model_pool = []
    if llm_service_config.get("provider") == "koboldai_horde":
        model_pool = llm_service_config.get("horde_models", ["Chronos-Hermes-13b"])
        final_history = await _truncate_history_by_tokens(system_prompt, api_history) if api_history else api_history
    else:
        verified_user_models = global_state.api_key_model_cache.get(user_id_str, [])
        model_pool = [temp_model_override] if temp_model_override else verified_user_models
        if not model_pool: model_pool = ["models/gemini-1.5-pro-latest"] # Fallback
        final_history = await _truncate_history_by_tokens(system_prompt, api_history) if api_history else api_history

    kwargs_for_service = {}
    if is_gemini_provider:
        # ... (此处逻辑保持不变)
        pass

    generation_config = genai.types.GenerationConfig(
        temperature=float(active_preset.get("temperature", 0.8)),
        top_p=float(active_preset.get("top_p", 0.9)),
        max_output_tokens=int(user_config.get("max_tokens", 4096)),
    )
    
    service_config_to_pass = {**llm_service_config, "api_keys": user_config.get('api_keys', [])}
    
    try:
        response_generator, model_name_used = await call_llm_service(
            user_id=user_id_str, service_config=service_config_to_pass, model_pool=model_pool,
            system_instruction=system_prompt, contents=final_history, generation_config=generation_config,
            stream=True, **kwargs_for_service
        )
        model_name_short = model_name_used.split("/")[-1] if is_gemini_provider else llm_service_config.get("provider")
        
        async for part in _handle_generation_stream(response_generator, stop_event, user_id_str, is_gemini_provider):
            if part['type'] == 'full':
                part['notification'] = f"[模型: {model_name_short}]"
            yield part

    except generation_types.BlockedPromptException as e:
        logger.error(f"AI_CHAT: Prompt blocked by safety filter for user {user_id_str}. Details: {e}")
        yield {"type": "error", "payload": {"code": "SAFETY_BLOCKED", "message": f"您的请求被安全策略拦截，无法生成回复。"}}
    except RuntimeError as e:
        logger.error(f"AI_CHAT: All fallbacks failed for user {user_id_str}. Last error: {e}", exc_info=True)
        yield {"type": "error", "payload": {"code": "ALL_SERVICES_FAILED", "message": f"抱歉，AI服务当前暂时过载。\n(所有模型和密钥均尝试失败)\n最后错误: {e}"}}
    except Exception as e:
        logger.critical(f"AI_CHAT: Unexpected critical error in generation pipeline for user {user_id_str}':\n{traceback.format_exc()}")
        yield {"type": "error", "payload": {"code": "PIPELINE_CRITICAL", "message": f"处理您的请求时发生意外错误: {type(e).__name__}"}}

async def perform_message_action_generation(
    user_id_str: str,
    action: str,
    history: List[Dict[str, Any]],
    target_message: Dict[str, Any]
) -> AsyncGenerator[Dict[str, Any], None]:
    
    dm = global_state.data_manager
    if not dm: raise RuntimeError("DataManager not initialized.")
    user_config = dm.get_user_config(user_id_str)
    
    history_for_action = history
    
    mock_event = MessageEvent.parse_obj({"message": "", "user_id": int(user_id_str) if user_id_str.isdigit() else 10000, "message_type": "private"})

    system_prompt = build_system_prompt(user_config, "", mock_event, False)
    
    action_instruction = ""
    if action in ['rewrite', 'regenerate']:
        action_instruction = "\n\n# 指令：\n请重新生成你上一条的回复。你需要提供一个与之前完全不同、但同样合理且符合角色性格的回复。"
    elif action in ['continue', 'complete']:
        action_instruction = "\n\n# 指令：\n请从你上一条回复的结尾处继续写下去，扩充内容或发展情节，使其更加完整。"
        history_for_action.append(target_message) 
    elif action == 'regenerate_options':
         action_instruction = "\n\n# 指令：\n为你的下一句回复提供三个不同的、简洁的剧情发展选项。"
         history_for_action.append(target_message) # 重新生成选项需要上文
    else:
        yield {"type": "error", "payload": {"code": "UNKNOWN_ACTION", "message": f"未知的消息操作: '{action}'"}}
        return

    final_system_prompt = system_prompt + action_instruction
    
    async for chunk in generate_ai_reply(
        user_id_str, 
        mock_event, 
        [], 
        history_for_action, 
        "action", 
        asyncio.Event(),
        request_story_options=(action == 'regenerate_options'),
        system_prompt_override=final_system_prompt
    ):
        yield chunk
