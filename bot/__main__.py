import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.db.database import Database
from bot.db.repositories import Repository
from bot.handlers import register_handlers
from bot.services.admin import AdminService
from bot.services.birthday import BirthdayService
from bot.services.greeting import GreetingService
from bot.services.scheduler import SchedulerService

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    db = Database(settings.db_path)
    await db.connect()

    repo = Repository(db)
    admin_service = AdminService(repo, settings.bot_owner_id)
    birthday_service = BirthdayService(repo)
    greeting_service = GreetingService(bot)
    scheduler_service = SchedulerService(repo, greeting_service)

    dp = Dispatcher()
    dp["repo"] = repo
    dp["admin_service"] = admin_service
    dp["birthday_service"] = birthday_service
    dp["greeting_service"] = greeting_service
    dp["scheduler_service"] = scheduler_service

    register_handlers(dp)

    @dp.startup()
    async def on_startup() -> None:
        logger.info("Starting scheduler...")
        await scheduler_service.start()
        me = await bot.get_me()
        logger.info("Bot started: @%s", me.username)

    @dp.shutdown()
    async def on_shutdown() -> None:
        logger.info("Shutting down scheduler...")
        scheduler_service.shutdown()
        logger.info("Closing database...")
        await db.disconnect()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
