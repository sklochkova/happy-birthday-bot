from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot

from bot.db.repositories import Repository

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, repo: Repository, owner_id: int, bot: Bot) -> None:
        self._repo = repo
        self._owner_id = owner_id
        self._bot = bot

    def is_owner(self, user_id: int) -> bool:
        return user_id == self._owner_id

    async def is_admin(self, channel_id: int, user_id: int) -> bool:
        if self.is_owner(user_id):
            return True
        return await self._repo.is_admin(channel_id, user_id)

    async def grant_admin(
        self, channel_id: int, user_id: int, granted_by: int
    ) -> None:
        await self._repo.add_admin(channel_id, user_id, granted_by)

    async def revoke_admin(self, channel_id: int, user_id: int) -> bool:
        return await self._repo.remove_admin(channel_id, user_id)

    async def get_admin_channels(self, user_id: int) -> list[dict[str, Any]]:
        if self.is_owner(user_id):
            channels = await self._repo.get_all_channels()
        else:
            channels = await self._repo.get_admin_channels(user_id)

        # Filter out channels where the bot is no longer a member
        active = []
        for ch in channels:
            try:
                await self._bot.get_chat(ch["id"])
                active.append(ch)
            except Exception:
                logger.info("Removing stale channel %d from DB", ch["id"])
                await self._repo.remove_channel(ch["id"])
        return active
