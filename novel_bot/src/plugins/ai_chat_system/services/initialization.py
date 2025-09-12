import os
import toml
import asyncio
import nonebot
from pathlib import Path
from nonebot import logger
import sys

from ..services.file_watcher import start_file_watcher
from ..services.archival_service import initialize_data_conduit
from ..database.session import initialize_database, create_db_and_tables

from .. import global_state
from ..data_manager import DataManager
from ..session_manager import SessionManager

PROJECT_ROOT = Path(__file__).resolve().parents[5] 
CONFIG_PATH = PROJECT_ROOT / "novel_bot" / "config.toml"

async def reconfigure_system():
    logger.info("System Reconfiguration: Starting hot reload of config.toml...")
    proxy_url = None
    db_url = None
    try:
        config_data = {}
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config_data = toml.load(f)
        
        proxy_url = config_data.get("ai_chat", {}).get("google_api_proxy")
        
        db_config = config_data.get("database", {})
        db_type = os.environ.get("DB_TYPE", db_config.get("db_type", "sqlite"))

        if db_type == "sqlite":
            sqlite_path_str = db_config.get("sqlite", {}).get("path", "novel_bot/data/mynovelbot.db")
            sqlite_path = PROJECT_ROOT / sqlite_path_str
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite+aiosqlite:///{sqlite_path.resolve()}"
            logger.info(f"System Reconfiguration: Using SQLite database at '{sqlite_path}'.")
        elif db_type == "postgres":
            db_url = db_config.get("postgres", {}).get("url")
            if not db_url:
                raise ValueError("DB_TYPE is 'postgres', but no PostgreSQL URL found in config.toml.")
            logger.info("System Reconfiguration: Using PostgreSQL database.")
        else:
            raise ValueError(f"Unsupported DB_TYPE: '{db_type}'. Must be 'sqlite' or 'postgres'.")

        if not db_url:
            raise ValueError("Database URL could not be determined. Please check config.toml.")

        initialize_database(db_url)
        await create_db_and_tables()
        
        gcs_config = config_data.get("google_cloud", {})
        initialize_data_conduit(
            key_path=gcs_config.get("service_account_key_path"),
            bucket_name=gcs_config.get("developer_backup_bucket")
        )

        if proxy_url:
            logger.info(f"System Reconfiguration: Setting HTTPS_PROXY environment variable to '{proxy_url}'.")
            os.environ['HTTPS_PROXY'] = proxy_url
            os.environ['HTTP_PROXY'] = proxy_url
        else:
            if 'HTTPS_PROXY' in os.environ: del os.environ['HTTPS_PROXY']
            if 'HTTP_PROXY' in os.environ: del os.environ['HTTP_PROXY']
            logger.info("System Reconfiguration: No proxy found. Cleared proxy environment variables.")
        
        logger.info("System Reconfiguration: Hot reload complete.")

    except Exception as e:
        logger.error(f"System Reconfiguration: Critical error during hot reload.", exc_info=True)
        raise

async def initialize_system():
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / "backend_trace.log"
    
    logger.remove()
    
    logger.add(
        sys.stderr, level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    logger.add(
        log_file_path, level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB", retention="7 days", encoding="utf-8",
        enqueue=True, backtrace=True, diagnose=True
    )
    
    logger.info("AI_CHAT [Init]: Logger configured. Starting system initialization...")
    
    try:
        await reconfigure_system()
    except Exception:
        logger.critical("Initialization failed during system reconfiguration. Aborting startup.")
        raise

    global_state.data_manager = DataManager()
    global_state.session_manager = SessionManager()
    logger.trace("AI_CHAT [Init]: DataManager and SessionManager instantiated.")
    
    try:
        main_loop = asyncio.get_running_loop()
        start_file_watcher(main_loop)
    except RuntimeError:
        logger.error("AI_CHAT: Could not get running event loop for file watcher.")

    logger.trace("AI_CHAT [Init]: System initialization process finished.")
    
    global_state.initialization_complete.set()
    logger.info("AI_CHAT [Init]: 'initialization_complete' signal set. System is fully ready.")