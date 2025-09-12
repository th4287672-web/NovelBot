import asyncio
from typing import Optional, Dict, TYPE_CHECKING, List

if TYPE_CHECKING:
    from .api_manager import ApiManager
    from .data_manager import DataManager
    from .session_manager import SessionManager

initialization_complete = asyncio.Event()

# [核心重构] 全局ApiManager被移除
api_manager: Optional["ApiManager"] = None
data_manager: Optional["DataManager"] = None
session_manager: Optional["SessionManager"] = None
# [核心重构] model_is_ready 状态现在是用户级别的，全局状态移除
# model_is_ready: bool = False
temp_model_sessions: Dict[str, str] = {}

# [核心重构] 缓存每个用户验证过的模型列表
api_key_model_cache: Dict[str, List[str]] = {}

# [优化] 新增一个字典来缓存每个用户的 ApiManager 实例
user_api_managers: Dict[str, "ApiManager"] = {}
