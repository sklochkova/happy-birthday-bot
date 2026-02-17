from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message, TelegramObject

logger = logging.getLogger(__name__)


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


class UserTrackingMiddleware(BaseMiddleware):
    """Silently caches user info from group messages into known_users table."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.chat.type in (
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ):
            user = event.from_user
            if user and not user.is_bot:
                repo = data.get("repo")
                if repo:
                    try:
                        await repo.upsert_known_user(
                            user_id=user.id,
                            channel_id=event.chat.id,
                            username=user.username,
                            first_name=user.first_name,
                        )
                    except Exception:
                        logger.debug(
                            "Failed to track user %d in channel %d",
                            user.id,
                            event.chat.id,
                        )
        return await handler(event, data)
