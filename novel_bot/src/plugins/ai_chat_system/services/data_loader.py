# novel_bot/src/plugins/ai_chat_system/services/data_loader.py

import base64
import json5
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from PIL import Image

from .data_persistence import BASE_DATA_PATH

logger = logging.getLogger("nonebot")

# --- 适配器与转换器 ---

def _convert_sillytavern_world_info(file_path: Path, raw_data: Dict) -> Optional[Dict]:
    """尝试将SillyTavern格式的世界书数据转换为MyNovelBot原生格式。"""
    try:
        converted_entries = []
        st_entries = raw_data.get("entries", {})
        if not isinstance(st_entries, dict): return None
        for entry_data in st_entries.values():
            keywords = entry_data.get("key", [])
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(',') if k.strip()]
            
            content = entry_data.get("content", "")
            if content: 
                converted_entries.append({
                    "name": entry_data.get("comment", file_path.stem),
                    "keywords": keywords, 
                    "content": content
                })
        
        name = raw_data.get("name") or file_path.stem
        return {"name": name, "entries": converted_entries}
    except Exception as e:
        logger.warning(f"DataLoader: Failed to convert SillyTavern World Info from {file_path.name}: {e}")
        return None

def _convert_character_card_v2(raw_data: Dict) -> Optional[Dict]:
    """将V2角色卡数据字段映射到我们的内部模型。"""
    try:
        return {
            "name": raw_data.get("name") or raw_data.get("char_name"),
            "description": raw_data.get("description") or raw_data.get("char_persona"),
            "personality": raw_data.get("personality"),
            "first_mes": raw_data.get("first_mes") or raw_data.get("greeting"),
            "mes_example": raw_data.get("mes_example") or raw_data.get("example_dialogue"),
        }
    except Exception as e:
        logger.warning(f"DataLoader: Failed to convert V2 Character Card: {e}")
        return None

# --- 核心加载逻辑 ---

def load_from_dir(path: Path, data_type: str) -> Dict[str, Dict]:
    """
    [核心优化] 从指定目录加载、解析并适配所有相关数据文件。
    这是一个具备多格式兼容性和错误容忍度的健壮加载器。
    """
    data = {}
    if not path.exists():
        return data

    patterns = ["*.json", "*.png"] if data_type == "character" else ["*.json"]
    
    files_to_scan = []
    for pattern in patterns:
        files_to_scan.extend(path.glob(pattern))
    
    for file in files_to_scan:
        # [核心优化] 隔离每个文件的加载错误
        try:
            raw_data = None
            
            if file.suffix == '.json':
                with open(file, "r", encoding="utf-8") as f:
                    raw_data = json5.load(f)
            elif file.suffix == '.png' and data_type == "character":
                with Image.open(file) as img:
                    metadata = img.info or {}
                    if "chara" in metadata:
                        chara_b64 = metadata["chara"]
                        chara_json = base64.b64decode(chara_b64).decode('utf-8')
                        raw_data = json5.loads(chara_json)
                    else:
                        continue
            
            if raw_data is None: continue

            processed_data = None
            
            if data_type == "character":
                spec = raw_data.get("spec")
                if spec == "chara_card_v2" or "char_name" in raw_data or "char_persona" in raw_data:
                    logger.debug(f"DataLoader: Detected Character Card V2 format for {file.name}. Converting...")
                    processed_data = _convert_character_card_v2(raw_data)
            
            elif data_type == "world_info":
                if isinstance(raw_data.get("entries"), dict):
                    logger.debug(f"DataLoader: Detected SillyTavern World Info format for {file.name}. Converting...")
                    processed_data = _convert_sillytavern_world_info(file, raw_data)

            if processed_data is None:
                processed_data = raw_data
            
            # 确保数据有效再加入字典
            if processed_data and ('name' in processed_data or data_type != 'preset'):
                 data[file.stem] = processed_data
            elif processed_data and data_type == 'preset':
                 data[file.stem] = processed_data
            else:
                logger.warning(f"DataLoader: Skipped {file.name} because it lacks a 'name' field after processing.")

        except Exception as e:
            logger.warning(f"DataLoader: Could not load or process {file.name}. Reason: {e}. Skipping file.")
    
    return data

def load_all_public_data() -> Tuple[Dict, Dict, Dict, Dict]:
    """加载所有公共数据"""
    public_path = BASE_DATA_PATH / "public"
    public_characters = load_from_dir(public_path / "characters", "character")
    public_presets = load_from_dir(public_path / "presets", "preset")
    public_world_info = load_from_dir(public_path / "world_info", "world_info")
    public_groups = load_from_dir(public_path / "groups", "group") # [核心新增]
    return public_characters, public_presets, public_world_info, public_groups
