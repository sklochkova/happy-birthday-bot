from __future__ import annotations

from typing import Any

from .database import Database


class Repository:
    def __init__(self, db: Database) -> None:
        self._db = db

    # ── Channels ──────────────────────────────────────────────────────

    async def upsert_channel(
        self, chat_id: int, title: str | None, timezone: str, greeting_time: str
    ) -> None:
        await self._db.conn.execute(
            """
            INSERT INTO channels (id, title, timezone, greeting_time)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET title = excluded.title
            """,
            (chat_id, title, timezone, greeting_time),
        )
        await self._db.conn.commit()

    async def get_channel(self, chat_id: int) -> dict[str, Any] | None:
        cursor = await self._db.conn.execute(
            "SELECT * FROM channels WHERE id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_all_channels(self) -> list[dict[str, Any]]:
        cursor = await self._db.conn.execute("SELECT * FROM channels")
        return [dict(r) for r in await cursor.fetchall()]

    async def update_channel_timezone(self, chat_id: int, timezone: str) -> None:
        await self._db.conn.execute(
            "UPDATE channels SET timezone = ? WHERE id = ?", (timezone, chat_id)
        )
        await self._db.conn.commit()

    async def update_channel_greeting_time(
        self, chat_id: int, greeting_time: str
    ) -> None:
        await self._db.conn.execute(
            "UPDATE channels SET greeting_time = ? WHERE id = ?",
            (greeting_time, chat_id),
        )
        await self._db.conn.commit()

    # ── Birthdays ─────────────────────────────────────────────────────

    async def set_birthday(
        self,
        channel_id: int,
        user_id: int,
        username: str | None,
        first_name: str | None,
        birth_day: int,
        birth_month: int,
        set_by: int,
    ) -> None:
        await self._db.conn.execute(
            """
            INSERT INTO birthdays (channel_id, user_id, username, first_name,
                                   birth_day, birth_month, set_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(channel_id, user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                birth_day = excluded.birth_day,
                birth_month = excluded.birth_month,
                set_by = excluded.set_by
            """,
            (channel_id, user_id, username, first_name, birth_day, birth_month, set_by),
        )
        await self._db.conn.commit()

    async def get_birthday(
        self, channel_id: int, user_id: int
    ) -> dict[str, Any] | None:
        cursor = await self._db.conn.execute(
            "SELECT * FROM birthdays WHERE channel_id = ? AND user_id = ?",
            (channel_id, user_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_birthdays_for_channel(
        self, channel_id: int
    ) -> list[dict[str, Any]]:
        cursor = await self._db.conn.execute(
            """
            SELECT * FROM birthdays
            WHERE channel_id = ?
            ORDER BY birth_month, birth_day
            """,
            (channel_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def get_birthdays_by_date(
        self, channel_id: int, day: int, month: int
    ) -> list[dict[str, Any]]:
        cursor = await self._db.conn.execute(
            """
            SELECT * FROM birthdays
            WHERE channel_id = ? AND birth_day = ? AND birth_month = ?
            """,
            (channel_id, day, month),
        )
        return [dict(r) for r in await cursor.fetchall()]

    async def remove_birthday(self, channel_id: int, user_id: int) -> bool:
        cursor = await self._db.conn.execute(
            "DELETE FROM birthdays WHERE channel_id = ? AND user_id = ?",
            (channel_id, user_id),
        )
        await self._db.conn.commit()
        return cursor.rowcount > 0

    # ── Admins ────────────────────────────────────────────────────────

    async def add_admin(
        self, channel_id: int, user_id: int, granted_by: int
    ) -> None:
        await self._db.conn.execute(
            """
            INSERT INTO admins (channel_id, user_id, granted_by)
            VALUES (?, ?, ?)
            ON CONFLICT(channel_id, user_id) DO NOTHING
            """,
            (channel_id, user_id, granted_by),
        )
        await self._db.conn.commit()

    async def remove_admin(self, channel_id: int, user_id: int) -> bool:
        cursor = await self._db.conn.execute(
            "DELETE FROM admins WHERE channel_id = ? AND user_id = ?",
            (channel_id, user_id),
        )
        await self._db.conn.commit()
        return cursor.rowcount > 0

    async def is_admin(self, channel_id: int, user_id: int) -> bool:
        cursor = await self._db.conn.execute(
            "SELECT 1 FROM admins WHERE channel_id = ? AND user_id = ?",
            (channel_id, user_id),
        )
        return await cursor.fetchone() is not None

    async def get_admin_channels(self, user_id: int) -> list[dict[str, Any]]:
        cursor = await self._db.conn.execute(
            """
            SELECT c.* FROM channels c
            JOIN admins a ON a.channel_id = c.id
            WHERE a.user_id = ?
            """,
            (user_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]

    # ── Greetings Log ─────────────────────────────────────────────────

    async def log_greeting(
        self, channel_id: int, user_id: int, date_str: str
    ) -> None:
        await self._db.conn.execute(
            """
            INSERT INTO greetings_log (channel_id, user_id, greeted_on)
            VALUES (?, ?, ?)
            ON CONFLICT(channel_id, user_id, greeted_on) DO NOTHING
            """,
            (channel_id, user_id, date_str),
        )
        await self._db.conn.commit()

    async def is_greeted_today(
        self, channel_id: int, user_id: int, date_str: str
    ) -> bool:
        cursor = await self._db.conn.execute(
            """
            SELECT 1 FROM greetings_log
            WHERE channel_id = ? AND user_id = ? AND greeted_on = ?
            """,
            (channel_id, user_id, date_str),
        )
        return await cursor.fetchone() is not None

    async def get_ungreeted_birthdays(
        self, channel_id: int, day: int, month: int, date_str: str
    ) -> list[dict[str, Any]]:
        cursor = await self._db.conn.execute(
            """
            SELECT b.* FROM birthdays b
            LEFT JOIN greetings_log g
                ON g.channel_id = b.channel_id
                AND g.user_id = b.user_id
                AND g.greeted_on = ?
            WHERE b.channel_id = ?
                AND b.birth_day = ?
                AND b.birth_month = ?
                AND g.id IS NULL
            """,
            (date_str, channel_id, day, month),
        )
        return [dict(r) for r in await cursor.fetchall()]
