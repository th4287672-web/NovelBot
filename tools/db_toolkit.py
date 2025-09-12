import asyncio
import sys
import json
import os
import re
from pathlib import Path
import logging
from datetime import datetime
import copy
from typing import List, Dict, Any
import toml

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "novel_bot"))

from src.plugins.ai_chat_system.database.models import Base, User, ContentItem, Session, ChatMessage, SharedContent, Task

logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
CONFIG_PATH = PROJECT_ROOT / "novel_bot" / "config.toml"

engine = None
AsyncSessionLocal = None

class Colors:
    HEADER = '\033[95m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GREY = '\033[90m'

def cprint(text: str, color: str = Colors.ENDC, bold: bool = False):
    bold_code = Colors.BOLD if bold else ''
    print(f"{bold_code}{color}{text}{Colors.ENDC}")

async def initialize_engine():
    global engine, AsyncSessionLocal
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"配置文件未找到: {CONFIG_PATH}")
    
    config_data = toml.load(CONFIG_PATH)
    db_config = config_data.get("database", {})
    db_type = os.environ.get("DB_TYPE", db_config.get("db_type", "sqlite"))

    db_url = ""
    if db_type == "sqlite":
        sqlite_path_str = db_config.get("sqlite", {}).get("path", "novel_bot/data/mynovelbot.db")
        sqlite_path = PROJECT_ROOT / sqlite_path_str
        if not sqlite_path.exists():
            raise FileNotFoundError(f"SQLite数据库文件未找到: {sqlite_path}")
        db_url = f"sqlite+aiosqlite:///{sqlite_path.resolve()}"
        cprint(f"检测到 SQLite 配置，正在连接: {sqlite_path.name}", Colors.GREEN)
    elif db_type == "postgres":
        db_url = db_config.get("postgres", {}).get("url")
        cprint(f"检测到 PostgreSQL 配置，正在连接...", Colors.GREEN)
    else:
        raise ValueError(f"不支持的数据库类型: {db_type}。请在 config.toml 中配置 'sqlite' 或 'postgres'。")

    if not db_url:
        raise ValueError("无法确定数据库连接URL，请检查 config.toml 文件。")

    engine = create_async_engine(db_url)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str, breadcrumbs: str = ""):
    clear_screen()
    width = 80
    cprint("=" * width, Colors.CYAN)
    title_line = f" {title} "
    padding = (width - len(title_line)) // 2
    cprint("=" * padding + f" {Colors.BOLD}{title}{Colors.ENDC}{Colors.CYAN} " + "=" * (width - padding - len(title_line)), Colors.CYAN)
    
    if breadcrumbs:
        cprint(f" 路径: {breadcrumbs}".ljust(width - 1) + "=", Colors.CYAN)
    cprint("=" * width, Colors.CYAN)
    print()

def get_display_width(text: str) -> int:
    width = 0
    for char in str(text):
        width += 2 if '\u4e00' <= char <= '\u9fff' else 1
    return width

def print_table(headers: List[str], rows: List[List[Any]], indent: int = 2):
    if not rows:
        print(" " * indent + "(无内容)")
        return
    
    widths = [get_display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], get_display_width(str(cell)))
            
    def pad_str(text: str, width: int) -> str:
        return str(text) + ' ' * (width - get_display_width(str(text)))

    header_line = " | ".join(f"{Colors.YELLOW}{pad_str(h, w)}{Colors.ENDC}" for h, w in zip(headers, widths))
    print(" " * indent + header_line)
    
    separator_line = "-+-".join("-" * w for w in widths)
    print(" " * indent + separator_line)
    
    for row in rows:
        row_line = " | ".join(pad_str(c, w) for c, w in zip(row, widths))
        print(" " * indent + row_line)

def get_user_input(prompt: str = "请输入选项 > ") -> str:
    return input(f"{Colors.CYAN}{prompt}{Colors.ENDC}").lower().strip()

def get_confirmation(warning_text: str) -> bool:
    cprint(f"\n警告: {warning_text}", Colors.YELLOW)
    choice = input(f"{Colors.RED}{Colors.BOLD}这是一个不可逆的永久性操作。您确定要写入数据库吗？(y/n) > {Colors.ENDC}").lower().strip()
    return choice == 'y'

def format_content_item_data(data_type: str, data: dict) -> str:
    output = []

    def append_field(title, key, default=""):
        value = data.get(key)
        display_value = ""
        if value is None or (isinstance(value, str) and not value.strip()):
            display_value = f"{Colors.GREY}(未设置){Colors.ENDC}"
        elif isinstance(value, list):
            if not value:
                display_value = f"{Colors.GREY}(空列表){Colors.ENDC}"
            else:
                display_value = "\n".join([f"      - {v}" for v in value])
        else:
            display_value = str(value).strip()

        output.append(f"  {Colors.CYAN}{title}:{Colors.ENDC}")
        output.append(f"    {display_value.replace('\n', '\n    ')}\n")

    if data_type == 'character':
        append_field("显示名称 (displayName)", "displayName")
        append_field("描述 (description)", "description")
        append_field("性格 (personality)", "personality")
        append_field("开场白 (first_mes)", "first_mes")
        append_field("对话示例 (mes_example)", "mes_example")
        append_field("关联世界书 (linked_worlds)", "linked_worlds")
    elif data_type == 'preset':
        append_field("预设名称 (displayName)", "displayName")
        modules = data.get('prompts', [])
        output.append(f"  {Colors.CYAN}模块 ({len(modules)}个):{Colors.ENDC}")
        for i, module in enumerate(modules, 1):
            if isinstance(module, dict):
                output.append(f"    {Colors.YELLOW}--- 模块 {i}: {module.get('name', '未命名模块')} ---{Colors.ENDC}")
                output.append(f"      ID: {module.get('identifier')}")
                output.append(f"      角色: {module.get('role')}")
                content_full = str(module.get('content', '')).strip()
                indented_content = content_full.replace('\n', '\n        ')
                output.append(f"      内容: {Colors.GREY}\n        {indented_content}{Colors.ENDC}")
            else:
                output.append(f"    {Colors.RED}--- 模块 {i} (格式异常: {type(module)}) ---{Colors.ENDC}")

    elif data_type == 'world_info':
        append_field("世界书名称 (name)", "name")
        entries = data.get('entries', [])
        output.append(f"  {Colors.CYAN}条目 ({len(entries) if isinstance(entries, list) else '未知数量'}):{Colors.ENDC}")
        
        if isinstance(entries, list):
            for i, entry in enumerate(entries, 1):
                if isinstance(entry, dict):
                    keywords = ", ".join(entry.get('keywords', []))
                    output.append(f"    {Colors.YELLOW}--- 条目 {i}: {entry.get('name', '未命名')} (关键词: {keywords}) ---{Colors.ENDC}")
                    content_full = str(entry.get('content', '')).strip()
                    indented_content = content_full.replace('\n', '\n        ')
                    output.append(f"      内容:\n        {Colors.GREY}{indented_content}{Colors.ENDC}")
                elif isinstance(entry, str):
                    output.append(f"    {Colors.YELLOW}--- 原始条目 {i} (字符串格式) ---{Colors.ENDC}")
                    json_formatted_string = json.dumps(entry, ensure_ascii=False, indent=2)
                    indented_json = "\n".join("      " + line for line in json_formatted_string.splitlines())
                    output.append(f"      内容 (原始JSON字符串):\n{Colors.GREY}{indented_json}{Colors.ENDC}")
                else:
                    output.append(f"    {Colors.RED}--- 未知条目类型 {i}: {type(entry)} ---{Colors.ENDC}")
        else:
             output.append(f"    {Colors.RED}内容格式异常: 'entries' 字段不是列表。{Colors.ENDC}")

    else:
        return json.dumps(data, ensure_ascii=False, indent=2)
    return "\n".join(output)

async def view_main_menu():
    while True:
        print_header("MyNovelBot 数据库交互式工具箱")
        cprint("[1] 查看数据 (View Data)", Colors.GREEN)
        cprint("[2] 工具与修复 (Tools & Fixes)", Colors.YELLOW)
        cprint("[3] 数据导出/诊断 (Data Export/Diagnosis)", Colors.BLUE)
        print("\n[q] 退出")
        
        choice = get_user_input()
        if choice == '1': await view_data_menu()
        elif choice == '2': await view_tools_menu()
        elif choice == '3': await view_export_menu()
        elif choice == 'q': return

async def view_data_menu(breadcrumbs: str = "查看数据"):
    while True:
        async with AsyncSessionLocal() as session:
            public_count = await session.scalar(select(func.count()).select_from(ContentItem).where(ContentItem.owner_id.is_(None)))
            user_count = await session.scalar(select(func.count()).select_from(User))
            community_count = await session.scalar(select(func.count()).select_from(SharedContent))
            task_count = await session.scalar(select(func.count()).select_from(Task))

        print_header("查看数据", breadcrumbs)
        print(f"[1] 公共数据库 (Public Data)     {Colors.GREY}({public_count} 个项目){Colors.ENDC}")
        print(f"[2] 私有用户数据库 (Private User) {Colors.GREY}({user_count} 个用户){Colors.ENDC}")
        print(f"[3] 社区分享数据库 (Community)  {Colors.GREY}({community_count} 个分享){Colors.ENDC}")
        print(f"[4] 后台任务数据库 (Tasks)      {Colors.GREY}({task_count} 个任务){Colors.ENDC}")
        print("\n[b] 返回主菜单")
        
        choice = get_user_input()
        if choice == '1': await view_public_data_menu(breadcrumbs)
        elif choice == '2': await view_user_list_menu(breadcrumbs)
        elif choice == '3': await view_community_list_menu(breadcrumbs)
        elif choice == '4': await view_task_list_menu(breadcrumbs)
        elif choice == 'b': return

async def view_public_data_menu(breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > 公共数据库"
    while True:
        async with AsyncSessionLocal() as session:
            counts = await session.execute(
                select(ContentItem.data_type, func.count(ContentItem.id))
                .where(ContentItem.owner_id.is_(None))
                .group_by(ContentItem.data_type)
            )
            counts_map = dict(counts.all())

        print_header("公共数据库", breadcrumbs)
        print(f"[1] 角色卡 (Characters) {Colors.GREY}({counts_map.get('character', 0)} 个){Colors.ENDC}")
        print(f"[2] 预设 (Presets)     {Colors.GREY}({counts_map.get('preset', 0)} 个){Colors.ENDC}")
        print(f"[3] 世界书 (World Info)  {Colors.GREY}({counts_map.get('world_info', 0)} 个){Colors.ENDC}")
        print("\n[b] 返回上一级")
        
        choice = get_user_input()
        if choice == '1': await view_content_item_list(None, 'character', breadcrumbs)
        elif choice == '2': await view_content_item_list(None, 'preset', breadcrumbs)
        elif choice == '3': await view_content_item_list(None, 'world_info', breadcrumbs)
        elif choice == 'b': return

async def view_user_list_menu(breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > 用户列表"
    while True:
        async with AsyncSessionLocal() as session:
            users = (await session.execute(select(User).order_by(User.username))).scalars().all()
        
        print_header("用户列表", breadcrumbs)
        if not users:
            print("数据库中没有用户。")
        else:
            for i, user in enumerate(users, 1):
                print(f"[{i}] {Colors.GREEN}{user.username}{Colors.ENDC} {Colors.GREY}(ID: {user.user_id}){Colors.ENDC}")

        print("\n[b] 返回上一级")
        choice = get_user_input("请输入用户序号或 [b] > ")
        
        if choice == 'b': return
        try:
            user_index = int(choice) - 1
            if 0 <= user_index < len(users):
                await view_user_detail_menu(users[user_index], breadcrumbs)
        except (ValueError, IndexError):
            cprint("无效输入。", Colors.RED)
            await asyncio.sleep(1)

async def view_user_detail_menu(user: User, breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > {user.username}"
    while True:
        async with AsyncSessionLocal() as session:
            content_counts = await session.execute(
                select(ContentItem.data_type, func.count(ContentItem.id))
                .where(ContentItem.owner_id == user.user_id)
                .group_by(ContentItem.data_type)
            )
            counts_map = dict(content_counts.all())
            session_count = await session.scalar(
                select(func.count()).select_from(Session).where(Session.owner_id == user.user_id)
            )

        print_header(f"用户: {user.username}", breadcrumbs)
        cprint(f"用户ID: {user.user_id}", Colors.GREY)
        cprint(f"账号: {user.account_number}", Colors.GREY)
        cprint(f"创建于: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}", Colors.GREY)

        print("\n--- 用户私有内容 ---")
        print(f"[1] 角色卡     {Colors.GREY}({counts_map.get('character', 0)} 个){Colors.ENDC}")
        print(f"[2] 预设         {Colors.GREY}({counts_map.get('preset', 0)} 个){Colors.ENDC}")
        print(f"[3] 世界书       {Colors.GREY}({counts_map.get('world_info', 0)} 个){Colors.ENDC}")
        print(f"[4] 对话会话     {Colors.GREY}({session_count} 个){Colors.ENDC}")
        print("\n[b] 返回用户列表")

        choice = get_user_input()
        if choice == '1': await view_content_item_list(user.user_id, 'character', breadcrumbs)
        elif choice == '2': await view_content_item_list(user.user_id, 'preset', breadcrumbs)
        elif choice == '3': await view_content_item_list(user.user_id, 'world_info', breadcrumbs)
        elif choice == '4': await view_session_char_list_menu(user.user_id, breadcrumbs)
        elif choice == 'b': return

async def view_content_item_list(user_id: str | None, data_type: str, breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > {data_type.capitalize()} 列表"
    while True:
        async with AsyncSessionLocal() as session:
            stmt = select(ContentItem).where(ContentItem.owner_id == user_id, ContentItem.data_type == data_type).order_by(ContentItem.filename)
            items = (await session.execute(stmt)).scalars().all()

        print_header(f"{data_type.capitalize()} 列表", breadcrumbs)
        if not items:
            print("没有找到内容。")
        else:
            for i, item in enumerate(items, 1):
                display_name = item.data.get('displayName') or item.data.get('name', 'N/A')
                print(f"[{i}] {Colors.GREEN}{item.filename}{Colors.ENDC} {Colors.GREY}(显示名称: {display_name}){Colors.ENDC}")
        
        print("\n[b] 返回上一级")
        choice = get_user_input("请输入序号查看详情或 [b] > ")

        if choice == 'b': return
        try:
            item_index = int(choice) - 1
            if 0 <= item_index < len(items):
                await view_content_item_detail(items[item_index], breadcrumbs)
        except (ValueError, IndexError):
            cprint("无效输入。", Colors.RED)
            await asyncio.sleep(1)

async def view_content_item_detail(item: ContentItem, breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > {item.filename}"
    show_raw = False

    while True:
        print_header(f"详情: {item.filename}", breadcrumbs)
        
        if not show_raw:
            cprint("--- 美化视图 ---", Colors.YELLOW, bold=True)
            formatted_output = format_content_item_data(item.data_type, item.data)
            print(formatted_output)
            prompt_text = "[r] 查看原始JSON, [b] 返回列表"
        else:
            cprint("--- 原始数据 (Raw JSON) ---", Colors.YELLOW, bold=True)
            try:
                raw_json = json.dumps(item.data, ensure_ascii=False, indent=2)
                print(f"{Colors.GREY}{raw_json}{Colors.ENDC}")
            except Exception as e:
                cprint(f"无法序列化为JSON: {e}", Colors.RED)
            prompt_text = "[r] 查看美化视图, [b] 返回列表"
            
        choice = get_user_input(f"\n{prompt_text} > ")
        if choice == 'r':
            show_raw = not show_raw
        elif choice == 'b':
            return

async def view_session_char_list_menu(user_id: str, breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > 对话会话"
    while True:
        async with AsyncSessionLocal() as session:
            stmt = (select(Session.character_filename, func.count(Session.id))
                    .where(Session.owner_id == user_id)
                    .group_by(Session.character_filename)
                    .order_by(Session.character_filename))
            char_groups = (await session.execute(stmt)).all()
        
        print_header("选择角色查看会话", breadcrumbs)
        if not char_groups:
            print("该用户没有会话记录。")
        else:
            for i, (char_filename, count) in enumerate(char_groups, 1):
                print(f"[{i}] {Colors.GREEN}{char_filename}{Colors.ENDC} {Colors.GREY}({count} 个会话){Colors.ENDC}")
        
        print("\n[b] 返回上一级")
        choice = get_user_input("请输入序号或 [b] > ")

        if choice == 'b': return
        try:
            group_index = int(choice) - 1
            if 0 <= group_index < len(char_groups):
                await view_session_list_menu(user_id, char_groups[group_index][0], breadcrumbs)
        except (ValueError, IndexError):
            cprint("无效输入。", Colors.RED)
            await asyncio.sleep(1)

async def view_session_list_menu(user_id: str, char_filename: str, breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > {char_filename}"
    while True:
        async with AsyncSessionLocal() as session:
            stmt = (select(Session)
                    .where(Session.owner_id == user_id, Session.character_filename == char_filename)
                    .order_by(Session.last_updated_at.desc()))
            sessions = (await session.execute(stmt)).scalars().all()
        
        print_header(f"会话列表 for {char_filename}", breadcrumbs)
        if not sessions:
            print("该角色没有会话记录。")
        else:
            for i, s in enumerate(sessions, 1):
                last_updated = datetime.fromtimestamp(s.last_updated_at).strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{i}] {Colors.GREEN}{s.title}{Colors.ENDC} {Colors.GREY}(ID: {s.id[:8]}... | 最后更新: {last_updated}){Colors.ENDC}")
        
        print("\n[b] 返回上一级")
        choice = get_user_input("请输入序号查看详情或 [b] > ")

        if choice == 'b': return
        try:
            session_index = int(choice) - 1
            if 0 <= session_index < len(sessions):
                await view_chat_message_list(sessions[session_index], breadcrumbs)
        except (ValueError, IndexError):
            cprint("无效输入。", Colors.RED)
            await asyncio.sleep(1)

async def view_chat_message_list(session_obj: Session, breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > {session_obj.title}"
    offset = 0
    page_size = 15
    while True:
        async with AsyncSessionLocal() as session:
            stmt = (select(ChatMessage)
                    .where(ChatMessage.session_id == session_obj.id)
                    .order_by(ChatMessage.timestamp)
                    .offset(offset).limit(page_size))
            messages = (await session.execute(stmt)).scalars().all()
            total_stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == session_obj.id)
            total_messages = (await session.execute(total_stmt)).scalar_one()

        print_header(f"聊天记录: {session_obj.title}", breadcrumbs)
        print(f"{Colors.GREY}(共 {total_messages} 条消息, 当前显示 {offset + 1}-{min(offset + page_size, total_messages)}){Colors.ENDC}")
        
        if not messages:
            print("该会话没有消息。")
        else:
            for msg in messages:
                ts = datetime.fromtimestamp(msg.timestamp).strftime('%H:%M')
                color = Colors.GREEN if msg.role == 'model' else Colors.BLUE
                cprint(f"  [{ts}] {msg.role.upper()}:", color, bold=True)
                print(f"    {msg.content}\n")

        print("\n[n] 下一页, [p] 上一页, [b] 返回")
        choice = get_user_input()
        if choice == 'b': return
        elif choice == 'n' or choice == 'next':
            if offset + page_size < total_messages:
                offset += page_size
            else:
                cprint("已到达消息末尾。", Colors.YELLOW)
                await asyncio.sleep(1)
        elif choice == 'p' or choice == 'prev':
            if offset - page_size >= 0:
                offset -= page_size
            else:
                cprint("已在第一页。", Colors.YELLOW)
                await asyncio.sleep(1)

async def view_community_list_menu(breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > 社区分享"
    while True:
        async with AsyncSessionLocal() as session:
            items = (await session.execute(select(SharedContent).order_by(SharedContent.created_at.desc()))).scalars().all()
        print_header("社区分享列表", breadcrumbs)
        item_rows = [(item.id, item.data_type, item.name, item.user_id[:8] + '...', item.downloads) for item in items]
        print_table(["ID", "类型", "名称", "作者 ID", "下载数"], item_rows)
        print("\n[b] 返回上一级")
        choice = get_user_input("请输入 ID 查看详情或 [b] > ")
        if choice == 'b': return

async def view_task_list_menu(breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > 后台任务"
    while True:
        async with AsyncSessionLocal() as session:
            items = (await session.execute(select(Task).order_by(Task.updated_at.desc()).limit(20))).scalars().all()
        print_header("后台任务列表 (最近20条)", breadcrumbs)
        
        def format_status(status):
            if status == 'success': return f"{Colors.GREEN}{status}{Colors.ENDC}"
            if status == 'failed': return f"{Colors.RED}{status}{Colors.ENDC}"
            if status == 'processing': return f"{Colors.BLUE}{status}{Colors.ENDC}"
            return status

        item_rows = [(
            item.id[:8],
            item.user_id[:8] + '...',
            item.task_type,
            format_status(item.status),
            datetime.fromtimestamp(item.updated_at).strftime('%Y-%m-%d %H:%M')
        ) for item in items]
        print_table(["任务 ID", "用户 ID", "类型", "状态", "更新时间"], item_rows)
        print("\n[b] 返回上一级")
        choice = get_user_input("请输入任务 ID 的前8位查看详情或 [b] > ")
        if choice == 'b': return
        
        selected_item = next((item for item in items if item.id.startswith(choice)), None)
        if selected_item:
            view_task_detail(selected_item, breadcrumbs)
        else:
            cprint("无效 ID。", Colors.RED)
            await asyncio.sleep(1)

def view_task_detail(item: Task, breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > {item.id[:8]}..."
    print_header(f"任务详情: {item.id[:8]}...", breadcrumbs)
    details = item.__dict__
    details.pop('_sa_instance_state', None)
    for key, value in details.items():
        if key.endswith('_at') and value:
            value = datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value, ensure_ascii=False, indent=2)
        
        key_str = f"  {key.ljust(15)}:"
        value_str = str(value).replace('\n', '\n' + ' ' * 19)
        print(f"{Colors.CYAN}{key_str}{Colors.ENDC} {value_str}")
    get_user_input("\n按任意键返回列表...")


async def view_tools_menu(breadcrumbs: str = "工具与修复"):
    breadcrumbs = "工具与修复"
    while True:
        print_header("数据工具与修复", breadcrumbs)
        cprint("--- 批量编辑与同步 ---", Colors.YELLOW)
        print("[1] 对某一类型的所有私有项目进行操作")
        print("[2] 同步某一类型所有项目的字段")
        
        cprint("\n--- 高级修复工具 ---", Colors.RED)
        print(f"[3] {Colors.RED}{Colors.BOLD}深度结构扫描与修复 (推荐){Colors.ENDC}")

        print("\n[b] 返回主菜单")

        choice = get_user_input()
        if choice == '1': await view_bulk_action_type_selection()
        elif choice == '2': await tool_sync_fields_by_type()
        elif choice == '3': await tool_data_integrity_scanner()
        elif choice == 'b': return

async def tool_sync_fields_by_type():
    breadcrumbs = "工具 > 字段同步"
    async with AsyncSessionLocal() as session:
        stmt = select(ContentItem.data_type, func.count(ContentItem.id)).group_by(ContentItem.data_type)
        all_types = (await session.execute(stmt)).all()

    while True:
        print_header("同步字段 - 选择类型", breadcrumbs)
        if not all_types:
            cprint("数据库中没有任何内容项。", Colors.YELLOW)
            get_user_input("\n按任意键返回...")
            return
        
        cprint("请选择要进行字段同步的内容类型：", Colors.GREEN)
        for i, (data_type, count) in enumerate(all_types, 1):
            print(f"[{i}] {data_type} {Colors.GREY}(共 {count} 个项目){Colors.ENDC}")
        print("\n[b] 返回上一级")

        choice = get_user_input()
        if choice == 'b': return
        try:
            await execute_field_sync(all_types[int(choice) - 1][0])
        except (ValueError, IndexError):
            cprint("无效输入。", Colors.RED)
            await asyncio.sleep(1)

async def execute_field_sync(data_type: str):
    print_header(f"同步字段: {data_type}", f"工具 > 字段同步 > {data_type}")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            items = (await session.execute(select(ContentItem).where(ContentItem.data_type == data_type))).scalars().all()
            if len(items) < 2:
                cprint(f"类型 '{data_type}' 的项目不足两个，无需同步。", Colors.GREEN)
            else:
                all_fields = set().union(*(item.data.keys() for item in items))
                cprint(f"检测到类型 '{data_type}' 的所有字段并集为:", Colors.GREEN)
                print(f"  {', '.join(sorted(list(all_fields)))}")
                
                items_to_update, preview_changes = [], []
                for item in items:
                    missing_fields = sorted(list(all_fields - set(item.data.keys())))
                    if missing_fields:
                        new_data = copy.deepcopy(item.data)
                        for field in missing_fields:
                            new_data[field] = [] if any(k in field for k in ["list", "worlds", "tags", "entries", "rules"]) else ""
                        items_to_update.append((item, new_data))
                        preview_changes.append(f"  - 文件 '{item.filename}': 将添加缺失字段 {Colors.GREEN}{', '.join(missing_fields)}{Colors.ENDC}")
                
                if not items_to_update:
                    cprint("\n无需修复，所有项目字段结构一致。", Colors.GREEN)
                else:
                    cprint("\n--- 即将进行的变更 (预览) ---", Colors.YELLOW, bold=True)
                    for change in preview_changes[:10]: print(change)
                    if len(preview_changes) > 10: print(f"  ...等共 {len(preview_changes)} 项变更。")
                    if get_confirmation(f"共检测到 {len(items_to_update)} 个 '{data_type}' 项目需要补全字段。"):
                        for item, new_data in items_to_update: item.data = new_data
                        await session.commit()
                        cprint(f"\n操作完成！已成功为 {len(items_to_update)} 个项目同步了字段。", Colors.GREEN, bold=True)
                    else:
                        cprint("\n操作已取消。", Colors.YELLOW)
                        await session.rollback()
    get_user_input("\n按任意键返回...")

async def view_bulk_action_type_selection():
    breadcrumbs = "工具 > 批量编辑"
    while True:
        async with AsyncSessionLocal() as session:
            stmt = select(ContentItem.data_type, func.count(ContentItem.id)).where(ContentItem.owner_id != None).group_by(ContentItem.data_type)
            private_types = (await session.execute(stmt)).all()
        
        print_header("批量编辑 - 选择类型", breadcrumbs)
        if not private_types:
            cprint("没有可编辑的私有内容类型。", Colors.YELLOW)
            get_user_input("\n按任意键返回...")
            return
            
        cprint("请选择要进行批量操作的内容类型：", Colors.GREEN)
        for i, (data_type, count) in enumerate(private_types, 1):
            print(f"[{i}] {data_type} {Colors.GREY}(共 {count} 个项目){Colors.ENDC}")
        print("\n[b] 返回上一级")
        
        choice = get_user_input()
        if choice == 'b': return
        try:
            await view_bulk_action_menu(private_types[int(choice) - 1][0], breadcrumbs)
        except (ValueError, IndexError):
            cprint("无效输入。", Colors.RED)
            await asyncio.sleep(1)

async def view_bulk_action_menu(data_type: str, breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > {data_type.capitalize()}"
    while True:
        print_header(f"批量编辑: {data_type.capitalize()}", breadcrumbs)
        cprint(f"您将对所有私有 {data_type} 项目进行操作。请选择具体动作：", Colors.GREEN)
        print("[1] 增加新字段 (Add new field)")
        print("[2] 删除一个字段 (Delete a field)")
        print("[3] 重命名一个字段 (Rename a field)")
        print("\n[b] 返回上一级")
        
        choice = get_user_input()
        if choice == '1': await tool_bulk_add_field(data_type)
        elif choice == '2': await tool_bulk_delete_field(data_type)
        elif choice == '3': await tool_bulk_rename_field(data_type)
        elif choice == 'b': return

async def tool_bulk_add_field(data_type: str):
    field_name = get_user_input("请输入要增加的字段名称 (例如: tags) > ")
    if not field_name: return
    default_value_str = get_user_input("请输入该字段的默认值 (JSON格式, 例如: [] 或 \"默认值\") > ")
    try:
        default_value = json.loads(default_value_str)
    except json.JSONDecodeError:
        cprint("错误: 输入的默认值不是有效的 JSON 格式。", Colors.RED)
        await asyncio.sleep(2)
        return

    async with AsyncSessionLocal() as session:
        async with session.begin():
            items = (await session.execute(select(ContentItem).where(ContentItem.data_type == data_type, ContentItem.owner_id != None))).scalars().all()
            items_to_update = [item for item in items if field_name not in item.data]
            if not items_to_update:
                cprint(f"\n无需操作，所有项目均已包含 '{field_name}' 字段。", Colors.GREEN)
            else:
                cprint("\n--- 即将进行的变更 (预览) ---", Colors.YELLOW, bold=True)
                for item in items_to_update[:5]: print(f"  - 文件 '{item.filename}': 将添加字段 '{Colors.GREEN}{field_name}{Colors.ENDC}'")
                if len(items_to_update) > 5: print(f"  ...等共 {len(items_to_update)} 项变更。")
                if get_confirmation(f"为 {len(items_to_update)} 个私有 {data_type} 添加字段 '{field_name}'。"):
                    for item in items_to_update:
                        new_data = copy.deepcopy(item.data)
                        new_data[field_name] = default_value
                        item.data = new_data
                    await session.commit()
                    cprint(f"\n操作完成！", Colors.GREEN, bold=True)
                else:
                    cprint("\n操作已取消。", Colors.YELLOW)
                    await session.rollback()
    get_user_input("\n按任意键返回...")

async def tool_bulk_delete_field(data_type: str):
    field_name = get_user_input("请输入要删除的字段名称 > ")
    if not field_name: return
    async with AsyncSessionLocal() as session:
        async with session.begin():
            items = (await session.execute(select(ContentItem).where(ContentItem.data_type == data_type, ContentItem.owner_id != None))).scalars().all()
            items_to_update = [item for item in items if field_name in item.data]
            if not items_to_update:
                cprint(f"\n无需操作，没有项目包含 '{field_name}' 字段。", Colors.GREEN)
            else:
                cprint("\n--- 即将进行的变更 (预览) ---", Colors.YELLOW, bold=True)
                for item in items_to_update[:5]: print(f"  - 文件 '{item.filename}': 将删除字段 '{Colors.RED}{field_name}{Colors.ENDC}'")
                if len(items_to_update) > 5: print(f"  ...等共 {len(items_to_update)} 项变更。")
                if get_confirmation(f"从 {len(items_to_update)} 个私有 {data_type} 中删除字段 '{field_name}'。此操作无法恢复！"):
                    for item in items_to_update:
                        new_data = copy.deepcopy(item.data)
                        del new_data[field_name]
                        item.data = new_data
                    await session.commit()
                    cprint(f"\n操作完成！", Colors.GREEN, bold=True)
                else:
                    cprint("\n操作已取消。", Colors.YELLOW)
                    await session.rollback()
    get_user_input("\n按任意键返回...")

async def tool_bulk_rename_field(data_type: str):
    old_name, new_name = get_user_input("请输入要重命名的旧字段名称 > "), None
    if old_name: new_name = get_user_input(f"请输入 '{old_name}' 的新名称 > ")
    if not old_name or not new_name: return
    async with AsyncSessionLocal() as session:
        async with session.begin():
            items = (await session.execute(select(ContentItem).where(ContentItem.data_type == data_type, ContentItem.owner_id != None))).scalars().all()
            items_to_update = [item for item in items if old_name in item.data]
            if not items_to_update:
                cprint(f"\n无需操作，没有项目包含 '{old_name}' 字段。", Colors.GREEN)
            else:
                cprint("\n--- 即将进行的变更 (预览) ---", Colors.YELLOW, bold=True)
                for item in items_to_update[:5]: print(f"  - 文件 '{item.filename}': 字段 '{Colors.RED}{old_name}{Colors.ENDC}' -> '{Colors.GREEN}{new_name}{Colors.ENDC}'")
                if len(items_to_update) > 5: print(f"  ...等共 {len(items_to_update)} 项变更。")
                if get_confirmation(f"在 {len(items_to_update)} 个私有 {data_type} 中将字段 '{old_name}' 重命名为 '{new_name}'。"):
                    for item in items_to_update:
                        new_data = copy.deepcopy(item.data)
                        new_data[new_name] = new_data.pop(old_name)
                        item.data = new_data
                    await session.commit()
                    cprint(f"\n操作完成！", Colors.GREEN, bold=True)
                else:
                    cprint("\n操作已取消。", Colors.YELLOW)
                    await session.rollback()
    get_user_input("\n按任意键返回...")

async def tool_data_integrity_scanner():
    breadcrumbs = "工具 > 完整性扫描"
    print_header("数据完整性扫描", breadcrumbs)
    cprint("正在扫描所有内容项，请稍候...", Colors.YELLOW)
    
    async with AsyncSessionLocal() as session:
        items = (await session.execute(select(ContentItem))).scalars().all()
    
    invalid_items = [{'item': item, 'errors': errors} for item in items if (errors := validate_content_item(item))]
    
    cprint(f"扫描完成！共检查 {len(items)} 个项目，发现 {len(invalid_items)} 个有问题的项目。", Colors.GREEN if not invalid_items else Colors.RED, bold=True)
    
    if not invalid_items:
        get_user_input("\n按任意键返回...")
        return

    while True:
        print("\n--- 问题项目列表 ---")
        for i, issue in enumerate(invalid_items, 1):
            owner = "公共" if issue['item'].owner_id is None else f"用户:{issue['item'].owner_id[:8]}..."
            print(f"[{i}] {Colors.RED}[{issue['item'].data_type}]{Colors.ENDC} {issue['item'].filename} {Colors.GREY}({owner}){Colors.ENDC}")
            for error in issue['errors']:
                print(f"    - {Colors.YELLOW}{error}{Colors.ENDC}")
        
        print("\n[b] 返回上一级")
        choice = get_user_input("请输入序号处理，或 [b] 返回 > ")
        if choice == 'b': return
        try:
            index = int(choice) - 1
            if 0 <= index < len(invalid_items):
                await handle_invalid_item_actions(invalid_items[index]['item'], invalid_items[index]['errors'], breadcrumbs)
                await tool_data_integrity_scanner()
                return 
        except (ValueError, IndexError):
            cprint("无效输入。", Colors.RED)
            await asyncio.sleep(1)

def validate_content_item(item: ContentItem) -> List[str]:
    errors = []
    if not isinstance(item.data, dict):
        errors.append("主数据不是一个有效的JSON对象（字典）。")
        return errors

    if not item.data.get('name', '').strip() and not item.data.get('displayName', '').strip():
        errors.append("缺少 'name' 或 'displayName' 字段。")
    
    if item.data_type == 'world_info':
        entries = item.data.get('entries')
        if entries is None:
            errors.append("'entries' 字段不存在。")
        elif not isinstance(entries, list):
            if isinstance(entries, dict):
                 errors.append(f"'entries' 字段是对象而非列表 (SillyTavern格式)。")
            else:
                 errors.append(f"'entries' 字段类型错误 (应为列表, 实为 {type(entries).__name__})。")
        elif any(not isinstance(e, dict) for e in entries):
            errors.append("'entries' 列表中包含非对象（字典）格式的条目。")
        else:
            for i, entry in enumerate(entries):
                if 'name' not in entry and 'comment' not in entry:
                    errors.append(f"'entries' 列表中的第 {i+1} 个条目缺少 'name' 或 'comment' 字段。")
                    break 
    
    return errors

def _fix_item_names(item_data: Dict, filename: str) -> Dict | None:
    new_data = copy.deepcopy(item_data)
    name, display_name = new_data.get('name', '').strip(), new_data.get('displayName', '').strip()
    changed = False
    if not name and display_name: new_data['name'], changed = display_name, True
    elif not display_name and name: new_data['displayName'], changed = name, True
    elif not name and not display_name: new_data['name'], new_data['displayName'], changed = filename, filename, True
    return new_data if changed else None

def _fix_world_info_item_entries(item_data: Dict) -> Dict | None:
    new_data = copy.deepcopy(item_data)
    entries = new_data.get('entries')
    changed = False
    
    entries_list = []
    
    if entries is None:
        new_data['entries'] = []
        changed = True
    elif isinstance(entries, dict):
        entries_list = list(entries.values())
        changed = True
    elif isinstance(entries, list):
        entries_list = entries
    else:
        new_data['entries'] = []
        changed = True

    final_entries = []
    has_structural_change = any(not isinstance(e, dict) for e in entries_list)
    if has_structural_change:
        changed = True

    for entry in entries_list:
        if isinstance(entry, dict):
            normalized_entry = copy.deepcopy(entry)
            if 'comment' in normalized_entry and 'name' not in normalized_entry:
                normalized_entry['name'] = normalized_entry.pop('comment')
                changed = True
            if 'key' in normalized_entry and 'keywords' not in normalized_entry:
                normalized_entry['keywords'] = normalized_entry.pop('key')
                changed = True
            
            if 'name' not in normalized_entry: normalized_entry['name'] = '未命名条目'
            if 'keywords' not in normalized_entry: normalized_entry['keywords'] = []
            if 'content' not in normalized_entry: normalized_entry['content'] = ''
            
            final_entries.append(normalized_entry)
        else:
            final_entries.append({'keywords': [], 'content': str(entry), 'name': '转换的条目'})
            
    if changed:
        new_data['entries'] = final_entries

    return new_data if changed else None


async def handle_invalid_item_actions(item: ContentItem, errors: List[str], breadcrumbs: str):
    breadcrumbs = f"{breadcrumbs} > {item.filename}"
    while True:
        print_header(f"处理问题项目: {item.filename}", breadcrumbs)
        cprint("检测到以下问题：", Colors.YELLOW, bold=True)
        for error in errors: print(f"  - {error}")
        
        print("\n--- 可用操作 ---")
        print("[1] 查看项目详情")
        print("[2] 尝试自动修复")
        print(f"[{Colors.RED}3{Colors.ENDC}] {Colors.RED}永久删除此项目{Colors.ENDC}")
        print("\n[b] 返回问题列表")
        
        choice = get_user_input()
        if choice == 'b': return
        elif choice == '1': view_content_item_detail(item, breadcrumbs)
        elif choice == '2':
            if await _attempt_auto_fix_item(item.id): return
        elif choice == '3':
            if get_confirmation(f"您将永久删除项目 '{item.filename}' ({item.data_type})。"):
                async with AsyncSessionLocal() as session:
                    await session.execute(delete(ContentItem).where(ContentItem.id == item.id))
                    await session.commit()
                cprint(f"项目 '{item.filename}' 已删除。", Colors.GREEN)
                get_user_input()
                return

async def _attempt_auto_fix_item(item_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            item = await session.get(ContentItem, item_id)
            if not item:
                cprint("找不到项目。", Colors.RED)
                return False

            original_data = copy.deepcopy(item.data)
            temp_data = original_data
            
            if item.data_type == 'world_info':
                fixed_entries_data = _fix_world_info_item_entries(temp_data)
                if fixed_entries_data:
                    temp_data = fixed_entries_data
            
            fixed_names_data = _fix_item_names(temp_data, item.filename)
            if fixed_names_data:
                temp_data = fixed_names_data
            
            if temp_data == original_data:
                cprint("未找到可应用的自动修复。", Colors.YELLOW)
                success = False
            else:
                item.data = temp_data
                await session.commit()
                cprint("修复成功！数据已更新。", Colors.GREEN, bold=True)
                success = True
    get_user_input("按任意键继续...")
    return success

async def view_export_menu(breadcrumbs: str = "数据导出/诊断"):
    while True:
        print_header("数据导出/诊断", breadcrumbs)
        cprint("[1] 导出所有世界书 (原始JSON)", Colors.BLUE)
        print("\n[b] 返回主菜单")
        
        choice = get_user_input()
        if choice == '1': await tool_export_all_world_info()
        elif choice == 'b': return

async def tool_export_all_world_info():
    print_header("导出所有世界书", "导出 > 世界书")
    cprint("正在从数据库查询所有世界书...", Colors.YELLOW)
    async with AsyncSessionLocal() as session:
        stmt = select(ContentItem).where(ContentItem.data_type == 'world_info')
        items = (await session.execute(stmt)).scalars().all()
    
    export_data = [
        {
            "filename": item.filename,
            "owner_id": item.owner_id,
            "data": item.data
        }
        for item in items
    ]
    
    tools_dir = PROJECT_ROOT / "tools"
    tools_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_filename = f"world_info_export_{timestamp}.json"
    export_path = tools_dir / export_filename

    try:
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        cprint(f"\n成功导出 {len(items)} 个世界书！", Colors.GREEN, bold=True)
        print(f"文件已保存至:")
        cprint(f"  {export_path}", Colors.CYAN)
    except Exception as e:
        cprint(f"\n导出文件时发生错误: {e}", Colors.RED, bold=True)

    get_user_input("\n按任意键返回...")
    

async def main():
    try:
        await initialize_engine()
        cprint("数据库连接成功！\n", Colors.GREEN, bold=True)
        await view_main_menu()
    except FileNotFoundError as e:
        cprint(f"错误: {e}", Colors.RED, bold=True)
        print("请确保 'novel_bot/config.toml' 文件存在，并且数据库文件路径正确。")
    except ValueError as e:
        cprint(f"配置错误: {e}", Colors.RED, bold=True)
    except KeyboardInterrupt:
        print("\n再见！")
    except Exception as e:
        cprint(f"发生未捕获的严重错误: {e}", Colors.RED, bold=True)
        logging.error("详细错误信息:", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        cprint(f"\n发生了一个错误: {e}", Colors.RED)
    
    if getattr(sys, 'frozen', False) or os.name == 'nt':
        os.system('pause')