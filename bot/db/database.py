import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    id              INTEGER PRIMARY KEY,
    title           TEXT,
    timezone        TEXT    NOT NULL DEFAULT 'UTC',
    greeting_time   TEXT    NOT NULL DEFAULT '09:00',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS birthdays (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      INTEGER NOT NULL REFERENCES channels(id),
    user_id         INTEGER NOT NULL,
    username        TEXT,
    first_name      TEXT,
    birth_day       INTEGER NOT NULL,
    birth_month     INTEGER NOT NULL,
    set_by          INTEGER NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(channel_id, user_id)
);

CREATE TABLE IF NOT EXISTS admins (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      INTEGER NOT NULL REFERENCES channels(id),
    user_id         INTEGER NOT NULL,
    granted_by      INTEGER NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(channel_id, user_id)
);

CREATE TABLE IF NOT EXISTS known_users (
    user_id         INTEGER NOT NULL,
    channel_id      INTEGER NOT NULL,
    username        TEXT,
    first_name      TEXT,
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, channel_id)
);

CREATE TABLE IF NOT EXISTS greetings_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    greeted_on      TEXT    NOT NULL,
    UNIQUE(channel_id, user_id, greeted_on)
);
"""


class Database:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._migrate()
        logger.info("Database connected: %s", self._db_path)

    async def disconnect(self) -> None:
        if self._conn:
            await self._conn.close()
            logger.info("Database disconnected")

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected")
        return self._conn

    async def _migrate(self) -> None:
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()
