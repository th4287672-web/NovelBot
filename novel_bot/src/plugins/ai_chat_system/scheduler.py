# novel_bot/src/plugins/ai_chat_system/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import logger
from .services.archival_service import data_conduit_instance

# 创建一个原生的 AsyncIOScheduler 实例
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

async def perform_periodic_synchronization():
    if data_conduit_instance:
        await data_conduit_instance.synchronize_repository()
    else:
        logger.warning("Scheduler: DataConduit instance not found, skipping synchronization job.")

scheduler.add_job(
    perform_periodic_synchronization,
    "interval",
    hours=6,
    id="periodic_data_sync",
    misfire_grace_time=3600
)

logger.info("Scheduler job defined: periodic data synchronization every 6 hours.")
# 注意：scheduler.start() 会在 main.py 的 startup 事件中被调用