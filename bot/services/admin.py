from __future__ import annotations

from typing import Any

from bot.db.repositories import Repository


class AdminService:
    def __init__(self, repo: Repository, owner_id: int) -> None:
        self._repo = repo
        self._owner_id = owner_id

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
            return await self._repo.get_all_channels()
        return await self._repo.get_admin_channels(user_id)
