# novel_bot/src/plugins/ai_chat_system/services/drawing/config.py
# 职责: AI绘画服务的唯一静态配置源。

from typing import Any, Dict

AI_DRAWING_CONFIG: Dict[str, Any] = {
    # [核心修改] 将默认服务改为 local_sd_webui，您可以根据喜好调整
    "service_to_use": "local_sd_webui",
    
    "local_sd_webui": {
        "api_url": "http://127.0.0.1:7860/sdapi/v1",
        "name": "Local SD-WebUI",
        "description": "您本地运行的 AUTOMATIC1111/Forge 实例。如果您有合适的硬件，这是最快、最自由的选择。",
        "api_key_url": None,
        "docs_url": "https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API",
        # [核心新增] 在这里手动填写您本地 WebUI 可用的模型名称 (Checkpoint a.k.a. Stable Diffusion Model)
        # 您可以通过访问 http://127.0.0.1:7860/sdapi/v1/sd-models 来获取模型列表
        "available_models": [
            "anything-v5-PrtRE.safetensors [7f96a1a9ca]",
            "counterfeit-v3.0.safetensors [9e2a8f1f54]",
            "dreamshaper-8.safetensors [879db523c3]",
        ]
    },
    "perchance": {
        "api_url": "https://image-generation.perchance.org/api/generate",
        "image_base_url": "https://image-generation.perchance.org/images",
        "name": "Perchance Generator",
        "description": "一个免费的、基于Web的AI图片生成器。速度快，无需API Key。",
        "api_key_url": None,
        "docs_url": "https://perchance.org/image-generator-professional",
        "available_models": [], # 不支持模型选择
    },
    "stable_horde": {
        "api_url": "https://stablehorde.net/api",
        "api_key": "0000000000",
        "name": "Stable Horde",
        "description": "一个由志愿者组成的分布式Stable Diffusion计算集群。免费、匿名，但速度和稳定性可能会有波动。",
        "api_key_url": "https://stablehorde.net/register",
        "docs_url": "https://stablehorde.net/models",
        # 示例模型列表，更多模型请查阅其文档
        "available_models": [
            "Anything Diffusion",
            "Stable Diffusion",
            "Deliberate",
        ]
    },
    "prodia": {
        "api_url": "https://api.prodia.com/v1",
        "api_key": "YOUR_PRODIA_API_KEY",
        "name": "Prodia",
        "description": "提供快速的API服务并包含免费额度。需要注册获取API Key。",
        "api_key_url": "https://app.prodia.com/api",
        "docs_url": "https://docs.prodia.com/docs/models",
        "available_models": [
            "anything-v4.5-pruned.ckpt [65745d25]",
            "dreamshaper_8.safetensors [879db523c3]",
            "v1-5-pruned-emaonly.ckpt [81761151]",
        ]
    },
}