# novel_bot/src/plugins/ai_chat_system/database/session.py

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi import Depends
from nonebot import logger

from .models import Base

engine = None
AsyncSessionLocal = None

def initialize_database(db_url: str):
    global engine, AsyncSessionLocal
    try:
        # [核心修复] 添加连接池参数以提高健壮性
        engine = create_async_engine(
            db_url, 
            echo=False,
            pool_size=10,  # 增加连接池大小
            max_overflow=20, # 允许额外的临时连接
            pool_recycle=3600, # 每小时回收一次连接，防止连接因空闲而失效
            pool_pre_ping=True # 在每次从池中获取连接时，先执行一个简单的 "ping" 查询来检查其有效性
        )
        AsyncSessionLocal = async_sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("Database engine and session maker initialized successfully with robust pool settings.")
    except Exception as e:
        logger.critical(f"Failed to initialize database connection: {e}", exc_info=True)
        raise

async def create_db_and_tables():
    if not engine:
        raise RuntimeError("Database engine not initialized.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified.")

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if not AsyncSessionLocal:
        raise RuntimeError("Database session maker not initialized.")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            
DBSession = Depends(get_db_session)