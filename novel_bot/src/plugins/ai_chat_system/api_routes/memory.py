# novel_bot/src/plugins/ai_chat_system/api_routes/memory.py

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any

# [核心修复] 将相对导入路径从 `.` 改为 `..`
from .. import global_state

router = APIRouter(prefix="/memory", tags=["Memory Management"])

@router.get("/{user_id}/{char_filename}")
async def get_character_memory(user_id: str, char_filename: str):
    """获取指定角色的记忆数据。"""
    if not global_state.data_manager:
        raise HTTPException(status_code=503, detail="DataManager not initialized.")
    
    memory_data = global_state.data_manager.get_character_memory(user_id, char_filename)
    return memory_data

@router.put("/{user_id}/{char_filename}")
async def update_character_memory(user_id: str, char_filename: str, memory_data: Dict[str, Any] = Body(...)):
    """更新或创建指定角色的记忆数据。"""
    if not global_state.data_manager:
        raise HTTPException(status_code=503, detail="DataManager not initialized.")
        
    if "entries" not in memory_data or not isinstance(memory_data["entries"], list):
        raise HTTPException(status_code=400, detail="Invalid memory data format. 'entries' array is required.")

    if global_state.data_manager.save_character_memory(user_id, char_filename, memory_data):
        return {"status": "success", "message": f"Memory for '{char_filename}' updated successfully."}
    
    raise HTTPException(status_code=500, detail=f"Failed to save memory for '{char_filename}'.")