import asyncio
from fastapi import APIRouter, Body, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
from nonebot import logger
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..services import system_utils
from .. import global_state
from ..api_manager import ApiManager
from ..session_manager import SessionManager
from ..database.session import get_db_session
from ..database.models import Session, ChatMessage

router = APIRouter(prefix="/system", tags=["System Utilities"])
test_router = APIRouter()

class ApiKeyTestRequest(BaseModel):
    api_key: str
    proxy_url: str | None = None

class CheckModelsRequest(BaseModel):
    user_id: str

@test_router.post("/system/check_models")
async def check_user_models(payload: CheckModelsRequest, db: AsyncSession = Depends(get_db_session)):
    dm = global_state.data_manager
    if not dm:
        raise HTTPException(status_code=503, detail="DataManager not initialized.")
    
    user_config = await dm.get_user_config(payload.user_id, db)
    api_keys = user_config.get("api_keys", [])
    proxy_url = user_config.get("llm_service_config", {}).get("proxy")

    if not api_keys:
        raise HTTPException(status_code=400, detail="用户配置中未找到API Keys。")

    original_proxy = os.environ.get('HTTPS_PROXY')
    try:
        if proxy_url:
            os.environ['HTTPS_PROXY'] = proxy_url
            os.environ['HTTP_PROXY'] = proxy_url

        temp_api_manager = ApiManager(api_keys)
        await temp_api_manager.initialize_available_models()
        
        global_state.api_key_model_cache[payload.user_id] = temp_api_manager.verified_models
        
        if not temp_api_manager.verified_models:
             raise HTTPException(status_code=404, detail="API Keys有效，但未找到任何系统支持的可用模型。")

        return {
            "status": "success",
            "models": temp_api_manager.verified_models,
            "error": None
        }
    except Exception as e:
        logger.error(f"Failed to check models for user {payload.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"检查模型时发生错误: {str(e)}")
    finally:
        if original_proxy:
            os.environ['HTTPS_PROXY'] = original_proxy
            os.environ['HTTP_PROXY'] = original_proxy
        elif 'HTTPS_PROXY' in os.environ:
            del os.environ['HTTPS_PROXY']
            del os.environ['HTTP_PROXY']

@test_router.get("/system/token_usage_stats/{user_id}")
async def get_token_usage_stats(user_id: str, db: AsyncSession = Depends(get_db_session)):
    latest_session_stmt = select(Session).where(Session.owner_id == user_id).order_by(Session.last_updated_at.desc()).limit(1)
    result = await db.execute(latest_session_stmt)
    latest_session = result.scalar_one_or_none()

    if not latest_session:
        return {"hourly": 0, "daily": 0, "monthly": 0}

    messages_stmt = select(ChatMessage).where(ChatMessage.session_id == latest_session.id)
    result = await db.execute(messages_stmt)
    history = result.scalars().all()

    if not history:
        return {"hourly": 0, "daily": 0, "monthly": 0}

    total_tokens = 0
    message_count = 0
    for message in history:
        usage = message.token_usage
        if usage and isinstance(usage, dict) and "total_token_count" in usage:
            total_tokens += usage["total_token_count"]
            message_count += 1
    
    avg_tokens_per_message = total_tokens / message_count if message_count > 0 else 750

    hourly = avg_tokens_per_message * 20
    daily = hourly * 24
    monthly = daily * 30

    return {"hourly": int(hourly), "daily": int(daily), "monthly": int(monthly)}

@test_router.post("/system/test-api-key")
async def test_google_api_key(payload: ApiKeyTestRequest):
    if not payload.api_key:
        raise HTTPException(status_code=400, detail="API key is required.")
    original_proxy = os.environ.get('HTTPS_PROXY')
    try:
        if payload.proxy_url:
            os.environ['HTTPS_PROXY'] = payload.proxy_url
            os.environ['HTTP_PROXY'] = payload.proxy_url
        genai.configure(api_key=payload.api_key)
        await asyncio.wait_for(
            asyncio.to_thread(lambda: list(genai.list_models())),
            timeout=20.0
        )
        return {"status": "success", "message": "API Key is valid and working."}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out. Check network/proxy.")
    except Exception as e:
        error_message = str(e)
        if "API_KEY_INVALID" in error_message:
            detail = "API Key is invalid."
        elif "permission" in error_message.lower():
            detail = "Permission denied. Check the API Key's permissions."
        else:
            detail = f"An unknown error occurred: {error_message}"
        raise HTTPException(status_code=400, detail=detail)
    finally:
        if original_proxy:
            os.environ['HTTPS_PROXY'] = original_proxy
            os.environ['HTTP_PROXY'] = original_proxy
        elif 'HTTPS_PROXY' in os.environ:
            del os.environ['HTTPS_PROXY']
            del os.environ['HTTP_PROXY']

@router.get("/net-check")
async def perform_network_check(proxy_url: str | None = None):
    try:
        original_proxy = os.environ.get('HTTPS_PROXY')
        if proxy_url:
            os.environ['HTTPS_PROXY'] = proxy_url
            os.environ['HTTP_PROXY'] = proxy_url
        result = await system_utils.check_network_connectivity()
        if original_proxy:
             os.environ['HTTPS_PROXY'] = original_proxy
             os.environ['HTTP_PROXY'] = original_proxy
        elif 'HTTPS_PROXY' in os.environ:
            del os.environ['HTTPS_PROXY']
            del os.environ['HTTP_PROXY']
        if result["success"]:
            return {"status": "success", "message": result["message"]}
        else:
            raise HTTPException(status_code=503, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")