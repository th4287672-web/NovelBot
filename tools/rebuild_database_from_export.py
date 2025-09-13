import asyncio
import json
import sys
from pathlib import Path
import logging
import toml
import uuid
import random
import string
import types
from collections import defaultdict

# --- 猴子补丁 (Monkey Patch) ---
try:
    import bcrypt
    if not hasattr(bcrypt, '__about__'):
        about_module = types.ModuleType('__about__')
        about_module.__version__ = '4.0.1'
        bcrypt.__about__ = about_module
        logging.debug("成功应用猴子补丁以修复 bcrypt 版本读取警告。")
except ImportError:
    pass
# --- 补丁结束 ---

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "novel_bot"))

from src.plugins.ai_chat_system.database.models import Base, User, ContentItem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)

CONFIG_PATH = PROJECT_ROOT / "novel_bot" / "config.toml"
TARGET_DB_FILE = PROJECT_ROOT / "novel_bot" / "data" / "mynovelbot.db"
SQLITE_URL = f"sqlite+aiosqlite:///{TARGET_DB_FILE}"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def create_schema(engine):
    """在目标数据库中创建所有表结构"""
    TARGET_DB_FILE.parent.mkdir(exist_ok=True, parents=True)
    if TARGET_DB_FILE.exists():
        logging.warning(f"目标数据库 {TARGET_DB_FILE.name} 已存在，将被删除并重建。")
        TARGET_DB_FILE.unlink()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info(f"成功在 {TARGET_DB_FILE.name} 创建了新的数据库表结构。")

def read_json_file(path: Path):
    """健壮地读取 JSON 文件"""
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"读取文件 {path} 失败: {e}")
        return None

async def main():
    """脚本主入口"""
    print("======================================================")
    print(" MyNovelBot 数据库从导出文件重建工具 v1.1 (详细日志版)")
    print("======================================================")
    
    export_dir_path_str = input(f"\n请输入包含 'public' 和 'private' 文件夹的导出目录路径\n(例如: {PROJECT_ROOT / 'tools' / 'flattened_export_...'})\n> ")
    export_dir = Path(export_dir_path_str)

    if not export_dir.is_dir() or not (export_dir / "public").is_dir() or not (export_dir / "private").is_dir():
        print(f"\n错误: 路径 '{export_dir}' 无效或缺少 'public'/'private' 子目录。")
        return

    print(f"\n将从以下路径读取数据: {export_dir}")
    print(f"将要写入并覆盖数据库: {TARGET_DB_FILE}")
    confirm = input("这是一个不可逆的操作。您确定要继续吗？ (y/n): ").lower()
    
    if confirm != 'y':
        print("\n操作已取消。")
        return

    engine = create_async_engine(SQLITE_URL)
    AsyncTargetSession = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    await create_schema(engine)

    stats = {
        "users_created": 0,
        "private": defaultdict(int),
        "public": defaultdict(int),
    }

    async with AsyncTargetSession() as session:
        # 处理私有数据
        logging.info("\n--- 开始处理私有数据 ---")
        private_path = export_dir / "private"
        user_dirs = [d for d in private_path.iterdir() if d.is_dir()]
        
        for user_dir in user_dirs:
            user_id = user_dir.name
            username = f"LegacyUser_{user_id[:8]}"
            account_number = ''.join(random.choices(string.digits, k=8))
            
            new_user = User(
                user_id=user_id,
                username=username,
                account_number=account_number,
                password_hash=get_password_hash("123456"),
            )
            session.add(new_user)
            stats["users_created"] += 1
            logging.info(f"  [用户] 准备创建用户 '{username}' (ID: {user_id})")

            for data_type_plural in ['characters', 'presets', 'world_infos', 'groups', 'personas']:
                data_path = user_dir / data_type_plural
                if data_path.is_dir():
                    count = 0
                    data_type_singular = data_type_plural.rstrip('s')
                    for json_file in data_path.glob("*.json"):
                        data = read_json_file(json_file)
                        if data:
                            item = ContentItem(owner_id=user_id, data_type=data_type_singular, filename=json_file.stem, data=data)
                            session.add(item)
                            count += 1
                    stats["private"][data_type_singular] += count
                    logging.info(f"    - [私有/{data_type_plural}] 找到并准备导入 {count} 个文件。")

        # 处理公共数据
        logging.info("\n--- 开始处理公共数据 ---")
        public_path = export_dir / "public"
        for data_type_plural in ['characters', 'presets', 'world_infos', 'groups', 'histories']:
            data_path = public_path / data_type_plural
            if data_path.is_dir():
                count = 0
                data_type_singular = data_type_plural.rstrip('s')
                for json_file in data_path.glob("*.json"):
                    data = read_json_file(json_file)
                    if data:
                        item = ContentItem(owner_id=None, data_type=data_type_singular, filename=json_file.stem, data=data)
                        session.add(item)
                        count += 1
                stats["public"][data_type_singular] += count
                logging.info(f"    - [公共/{data_type_plural}] 找到并准备导入 {count} 个文件。")
        
        try:
            await session.commit()
            total_private = sum(stats["private"].values())
            total_public = sum(stats["public"].values())
            
            print("\n======================= 成功 =======================")
            print("数据库已成功根据导出文件重建！")
            print("\n[详细报告]")
            print(f"  - 创建的用户总数: {stats['users_created']}")
            print(f"  - 导入的私有项目总数: {total_private}")
            for dtype, count in sorted(stats["private"].items()):
                print(f"    - {dtype.replace('_', ' ').capitalize()}: {count} 个")
            print(f"  - 导入的公共项目总数: {total_public}")
            for dtype, count in sorted(stats["public"].items()):
                print(f"    - {dtype.replace('_', ' ').capitalize()}: {count} 个")
            print("====================================================")
        except Exception as e:
            await session.rollback()
            print(f"\n错误: 在提交到数据库时发生错误: {e}")
            logging.error("数据库提交失败", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n发生了一个无法恢复的错误: {e}")