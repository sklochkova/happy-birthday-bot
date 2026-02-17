from __future__ import annotations

from typing import Any

from bot.db.repositories import Repository


class ResolvedUser:
    """Result of resolving a user from @username or numeric ID."""

    __slots__ = ("user_id", "first_name", "username", "display")

    def __init__(
        self,
        user_id: int,
        first_name: str | None = None,
        username: str | None = None,
        display: str | None = None,
    ) -> None:
        self.user_id = user_id
        self.first_name = first_name
        self.username = username
        self.display = display or first_name or str(user_id)


async def resolve_user(
    text: str, channel_id: int, repo: Repository
) -> ResolvedUser | None:
    """Resolve a user argument to a ResolvedUser.

    Accepts @username or numeric user ID.
    Returns None if the input is invalid or user not found for @username.
    """
    text = text.strip()
    if not text:
        return None

    if text.startswith("@"):
        username = text[1:]
        if not username:
            return None
        known = await repo.find_user_by_username(channel_id, username)
        if not known:
            return None
        return ResolvedUser(
            user_id=known["user_id"],
            first_name=known["first_name"],
            username=known["username"],
            display=f"@{username} (ID: {known['user_id']})",
        )

    if text.isdigit():
        uid = int(text)
        known = await repo.find_user_by_id(channel_id, uid)
        return ResolvedUser(
            user_id=uid,
            first_name=known["first_name"] if known else None,
            username=known["username"] if known else None,
        )

    return None
