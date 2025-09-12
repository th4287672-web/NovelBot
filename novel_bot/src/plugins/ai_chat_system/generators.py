# novel_bot/src/plugins/ai_chat_system/generators.py

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
import uuid

import google.generativeai as genai
from google.generativeai.types import generation_types

from . import global_state
from .utils.api_utils import call_llm_service

logger = logging.getLogger("nonebot")

def get_best_generation_model_pool() -> List[str]:
    api_manager = global_state.api_manager
    if not api_manager or not api_manager.verified_models:
        raise ValueError("AI模型服务未准备就绪，无法确定模型池。")

    pro_models = [m for m in api_manager.verified_models if "pro" in m]
    flash_models = [m for m in api_manager.verified_models if "flash" in m]
    
    model_pool = pro_models + flash_models if pro_models else flash_models
    if not model_pool:
        raise ValueError("在已验证的模型列表中找不到任何'pro'或'flash'系列模型。")
    
    logger.debug(f"Determined best generation model pool: {model_pool}")
    return model_pool

def _convert_history_to_api_format(history: List[Dict]) -> List[Dict]:
    api_history = []
    for i, msg in enumerate(history):
        role = msg.get("role")
        content = msg.get("content") or "".join(part.get("text", "") for part in msg.get("parts", []))
        
        if role and content:
            api_history.append({
                "role": "model" if role == "assistant" else role,
                "parts": [{"text": content}]
            })
    return api_history

DEFAULT_SYSTEM_PROMPT_TEMPLATES = {
    "character_card": """
# 任务: 创作角色卡
你是一位顶级的角色概念艺术家和小说作家。根据用户提供的核心概念，创作一张结构完整、内容丰富、引人入胜的角色扮演卡片。

# 输出格式
你的最终输出必须是一个单一的、严格合规的JSON对象，不包含任何Markdown标记、前言或解释。
{
  "name": "string (角色名)",
  "displayName": "string (显示名称，与name相同)",
  "description": "string (生动详细的角色外观、背景和总体描述)",
  "personality": "string (精准概括核心性格特质)",
  "first_mes": "string (符合性格和背景的开场白)",
  "mes_example": "string (展示典型反应和语言风格的对话示例)"
}

# 强制规则
1.  **所有字段必须填充**：JSON对象中的每个字段都必须包含有意义的、非空的字符串内容。
2.  **内容质量**: `description` 必须超过50个字，`first_mes` 和 `mes_example` 必须是完整的句子。

# 用户提供的核心概念
"{prompt}"
""",
    "user_persona": """
# 任务: 创作用户人设卡
你是一位专业的角色概念设计师。根据用户提供的核心概念，创作一张结构化的用户人设卡（User Persona）。

# 输出格式
你的最终输出必须是一个单一的、严格合规的JSON对象，不包含任何Markdown标记、前言或解释。
{
  "name": "string (简洁的角色名)",
  "displayName": "string (显示名称，与name相同)",
  "description": "string (生动详细的角色描述，用于定义用户在扮演中的身份)"
}

# 强制规则
1.  **所有字段必须填充**: `name`, `displayName`, `description` 字段都必须包含有意义的、非空的字符串内容。
2.  **内容质量**: `description` 必须是一段有意义的、详细的描述，长度至少为30个字。

# 用户提供的核心概念
"{prompt}"
""",
    "world_info": """
# 任务: 创作世界书
你是一位富有想象力的世界观构建大师。根据用户提供的核心主题，创作一本结构化的世界书。

# 输出格式
你的最终输出必须是一个单一的、严格合规的JSON对象，不包含任何Markdown标记、前言或解释。
{
  "name": "string (简洁而有吸引力的世界书名称)",
  "entries": [
    {
      "uid": "string (UUIDv4)",
      "keywords": ["string", "string"],
      "content": "string (详细描述)"
    }
  ]
}

# 强制规则
1.  **条目数量**: `entries` 数组中应包含**至少5个**独立的条目。
2.  **条目完整性**: **每一个条目**的 `keywords` 数组都不能为空，`content` 字符串必须包含详细描述，并且必须包含一个唯一的 `uid`。

# 用户提供的主题
"{prompt}"
""",
    "story_package": """
# 任务: 故事编织者
你是一位经验丰富的小说家和游戏设计师。根据用户提供的核心创意，你需要构思并生成一个完整的、可立即开始的角色扮演故事包。

# 输出格式
你的最终输出必须是一个单一的、严格合规的JSON对象，不包含任何Markdown标记或解释。结构如下:
{
  "main_character": { "name": "...", "displayName": "...", "description": "...", "personality": "...", "first_mes": "...", "mes_example": "..." },
  "npcs": [
    { "name": "...", "displayName": "...", "description": "...", "personality": "...", "first_mes": "...", "mes_example": "..." },
    { "name": "...", "displayName": "...", "description": "...", "personality": "...", "first_mes": "...", "mes_example": "..." }
  ],
  "world_info": {
    "name": "...",
    "entries": [ { "uid": "...", "keywords": ["..."], "content": "..." } ]
  },
  "group": {
    "name": "开场故事",
    "description": "故事的整体简介",
    "first_mes": "故事的开场白或第一段旁白"
  }
}

# 强制规则
1.  **完整性**: 必须生成**所有**指定的键：`main_character` (1个), `npcs` (至少2个), `world_info` (至少3个条目), `group` (1个)。所有 `displayName` 字段都必须填充。
2.  **一致性**: 所有生成的内容必须围绕用户的核心创意，并保持逻辑和风格上的一致性。
3.  **质量**: 所有描述性字段都必须内容丰富、引人入胜。
4.  **唯一ID**: 世界书的每个条目都必须有一个 `uid` 字段。

# 用户的核心创意
"{prompt}"
"""
}

async def _generate_structured_json(
    task_name: str, 
    prompt: str, 
    user_id: str,
    selected_presets: Optional[List[str]] = None,
    selected_worlds: Optional[List[str]] = None
) -> str:
    dm = global_state.data_manager
    if not dm: raise RuntimeError("DataManager not initialized.")
    user_config = dm.get_user_config(user_id)
    llm_config = user_config.get("llm_service_config", {})

    system_instruction_template = DEFAULT_SYSTEM_PROMPT_TEMPLATES.get(task_name)
    if not system_instruction_template:
        raise ValueError(f"未找到任务 '{task_name}' 的提示词模板。")

    system_instruction = system_instruction_template.format(prompt=prompt)
    
    try:
        model_pool = get_best_generation_model_pool()
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json", temperature=0.75
        )
        
        response, _ = await call_llm_service(
            user_id=user_id,
            service_config={**llm_config, "api_keys": user_config.get('api_keys', [])},
            model_pool=model_pool,
            contents=[{'role': 'user', 'parts': [system_instruction]}],
            generation_config=generation_config,
            stream=False
        )
        
        if not response.candidates: raise ValueError("AI响应中不包含任何候选内容。")

        cleaned_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        
        parsed_json = json.loads(cleaned_text)
        if task_name == 'world_info' and 'entries' in parsed_json:
            for entry in parsed_json['entries']:
                if 'uid' not in entry: entry['uid'] = str(uuid.uuid4())
        elif task_name == 'story_package' and 'world_info' in parsed_json:
             for entry in parsed_json['world_info'].get('entries', []):
                if 'uid' not in entry: entry['uid'] = str(uuid.uuid4())

        return json.dumps(parsed_json, ensure_ascii=False)

    except Exception as e:
        logger.error(f"AI_GENERATOR ({task_name.capitalize()}): Generation failed for user '{user_id}': {e}", exc_info=True)
        raise RuntimeError(f"AI生成时发生内部错误: {e}") from e

async def generate_character_from_prompt(prompt: str, user_id: str, selected_presets: Optional[List[str]] = None, selected_worlds: Optional[List[str]] = None) -> str:
    return await _generate_structured_json("character_card", prompt, user_id, selected_presets, selected_worlds)

async def generate_user_persona_from_prompt(prompt: str, user_id: str, selected_presets: Optional[List[str]] = None, selected_worlds: Optional[List[str]] = None) -> str:
    return await _generate_structured_json("user_persona", prompt, user_id, selected_presets, selected_worlds)

async def generate_world_info_from_prompt(prompt: str, user_id: str, selected_presets: Optional[List[str]] = None, selected_worlds: Optional[List[str]] = None) -> str:
    return await _generate_structured_json("world_info", prompt, user_id, selected_presets, selected_worlds)

async def generate_story_package_from_prompt(prompt: str, user_id: str) -> Dict[str, Any]:
    json_string = await _generate_structured_json("story_package", prompt, user_id)
    return json.loads(json_string)

async def generate_title_from_history(user_id: str, history: List[Dict]) -> str:
    system_prompt = "你是一个对话总结专家。请仔细阅读以下对话历史，为其生成一个不超过10个字的、简洁且能概括核心内容的标题。只返回标题文本，不要包含任何其他说明或引号。"
    api_history = _convert_history_to_api_format(history)
    
    dm = global_state.data_manager
    if not dm: raise RuntimeError("DataManager not initialized.")
    user_config = dm.get_user_config(user_id)
    llm_config = user_config.get("llm_service_config", {})

    model_pool = get_best_generation_model_pool()
    response, _ = await call_llm_service(
        user_id=user_id,
        service_config={**llm_config, "api_keys": user_config.get('api_keys', [])},
        model_pool=model_pool,
        contents=api_history,
        system_instruction=system_prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=50),
        stream=False
    )
    return response.text.strip().replace("\"", "").replace("”", "").replace("“", "")

async def generate_memory_from_history(user_id: str, history: List[Dict]) -> List[str]:
    system_prompt = """你是一个信息提取和总结的AI助手。你的任务是分析下面的对话历史，并提取出关于角色、关系、关键事件、重要设定或用户偏好等长期性的、值得记住的核心信息。

# 规则
1.  **分点提取**: 将每个关键信息点作为一个独立的条目。
2.  **客观简洁**: 用客观、陈述性的语言来描述每个信息点，力求简洁明了。
3.  **JSON格式**: 你的输出必须是一个单一的、严格合规的JSON对象，格式为 `{"entries": ["记忆点1", "记忆点2", ... ]}`。
4.  **内容聚焦**: 只提取对未来对话有影响的关键信息，忽略日常寒暄和不重要的细节。

请开始分析以下对话历史："""
    api_history = _convert_history_to_api_format(history)

    dm = global_state.data_manager
    if not dm: raise RuntimeError("DataManager not initialized.")
    user_config = dm.get_user_config(user_id)
    llm_config = user_config.get("llm_service_config", {})

    model_pool = get_best_generation_model_pool()
    response, _ = await call_llm_service(
        user_id=user_id,
        service_config={**llm_config, "api_keys": user_config.get('api_keys', [])},
        model_pool=model_pool,
        contents=api_history,
        system_instruction=system_prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.5
        ),
        stream=False
    )
    try:
        data = json.loads(response.text)
        if isinstance(data, dict) and "entries" in data and isinstance(data["entries"], list):
            return data["entries"]
        else:
            raise ValueError("AI返回的JSON格式不正确，缺少'entries'数组。")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"解析记忆提取结果失败: {e}\n原始回复: {response.text}")
        raise