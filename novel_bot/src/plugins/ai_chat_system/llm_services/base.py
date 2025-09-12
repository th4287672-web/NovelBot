# novel_bot/src/plugins/ai_chat_system/llm_services/base.py

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple, AsyncGenerator, Dict

class LLMService(ABC):
    """
    语言模型服务提供商的抽象基类。
    所有具体的 LLM 服务实现都必须继承此类并实现其抽象方法。
    """
    
    @abstractmethod
    async def call_api(
        self,
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
        """
        调用 LLM API 的核心方法。

        Args:
            user_id (str): 发起请求的用户ID。
            service_config (Dict): 包含API Key、代理等特定于服务的配置。
            model_pool (List[str]): 可供选择的模型列表。
            contents (List[Any]): 对话历史。
            system_instruction (Optional[str]): 系统提示。
            generation_config (Optional[Any]): 生成参数配置。
            tools (Optional[List[Any]]): 可供模型使用的工具列表。
            stream (bool): 是否以流式模式返回响应。
            **kwargs: 其他特定于服务的参数。

        Returns:
            如果 stream=False，返回一个包含完整响应和所用模型名称的元组。
            如果 stream=True，返回一个异步生成器，逐块产生响应字典。
        """
        pass
    
    def get_proxy_transport(self, service_config: Dict) -> Optional[Any]:
        """
        一个辅助方法，用于从服务配置中获取并创建一个 httpx transport。
        """
        import httpx
        proxy_url = service_config.get("proxy")
        if proxy_url:
            return httpx.AsyncHTTPTransport(proxy=proxy_url)
        return None