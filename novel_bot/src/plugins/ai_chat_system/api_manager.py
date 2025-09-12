# novel_bot/src/plugins/ai_chat_system/api_manager.py

import google.generativeai as genai
from typing import List, Dict, Any
import asyncio
import time
from nonebot import logger

from .constants import API_KEY_COOLDOWN_DURATION

class ApiManager:
    def __init__(self, api_keys: List[Dict[str, Any]] | List[str]):
        processed_keys = []
        if api_keys and isinstance(api_keys, list):
            for item in api_keys:
                if isinstance(item, dict) and 'key' in item and isinstance(item['key'], str):
                    processed_keys.append(item['key'].strip())
                elif isinstance(item, str):
                    processed_keys.append(item.strip())
        
        self.keys: List[str] = [key for key in processed_keys if key]

        if not self.keys:
            logger.trace("ApiManager: Instantiated with an empty list of API keys.")
            
        self.current_key_index = 0
        self.key_priority_order = list(range(len(self.keys)))
        self.last_successful_key_index = 0
        self.key_cooldowns: dict[int, float] = {}
        
        self.verified_models: list[Dict[str, Any]] = [] # [核心修改] 现在存储模型详情字典
        
        if self.keys:
            self.configure_key(self.current_key_index)

    def get_current_key(self) -> str:
        if not self.keys or not (0 <= self.current_key_index < len(self.keys)):
            raise RuntimeError("ApiManager has no valid keys configured.")
        return self.keys[self.current_key_index]

    def configure_key(self, key_index: int):
        if not self.keys or not (0 <= key_index < len(self.keys)):
            return
        self.current_key_index = key_index
        current_key = self.keys[self.current_key_index]
        genai.configure(api_key=current_key)
    
    def report_key_success(self, key_index: int):
        if not self.keys: return
        self.last_successful_key_index = key_index
        self.current_key_index = key_index
        if key_index in self.key_priority_order:
            self.key_priority_order.remove(key_index)
        self.key_priority_order.insert(0, key_index)
        if key_index in self.key_cooldowns:
            del self.key_cooldowns[key_index]

    def report_key_failure(self, key_index: int):
        if not self.keys: return
        if key_index in self.key_priority_order:
            self.key_priority_order.remove(key_index)
            self.key_priority_order.append(key_index)
        self.key_cooldowns[key_index] = time.time()

    def get_prioritized_and_available_indices(self) -> List[int]:
        if not self.keys: return []
        now = time.time()
        return [
            index for index in self.key_priority_order 
            if self.key_cooldowns.get(index) is None or (now - self.key_cooldowns.get(index, 0)) > API_KEY_COOLDOWN_DURATION
        ]

    async def initialize_available_models(self) -> List[Dict[str, Any]]:
        if not self.keys:
            logger.warning("ApiManager: Cannot initialize models without any API keys.")
            return []

        for i in range(len(self.keys)):
            key_idx_to_try = (self.current_key_index + i) % len(self.keys)
            self.configure_key(key_idx_to_try)
            try:
                models_iterator = await asyncio.wait_for(
                    asyncio.to_thread(genai.list_models), timeout=20.0
                )
                
                # [核心修改] 提取并格式化模型详细信息
                all_models_from_api = sorted([
                    {
                        "name": m.name,
                        "display_name": m.display_name,
                        "description": m.description,
                        "input_token_limit": m.input_token_limit,
                        "output_token_limit": m.output_token_limit,
                        "supported_generation_methods": m.supported_generation_methods,
                    }
                    for m in models_iterator if "generateContent" in m.supported_generation_methods
                ], key=lambda x: x['display_name'])
                
                if all_models_from_api:
                    self.verified_models = all_models_from_api
                    self.current_key_index = key_idx_to_try
                    logger.info(f"ApiManager: Successfully verified {len(self.verified_models)} models using Key index {key_idx_to_try}.")
                    return self.verified_models
            except Exception as e:
                logger.error(f"ApiManager: Exception querying models with Key index {key_idx_to_try}: {e}")
        
        logger.error("ApiManager: All provided API Keys failed to find any models.")
        self.verified_models = []
        return []