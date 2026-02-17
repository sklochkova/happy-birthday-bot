from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class OwnerAuthMiddleware(BaseMiddleware):
    """Blocks non-owner users. Attach to the owner-only router."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        admin_service = data["admin_service"]
        user = data.get("event_from_user")
        if not user or not admin_service.is_owner(user.id):
            if isinstance(event, Message):
                await event.answer("⛔ This command is available to the bot owner only.")
            return None
        return await handler(event, data)
