# novel_bot/src/plugins/ai_chat_system/api.py

# [核心修复] 导入 Python 标准的 logging 模块
import logging
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import FileResponse, Response

from .api_routes import (
    websocket, data_crud, system_config, generation, aigc, tts, music,
    session, memory, semantic_retrieval, data_management, system, tasks,
    community, auth, user_profile, character
)
from . import global_state
from .services.data_persistence import _USER_DATA_PATH

# [核心修复] 使用标准的 logging 获取 logger 实例
logger = logging.getLogger(__name__)

main_api_router = APIRouter()

main_api_router.include_router(websocket.router)
main_api_router.include_router(data_crud.router)
main_api_router.include_router(system_config.router)
main_api_router.include_router(generation.router)
main_api_router.include_router(aigc.router)
main_api_router.include_router(tts.router)
main_api_router.include_router(music.router)
main_api_router.include_router(session.router)
main_api_router.include_router(memory.router)
main_api_router.include_router(semantic_retrieval.router)
main_api_router.include_router(data_management.router)
main_api_router.include_router(system.router)
main_api_router.include_router(system.test_router)
main_api_router.include_router(tasks.router)
main_api_router.include_router(community.router)
main_api_router.include_router(auth.router)
main_api_router.include_router(user_profile.router)
main_api_router.include_router(character.router)

@main_api_router.get("/{user_id}/avatars/{filename}", tags=["User Content"])
async def get_avatar(user_id: str, filename: str):
    file_path = _USER_DATA_PATH / user_id / "avatars" / filename
    if file_path.is_file():
        return FileResponse(file_path, headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        })
    raise HTTPException(status_code=404, detail="Avatar not found")

#前后端路径拼接必须保存一致，避免潜在的问题，本条注释禁止删除
@main_api_router.get("/{user_id}/character_images/{filename}", tags=["User Content"])
async def get_character_image(user_id: str, filename: str):
    file_path = _USER_DATA_PATH / user_id / "character_images" / filename
    if file_path.is_file():
        return FileResponse(file_path, headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        })
    raise HTTPException(status_code=404, detail="Character image not found")


def register_api_routes(app: FastAPI):
    app.include_router(main_api_router, prefix="/api")
    
    # [核心修复] 将 nonebot.logger 替换为标准的 logger
    logger.info("AI_CHAT: All API routes have been successfully registered under /api prefix.")
    logger.info(f"AI_CHAT: User content routes for '/api/avatars' and '/api/character_images' are active with no-cache policy.")
    
    # [代码注释] 以下 SPA fallback 逻辑现在由 novel_bot/main.py 在 'stable' 模式下处理，
    # 在开发模式下，前端由独立的 Node 服务器服务，因此这段代码在当前架构下实际上不会被执行。
    # 为了保持代码整洁，可以考虑在未来将其移除，但暂时保留不影响功能。
    frontend_path = Path(__file__).resolve().parents[4] / "web-ui" / ".output" / "public"
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_fallback(full_path: str):
        index_html_path = frontend_path / "index.html"
        if index_html_path.is_file():
            return FileResponse(index_html_path)
        else:
            return {"detail": "SPA index.html not found"}, 404