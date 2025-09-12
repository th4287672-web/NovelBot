import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

import pytz
from nonebot.adapters.onebot.v11 import MessageEvent

from . import global_state

logger = logging.getLogger("nonebot")

# [核心新增] 模板渲染引擎
def _render_template(template_string: str, context: Dict[str, Any]) -> str:
    """
    使用给定的上下文数据渲染一个包含 {{placeholder}} 的字符串模板。
    """
    def replacer(match: re.Match) -> str:
        # 获取占位符的键名，例如 'char' 或 'personality'
        key = match.group(1).strip()
        # 从上下文字典中获取对应的值，如果不存在则返回原始占位符
        return str(context.get(key, match.group(0)))

    # 查找所有 {{...}} 格式的占位符并替换
    return re.sub(r"\{\{\s*(.*?)\s*\}\}", replacer, template_string)

def build_system_prompt(
    user_config: Dict, 
    user_message: str, 
    event: MessageEvent,
    request_story_options: bool = False
) -> str:
    """
    构建一个单一的、完整的、用于指导AI模型的系统提示(System Prompt)。
    该函数现在完全由用户激活的预设驱动，并包含一个模板渲染步骤。
    """
    if not global_state.data_manager:
        logger.critical("FATAL: DataManager in global_state is not initialized! Cannot build system prompt.")
        return "Error: DataManager not ready."

    user_id = str(event.user_id)
    
    # --- 1. 数据加载与上下文准备 ---
    dm = global_state.data_manager
    available_chars = dm.get_available_data(user_id, "character")
    
    active_char_name = user_config.get("active_character")
    active_char_card = available_chars.get(active_char_name, {})
    
    user_persona_name = user_config.get("user_persona")
    user_persona_card = available_chars.get(user_persona_name, {}) if user_persona_name and user_persona_name != "User" else {}

    # 加载所有相关的世界书
    world_names_to_load = set(active_char_card.get("linked_worlds", []) + user_config.get("world_info", []))
    available_worlds = dm.get_available_data(user_id, "world_info")
    loaded_worlds_content = "\n".join(
        "\n".join(f"- {entry.get('content', '')}" for entry in available_worlds[name].get("entries", []))
        for name in world_names_to_load if name in available_worlds
    )

    # --- 2. 预设和模块加载 ---
    preset_name = user_config.get("preset")
    available_presets = dm.get_available_data(user_id, "preset")
    preset = available_presets.get(preset_name, {})
    
    if not preset:
        logger.error(f"User '{user_id}' has an invalid preset '{preset_name}' configured. Returning empty prompt.")
        return ""
    
    active_module_ids = user_config.get("active_modules", {}).get(preset_name, [])

    if request_story_options:
        story_option_module_id = "ec7db4d7-c8ac-4b17-9d1b-3892225cdfdf"
        if story_option_module_id not in active_module_ids:
            active_module_ids.append(story_option_module_id)
            logger.info(f"AI_CHAT: Force-activating story option module for user {user_id}.")

    id_to_prompt = {p["identifier"]: p for p in preset.get("prompts", [])}
    
    prompt_order_info = next((o for o in preset.get("prompt_order", []) if o.get("character_id") == 100001), None)
    ordered_prompts_data = []
    if prompt_order_info and prompt_order_info.get("order"):
        order_list = prompt_order_info["order"]
        ordered_prompts_data = [
            id_to_prompt[o["identifier"]] for o in order_list if o.get("identifier") in active_module_ids and o["identifier"] in id_to_prompt
        ]
    else:
        logger.warning(f"No prompt order found for preset '{preset_name}'. Loading modules in default order.")
        ordered_prompts_data = [p for p in preset.get("prompts", []) if p.get("identifier") in active_module_ids]

    # --- 3. [核心优化] 创建用于模板渲染的上下文 ---
    rendering_context = {
        "char": active_char_card.get("name", "AI"),
        "user": user_persona_card.get("name") or (event.sender.nickname if hasattr(event, "sender") and event.sender.nickname else "User"),
        "personality": active_char_card.get("personality", ""),
        "description": active_char_card.get("description", ""),
        "scenario": active_char_card.get("first_mes", ""), # 默认场景为开场白
        "world_info": loaded_worlds_content,
        "personaDescription": user_persona_card.get("description", ""),
        "dialogueExamples": active_char_card.get("mes_example", ""),
        # 可以添加更多...
        "Nickname": "小助手",
        "CoreTrait": " helpful AI",
        "RoleBase": "Roleplayer",
    }

    # --- 4. 构建最终提示词字符串 ---
    final_prompt_parts = []
    for module in ordered_prompts_data:
        content = module.get("content", "")
        # [核心优化] 对标记模块进行特殊处理，用上下文数据替换它们
        if module.get("marker"):
            marker_id = module.get("identifier")
            if marker_id == "charDescription":
                final_prompt_parts.append(rendering_context["description"])
            elif marker_id == "charPersonality":
                final_prompt_parts.append(rendering_context["personality"])
            elif marker_id == "scenario":
                final_prompt_parts.append(rendering_context["scenario"])
            elif marker_id == "worldInfoBefore":
                final_prompt_parts.append(rendering_context["world_info"])
            elif marker_id == "personaDescription":
                final_prompt_parts.append(rendering_context["personaDescription"])
            elif marker_id == "dialogueExamples":
                final_prompt_parts.append(rendering_context["dialogueExamples"])
            # 'chatHistory' is handled by the generation pipeline, so we skip it here.
        else:
            final_prompt_parts.append(content)

    # --- 5. 添加动态时间信息 ---
    try:
        china_tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.now(china_tz).strftime('%Y-%m-%d %H:%M:%S %Z')
        final_prompt_parts.append(f"[系统指令：当前现实世界时间是 {current_time}。请在你的回复中适当考虑这一点。]")
    except Exception as e:
        logger.warning(f"Failed to get current time for system prompt: {e}")
                
    unrendered_prompt = "\n".join(filter(None, final_prompt_parts))
    
    # --- 6. [核心优化] 执行模板渲染 ---
    final_prompt = _render_template(unrendered_prompt, rendering_context)
    
    logger.debug(f"AI_CHAT: Built a unified system prompt for user {user_id}, length {len(final_prompt)}")
    return final_prompt