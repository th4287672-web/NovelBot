from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Dict, Any

from .. import global_state
from .. import generators
from ..database.session import DBSession
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Session Management"])

@router.get("/sessions/{user_id}/{char_filename}")
async def get_sessions_for_character(user_id: str, char_filename: str, db: AsyncSession = DBSession):
    if not global_state.session_manager: raise HTTPException(status_code=503, detail="SessionManager not initialized.")
    sessions = await global_state.session_manager.get_sessions_for_character(user_id, char_filename, db)
    return sessions

@router.post("/session/{user_id}/{char_filename}")
async def create_new_session_for_character(user_id: str, char_filename: str, db: AsyncSession = DBSession):
    if not global_state.session_manager: raise HTTPException(status_code=503, detail="SessionManager not initialized.")
    new_session = await global_state.session_manager.create_new_session(user_id, char_filename, db)
    if new_session: return new_session
    raise HTTPException(status_code=500, detail="Failed to create new session.")

@router.get("/history/{user_id}/{session_id}")
async def get_session_history_by_id(user_id: str, session_id: str, db: AsyncSession = DBSession):
    if not global_state.session_manager: raise HTTPException(status_code=503, detail="SessionManager not initialized.")
    history = await global_state.session_manager.get_session_history(user_id, session_id, db)
    if history is not None: return history
    raise HTTPException(status_code=404, detail="Session history not found.")

@router.put("/history/{user_id}/{session_id}")
async def update_session_history_by_id(user_id: str, session_id: str, history: List[Dict[str, Any]] = Body(...), db: AsyncSession = DBSession):
    if not global_state.session_manager: raise HTTPException(status_code=503, detail="SessionManager not initialized.")
    if await global_state.session_manager.update_session_history(user_id, session_id, history, db):
        return {"status": "success", "message": "History updated."}
    raise HTTPException(status_code=500, detail="Failed to update session history.")

@router.delete("/session/{user_id}/{session_id}")
async def delete_session_by_id(user_id: str, session_id: str, db: AsyncSession = DBSession):
    if not global_state.session_manager: raise HTTPException(status_code=503, detail="SessionManager not initialized.")
    if await global_state.session_manager.delete_session(user_id, session_id, db):
        return {"status": "success", "message": "Session deleted."}
    raise HTTPException(status_code=404, detail="Session not found or failed to delete.")

@router.patch("/session/{user_id}/{session_id}")
async def rename_session_by_id(user_id: str, session_id: str, payload: Dict[str, str] = Body(...), db: AsyncSession = DBSession):
    if not global_state.session_manager: raise HTTPException(status_code=503, detail="SessionManager not initialized.")
    new_title = payload.get("title")
    if not new_title:
        raise HTTPException(status_code=400, detail="Missing 'title' in payload.")
    if await global_state.session_manager.rename_session(user_id, session_id, new_title, db):
        return {"status": "success", "message": "Session renamed."}
    raise HTTPException(status_code=404, detail="Session not found or failed to rename.")

@router.post("/session/{user_id}/{session_id}/generate_title")
async def generate_session_title(user_id: str, session_id: str, db: AsyncSession = DBSession):
    if not global_state.session_manager:
        raise HTTPException(status_code=503, detail="SessionManager not initialized.")
    
    history = await global_state.session_manager.get_session_history(user_id, session_id, db)
    if history is None or len(history) < 2:
        raise HTTPException(status_code=400, detail="Not enough history to generate a title.")
        
    try:
        title = await generators.generate_title_from_history(user_id, history)
        if await global_state.session_manager.rename_session(user_id, session_id, title, db):
            return {"status": "success", "title": title}
        else:
            raise HTTPException(status_code=500, detail="Failed to save generated title.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))