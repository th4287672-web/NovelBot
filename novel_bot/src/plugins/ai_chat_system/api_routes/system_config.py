import traceback
from fastapi import APIRouter, Body, HTTPException, Depends
from typing import Dict, List
from nonebot import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .. import global_state
from ..services.connection_manager import broadcast_status_update
from ..database.session import DBSession
from ..database.models import User

router = APIRouter(tags=["System & Config"])

@router.get("/bootstrap/{user_id}")
async def bootstrap_user_data(user_id: str, db: AsyncSession = DBSession):
    logger.info(f"[DIAG] /bootstrap endpoint hit for user_id: {user_id}")
    try:
        if not global_state.data_manager or not global_state.session_manager:
            logger.error("[DIAG] Critical failure: System services (DataManager/SessionManager) not initialized.")
            raise HTTPException(status_code=503, detail="System services not fully initialized.")
        
        logger.debug("[DIAG] System services seem to be initialized.")
        
        dm = global_state.data_manager
        
        if user_id == 'anonymous-user':
            logger.info(f"[DIAG] Handling anonymous user. Preparing default bootstrap data.")
            public_data = await dm.get_all_public_data(db)
            anonymous_config = dm._get_default_anonymous_config()

            response_payload = {
                "user_config": anonymous_config,
                "user_info": None,
                "system_status": { "model_is_ready": False, "api_key_count": 0, "verified_models": [] },
                "initial_sessions": [],
                "public_characters": public_data.get('character', {}),
                "public_presets": public_data.get('preset', {}),
                "public_world_info": public_data.get('world_info', {}),
                "public_groups": public_data.get('group', {}),
            }
            logger.info(f"[DIAG] Successfully prepared response for anonymous user.")
            return response_payload

        logger.debug(f"[DIAG] Querying database for registered user: {user_id}")
        user_result = await db.execute(select(User).where(User.user_id == user_id))
        user_db_obj = user_result.scalar_one_or_none()
        
        if not user_db_obj:
            logger.error(f"[DIAG] User with ID {user_id} not found in database.")
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found in database.")
        
        logger.debug(f"[DIAG] User '{user_db_obj.username}' found in DB. Proceeding...")

        logger.debug(f"[DIAG] Getting user config for '{user_db_obj.username}'...")
        user_config = await dm.get_user_config(user_id, db, db_user=user_db_obj)
        logger.debug(f"[DIAG] User config loaded.")
        
        user_info_payload = {
            "user_id": user_db_obj.user_id, "username": user_db_obj.username,
            "account_number": user_db_obj.account_number, "avatar": user_db_obj.avatar
        }

        active_char_filename = user_config.get("active_character")
        sessions = []
        if active_char_filename:
            logger.debug(f"[DIAG] Fetching initial sessions for character '{active_char_filename}'...")
            sessions = await global_state.session_manager.get_sessions_for_character(user_id, active_char_filename, db)
            logger.debug(f"[DIAG] Found {len(sessions)} initial sessions.")
        
        logger.debug(f"[DIAG] Fetching all public data...")
        public_data = await dm.get_all_public_data(db)
        logger.debug(f"[DIAG] Public data fetched.")

        response_payload = {
            "user_config": user_config,
            "user_info": user_info_payload,
            "system_status": {
                "model_is_ready": user_id in global_state.api_key_model_cache,
                "api_key_count": len(user_config.get("api_keys", [])),
                "verified_models": global_state.api_key_model_cache.get(user_id, []),
            },
            "initial_sessions": sessions,
            "public_characters": public_data.get('character', {}),
            "public_presets": public_data.get('preset', {}),
            "public_world_info": public_data.get('world_info', {}),
            "public_groups": public_data.get('group', {}),
        }
        logger.info(f"[DIAG] Successfully prepared response for user '{user_db_obj.username}'. Bootstrap complete.")
        return response_payload

    except HTTPException as e:
        logger.error(f"[DIAG] HTTP Exception in /bootstrap: {e.detail}")
        raise e
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.critical(f"!!!!!!!!!!!!!! [DIAG] CRITICAL ERROR IN BOOTSTRAP API !!!!!!!!!!!!!!")
        logger.critical(f"FATAL ERROR in bootstrap_user_data for user {user_id}:\n{tb_str}")
        logger.critical(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")

@router.post("/user_config/{user_id}")
async def update_user_config(user_id: str, config_data: Dict = Body(...), db: AsyncSession = DBSession):
    if not global_state.data_manager:
        raise HTTPException(status_code=503, detail="DataManager not initialized.")
        
    try:
        await global_state.data_manager.save_user_config(user_id, config_data, db)
        logger.info(f"[CONFIG] User '{user_id}' config updated successfully. Changed keys: {list(config_data.keys())}")
        await broadcast_status_update(
            {"user_id": user_id, "new_config": config_data},
            "user_config_updated"
        )
        return {"status": "success", "message": "User config updated successfully."}
    except Exception as e:
        logger.error(f"Failed to save config for user '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")

@router.post("/user_config/{user_id}/display_order")
async def update_display_order(user_id: str, payload: Dict = Body(...), db: AsyncSession = DBSession):
    data_type = payload.get("dataType")
    order = payload.get("order")
    
    if not data_type or not isinstance(order, list):
        raise HTTPException(status_code=400, detail="Invalid payload. 'dataType' and 'order' are required.")

    if not global_state.data_manager:
        raise HTTPException(status_code=503, detail="DataManager not initialized.")
    
    try:
        user_config = await global_state.data_manager.get_user_config(user_id, db)
        user_config.setdefault("display_order", {})[data_type] = order
        await global_state.data_manager.save_user_config(user_id, user_config, db)
        return {"status": "success", "message": f"{data_type} display order updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update display order: {e}")


@router.post("/user_config/{user_id}/generation_profiles")
async def update_generation_profiles(user_id: str, profiles: Dict = Body(...), db: AsyncSession = DBSession):
    if not global_state.data_manager:
        raise HTTPException(status_code=503, detail="DataManager not initialized.")
    
    try:
        user_config = await global_state.data_manager.get_user_config(user_id, db)
        user_config.setdefault("generation_profiles", {}).update(profiles)
        await global_state.data_manager.save_user_config(user_id, user_config, db)
        
        await broadcast_status_update(
            {"user_id": user_id, "generation_profiles": user_config["generation_profiles"]},
            "user_config_updated"
        )
        return {"status": "success", "message": "Generation profiles updated successfully."}
    except Exception as e:
        logger.error(f"Failed to update generation profiles for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save generation profiles: {e}")


@router.post("/session/{user_id}/temp_model")
async def set_temporary_model(user_id: str, payload: Dict = Body(...)):
    model = payload.get("model")
    if model:
        global_state.temp_model_sessions[user_id] = model
    elif user_id in global_state.temp_model_sessions:
        del global_state.temp_model_sessions[user_id]
    
    await broadcast_status_update(
        {"user_id": user_id, "temp_model": model},
        "session_model_updated"
    )
    return {"status": "success", "message": "Session model updated."}