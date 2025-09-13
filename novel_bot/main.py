import uvicorn
import pathlib
import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from src.plugins.ai_chat_system.services.initialization import initialize_system
from src.plugins.ai_chat_system.scheduler import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application is starting up...")
    try:
        await initialize_system()
        scheduler.start()
        print("Scheduler started.")
    except Exception as e:
        print(f"CRITICAL STARTUP FAILURE: {e}")
        traceback.print_exc()
    
    yield
    
    print("Application is shutting down...")
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler shut down.")

app = FastAPI(title="MyNovelBot API", lifespan=lifespan)

frontend_mode = os.environ.get("MYNOVELBOT_FRONTEND_MODE", "stable")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", f"http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.plugins.ai_chat_system.api import register_api_routes
register_api_routes(app)

if frontend_mode == 'stable':
    _current_dir = pathlib.Path(__file__).parent
    project_root = _current_dir.parent.resolve()
    frontend_path = project_root / "web-ui" / "dist-stable"

    if frontend_path.is_dir() and (frontend_path / "index.html").is_file():
        spa_app = FastAPI()
        
        spa_app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="spa_static")
        
        @spa_app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa_fallback(request: Request, full_path: str):
            return FileResponse(frontend_path / "index.html")

        app.mount("/", spa_app, name="frontend")
        print(f"Serving frontend from: {frontend_path}")
    else:
        print(f"WARNING: Frontend directory for stable mode not found at {frontend_path}")

if __name__ == "__main__":
    current_dir = pathlib.Path(__file__).parent
    reload_dirs = [str(current_dir / "src")]
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8080, 
        reload=True,
        reload_dirs=reload_dirs
    )