# novel_bot/src/plugins/ai_chat_system/services/drawing/providers/__init__.py
# 职责: 聚合所有独立的provider实现，并提供统一的服务地图。

from .local_sd import call_sd_webui_api
from .mage_space import call_mage_space_api
from .perchance import call_perchance_api
from .prodia import call_prodia_api
from .stable_horde import call_stable_horde_api

# 建立服务名称到其调用函数的映射，供上层调度器使用
SERVICE_MAP = {
    "perchance": call_perchance_api,
    "stable_horde": call_stable_horde_api,
    "prodia": call_prodia_api,
    "mage_space": call_mage_space_api,
    "local_sd_webui": call_sd_webui_api,
}