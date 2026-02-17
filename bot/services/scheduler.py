from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.db.repositories import Repository
from bot.services.greeting import GreetingService
from bot.utils.date_helpers import today_date_str, today_in_timezone

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, repo: Repository, greeting_service: GreetingService) -> None:
        self._scheduler = AsyncIOScheduler()
        self._repo = repo
        self._greeting = greeting_service

    async def start(self) -> None:
        channels = await self._repo.get_all_channels()
        for ch in channels:
            self._add_channel_job(ch["id"], ch["greeting_time"], ch["timezone"])
        self._scheduler.start()
        logger.info("Scheduler started with %d channel jobs", len(channels))

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")

    def update_channel_job(
        self, channel_id: int, greeting_time: str, timezone: str
    ) -> None:
        self._add_channel_job(channel_id, greeting_time, timezone)
        logger.info(
            "Updated job for channel %d: %s %s", channel_id, greeting_time, timezone
        )

    def remove_channel_job(self, channel_id: int) -> None:
        job_id = f"greet_{channel_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info("Removed job for channel %d", channel_id)

    def _add_channel_job(
        self, channel_id: int, greeting_time: str, timezone: str
    ) -> None:
        hour, minute = map(int, greeting_time.split(":"))
        self._scheduler.add_job(
            self._greet_channel,
            CronTrigger(hour=hour, minute=minute, timezone=timezone),
            id=f"greet_{channel_id}",
            args=[channel_id],
            replace_existing=True,
        )

    async def _greet_channel(self, channel_id: int) -> None:
        channel = await self._repo.get_channel(channel_id)
        if not channel:
            return

        tz = channel["timezone"]
        day, month = today_in_timezone(tz)
        date_str = today_date_str(tz)

        birthdays = await self._repo.get_ungreeted_birthdays(
            channel_id, day, month, date_str
        )

        for bd in birthdays:
            try:
                await self._greeting.send_greeting(
                    channel_id,
                    bd["user_id"],
                    bd["username"],
                    bd["first_name"],
                    bd["birth_day"],
                    bd["birth_month"],
                )
                await self._repo.log_greeting(channel_id, bd["user_id"], date_str)
            except Exception:
                logger.exception(
                    "Failed to send greeting in channel %d for user %d",
                    channel_id,
                    bd["user_id"],
                )

    async def check_missed_greetings(self) -> None:
        """Check all channels for today's ungreeted birthdays. Called on startup."""
        channels = await self._repo.get_all_channels()
        total_sent = 0

        for ch in channels:
            tz = ch["timezone"]
            day, month = today_in_timezone(tz)
            date_str = today_date_str(tz)

            ungreeted = await self._repo.get_ungreeted_birthdays(
                ch["id"], day, month, date_str
            )

            for bd in ungreeted:
                try:
                    await self._greeting.send_greeting(
                        ch["id"],
                        bd["user_id"],
                        bd["username"],
                        bd["first_name"],
                        bd["birth_day"],
                        bd["birth_month"],
                    )
                    await self._repo.log_greeting(ch["id"], bd["user_id"], date_str)
                    total_sent += 1
                except Exception:
                    logger.exception(
                        "Failed belated greeting in channel %d for user %d",
                        ch["id"],
                        bd["user_id"],
                    )

        if total_sent:
            logger.info("Sent %d belated greetings on startup", total_sent)
