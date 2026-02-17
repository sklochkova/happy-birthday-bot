import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    bot_owner_id: int
    db_path: Path
    default_timezone: str
    default_greeting_time: str
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        bot_token = os.environ.get("BOT_TOKEN", "")
        if not bot_token:
            raise ValueError("BOT_TOKEN environment variable is required")

        raw_owner = os.environ.get("BOT_OWNER_ID", "")
        if not raw_owner:
            raise ValueError("BOT_OWNER_ID environment variable is required")
        bot_owner_id = int(raw_owner)

        db_path = Path(os.getenv("DB_PATH", "data/birthdays.db"))
        default_timezone = os.getenv("DEFAULT_TIMEZONE", "UTC")
        default_greeting_time = os.getenv("DEFAULT_GREETING_TIME", "09:00")
        log_level = os.getenv("LOG_LEVEL", "INFO")

        return cls(
            bot_token=bot_token,
            bot_owner_id=bot_owner_id,
            db_path=db_path,
            default_timezone=default_timezone,
            default_greeting_time=default_greeting_time,
            log_level=log_level,
        )


settings = Settings.from_env()
