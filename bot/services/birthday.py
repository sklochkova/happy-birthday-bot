from __future__ import annotations

from typing import Any

from bot.db.repositories import Repository
from bot.utils.date_helpers import today_in_timezone


class BirthdayService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    async def set_birthday(
        self,
        channel_id: int,
        user_id: int,
        username: str | None,
        first_name: str | None,
        day: int,
        month: int,
        set_by: int,
    ) -> None:
        await self._repo.set_birthday(
            channel_id, user_id, username, first_name, day, month, set_by
        )

    async def get_birthday(
        self, channel_id: int, user_id: int
    ) -> dict[str, Any] | None:
        return await self._repo.get_birthday(channel_id, user_id)

    async def list_birthdays(self, channel_id: int) -> list[dict[str, Any]]:
        return await self._repo.get_birthdays_for_channel(channel_id)

    async def remove_birthday(self, channel_id: int, user_id: int) -> bool:
        return await self._repo.remove_birthday(channel_id, user_id)

    async def get_todays_birthdays(
        self, channel_id: int, timezone: str
    ) -> list[dict[str, Any]]:
        day, month = today_in_timezone(timezone)
        return await self._repo.get_birthdays_by_date(channel_id, day, month)
