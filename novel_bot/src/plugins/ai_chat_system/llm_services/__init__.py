# novel_bot/src/plugins/ai_chat_system/llm_services/__init__.py

from typing import Dict, Type
from .base import LLMService
from .google_gemini import GoogleGeminiService
from .koboldai_horde import KoboldAIHordeService

# 服务注册表
# Key: 在配置文件中使用的服务名称 (例如 'google_gemini')
# Value: 实现了 LLMService 基类的服务类
SERVICE_REGISTRY: Dict[str, Type[LLMService]] = {
    "google_gemini": GoogleGeminiService,
    "koboldai_horde": KoboldAIHordeService,
}

def get_llm_service(service_name: str) -> Type[LLMService]:
    """
    根据服务名称从注册表中获取相应的服务类。
    
    Args:
        service_name (str): 服务的唯一标识符。

    Returns:
        Type[LLMService]: 对应的服务类。

    Raises:
        ValueError: 如果找不到指定的服务。
    """
    service_class = SERVICE_REGISTRY.get(service_name)
    if not service_class:
        raise ValueError(f"未知的 LLM 服务提供商: {service_name}")
    return service_class