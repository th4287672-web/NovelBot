# 简体中文注释：
# MyNovelBot 旧版文件系统数据到 SQLite 迁移脚本 v1.3 (最终修正版)
#
# 描述:
# 此版本修复了因 user_configs.json 字段映射错误和事务管理问题
# 导致用户会话数据迁移失败的严重 Bug。

import asyncio
import json
import sqlite3
import sys
from pathlib import Path
import logging
import json5
from datetime import datetime
from dateutil.parser import parse as parse_datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# --- 核心设置 ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "novel_bot"))

from src.plugins.ai_chat_system.database.models import Base, User, ContentItem, Session, ChatMessage, SharedContent, Task

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

# --- 路径定义 ---
LEGACY_DATA_PATH = PROJECT_ROOT / "tools" / "legacy_backup" / "ai_chat"
TARGET_DB_FILE = PROJECT_ROOT / "novel_bot" / "data" / "mynovelbot.db"
SQLITE_URL = f"sqlite+aiosqlite:///{TARGET_DB_FILE}"

# --- SQLAlchemy 异步设置 ---
engine = create_async_engine(SQLITE_URL)
AsyncTargetSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# --- 数据迁移函数 --- (create_schema, read_json_file, migrate_public_data, migrate_community_data, migrate_tasks 保持不变)

async def create_schema():
    """在目标数据库中创建所有表结构"""
    TARGET_DB_FILE.parent.mkdir(exist_ok=True, parents=True)
    if TARGET_DB_FILE.exists():
        logging.warning(f"目标数据库 {TARGET_DB_FILE} 已存在，将被删除并重建。")
        TARGET_DB_FILE.unlink()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info(f"成功在 {TARGET_DB_FILE} 创建了新的数据库表结构。")

def read_json_file(path: Path):
    """健壮地读取 JSON 或 JSON5 文件"""
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json5.load(f)
    except Exception as e:
        logging.error(f"读取文件 {path} 失败: {e}")
        return None

async def migrate_public_data(session: AsyncSession):
    """迁移 public 目录下的所有 JSON 文件"""
    logging.info("--- 开始迁移公共数据 (public data)... ---")
    try:
        public_path = LEGACY_DATA_PATH / "public"
        if not public_path.is_dir():
            logging.warning("未找到 public 目录，跳过。")
            return

        data_types = ['characters', 'presets', 'world_info']
        for data_type_plural in data_types:
            data_type_singular = data_type_plural.rstrip('s')
            data_path = public_path / data_type_plural
            count = 0
            if data_path.is_dir():
                for json_file in data_path.glob("*.json"):
                    data = read_json_file(json_file)
                    if data:
                        item = ContentItem(owner_id=None, data_type=data_type_singular, filename=json_file.stem, data=data)
                        session.add(item)
                        count += 1
            logging.info(f"准备迁移 {count} 个公共 {data_type_plural}。")
        await session.commit()
        logging.info("公共数据迁移成功。")
    except Exception as e:
        await session.rollback()
        logging.error(f"迁移公共数据时出错: {e}", exc_info=True)


async def migrate_community_data(session: AsyncSession):
    """迁移社区数据"""
    logging.info("--- 开始迁移社区数据 (community data)... ---")
    try:
        community_db_path = LEGACY_DATA_PATH / "community" / "community.db"
        if not community_db_path.exists():
            logging.warning("未找到 community.db，跳过。")
            return

        conn = sqlite3.connect(community_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, data_type, name, description, tags, file_path, downloads, rating, created_at, is_approved FROM shared_content")
        rows = cursor.fetchall()
        
        for row in rows:
            created_at_dt = parse_datetime(row[9]) if row[9] else None
            
            new_shared_item = SharedContent(
                id=row[0], user_id=row[1], data_type=row[2], name=row[3],
                description=row[4], tags=json.loads(row[5]) if row[5] else [],
                file_path=row[6], downloads=row[7], rating=row[8],
                created_at=created_at_dt, is_approved=bool(row[10])
            )
            session.add(new_shared_item)
        
        await session.commit()
        logging.info(f"成功迁移 {len(rows)} 条社区分享记录。")
    except Exception as e:
        await session.rollback()
        logging.error(f"迁移 community.db 时出错: {e}", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close()


async def migrate_tasks(session: AsyncSession):
    """迁移任务数据"""
    logging.info("--- 开始迁移任务数据 (tasks data)... ---")
    try:
        tasks_db_path = LEGACY_DATA_PATH / "tasks.db"
        if not tasks_db_path.exists():
            logging.warning("未找到 tasks.db，跳过。")
            return

        conn = sqlite3.connect(tasks_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        rows = cursor.fetchall()
        
        for row in rows:
            task_data = dict(row)
            if isinstance(task_data.get('result'), str):
                try: task_data['result'] = json.loads(task_data['result'])
                except json.JSONDecodeError: pass
            if isinstance(task_data.get('error'), str):
                try: task_data['error'] = json.loads(task_data['error'])
                except json.JSONDecodeError: pass
            
            new_task = Task(**task_data)
            session.add(new_task)
            
        await session.commit()
        logging.info(f"成功迁移 {len(rows)} 条任务记录。")
    except Exception as e:
        await session.rollback()
        logging.error(f"迁移 tasks.db 时出错: {e}", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close()


async def migrate_user_data(session: AsyncSession):
    """迁移所有用户私有数据"""
    logging.info("--- 开始迁移用户数据 (user data)... ---")
    
    users_path = LEGACY_DATA_PATH / "users"
    if not users_path.is_dir():
        logging.critical("错误：未找到 'users' 目录！迁移无法继续。")
        return

    user_dirs = [d for d in users_path.iterdir() if d.is_dir() and d.name not in ['avatars', 'character_images']]
    total_users_migrated = 0

    for user_dir in user_dirs:
        try:
            async with session.begin_nested(): # [核心修复] 为每个用户创建一个子事务
                user_id = user_dir.name
                logging.info(f"  正在处理用户: {user_id}")
                
                user_config_path = user_dir / "config.json" # 修正文件名
                config_data = read_json_file(user_config_path) or {}
                
                # [核心修复] 手动进行字段映射
                new_user = User(
                    user_id=user_id,
                    username=f"LegacyUser_{user_id[:8]}",
                    account_number=user_id[:8],
                    password_hash="placeholder_hash_migrated",
                    active_character_filename=config_data.get("active_character"),
                    active_session_id=config_data.get("active_session_id"),
                    user_persona_filename=config_data.get("user_persona"),
                    preset_filename=config_data.get("preset"),
                    active_modules=config_data.get("active_modules", {}),
                    max_tokens=config_data.get("max_tokens", 4096),
                    session_world_info=config_data.get("world_info", []),
                    display_order=config_data.get("display_order", {}),
                    regex_rules=config_data.get("regex_rules", []),
                    generation_profiles=config_data.get("generation_profiles", {}),
                    deleted_public_items=config_data.get("deleted_public_items", []),
                    tts_voice_assignments=config_data.get("tts_voice_assignments", {}),
                    tts_service_config=config_data.get("tts_service_config", {}),
                    api_keys=config_data.get("api_keys", []),
                    llm_service_config=config_data.get("llm_service_config", {})
                )
                session.add(new_user)
                
                for data_type_plural in ['characters', 'presets', 'world_info']:
                    data_type_singular = data_type_plural.rstrip('s')
                    data_path = user_dir / data_type_plural
                    count = 0
                    if data_path.is_dir():
                        for json_file in data_path.glob("*.json"):
                            data = read_json_file(json_file)
                            if data:
                                item = ContentItem(owner_id=user_id, data_type=data_type_singular, filename=json_file.stem, data=data)
                                session.add(item)
                                count += 1
                    logging.info(f"    - 准备迁移 {count} 个私有 {data_type_plural}。")
                
                # [核心修复] 同时检查 'sessions' 和 'histories' 目录
                sessions_path = user_dir / "sessions"
                if not sessions_path.is_dir():
                    sessions_path = user_dir / "histories"

                session_count = 0
                message_count = 0
                if sessions_path.is_dir():
                    for session_file in sessions_path.rglob("*.json"):
                        char_filename = session_file.parent.name
                        session_id = session_file.stem
                        
                        session_data = read_json_file(session_file)
                        if session_data and isinstance(session_data, dict):
                            # [核心修复] 只提取 Session 模型需要的字段
                            new_session = Session(
                                id=session_id,
                                owner_id=user_id,
                                character_filename=char_filename,
                                title=session_data.get('title', '迁移的对话'),
                                created_at=session_data.get('created', 0),
                                last_updated_at=session_data.get('last_updated', 0)
                            )
                            session.add(new_session)
                            session_count += 1
                            
                            history = session_data.get('history', [])
                            if isinstance(history, list):
                                for i, msg in enumerate(history):
                                    if msg and 'role' in msg and 'content' in msg:
                                        new_msg = ChatMessage(
                                            session_id=session_id, 
                                            timestamp=session_data.get('last_updated', 0) + i, 
                                            role=msg.get('role'),
                                            content=msg.get('content'),
                                            token_usage=msg.get('tokenUsage')
                                        )
                                        session.add(new_msg)
                                        message_count += 1
                logging.info(f"    - 准备迁移 {session_count} 个会话和 {message_count} 条消息。")
            
            await session.commit() # 提交这个用户的子事务
            total_users_migrated += 1
            logging.info(f"  成功提交用户 {user_id} 的所有数据。")

        except Exception as e:
            logging.error(f"处理用户 {user_dir.name} 时发生严重错误，该用户的数据将被跳过: {e}", exc_info=True)
            # 外部的 try/except 会处理回滚
            raise

    logging.info(f"成功迁移了 {total_users_migrated} 个用户的数据。")


async def main():
    """脚本主入口"""
    logging.info("==============================================")
    logging.info(" MyNovelBot 旧数据迁移工具 v1.3")
    logging.info("==============================================")
    
    if not LEGACY_DATA_PATH.is_dir():
        logging.critical(f"错误: 未找到旧数据备份目录: {LEGACY_DATA_PATH}")
        return

    await create_schema()
    
    async with AsyncTargetSession() as session:
        await migrate_public_data(session)
        await migrate_community_data(session)
        await migrate_tasks(session)
        try:
            await migrate_user_data(session)
        except Exception:
            logging.critical("在迁移用户数据时发生了一个或多个错误，部分用户可能未被迁移。请检查上面的日志。")
            await session.rollback()

    logging.info("\n所有任务已完成！")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n发生了一个无法恢复的错误: {e}")