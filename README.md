# Happy Birthday Telegram Bot

A Telegram bot that tracks birthdays of group participants and automatically posts congratulatory messages on schedule.

## Features

- **Multi-channel** — works in multiple groups simultaneously
- **Self-service** — users set their own birthday via `/setbirthday DD.MM`
- **Admin mode** — designated admins manage birthdays for others via DM
- **Scheduled greetings** — configurable time and timezone per channel
- **100 built-in greetings** — warm Russian-language templates, picked at random

## Quick Start

### 1. Prerequisites

- Python 3.11+
- A bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram user ID from [@userinfobot](https://t.me/userinfobot)

### 2. Install

```bash
git clone <your-repo-url>
cd happy-birthday-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN and BOT_OWNER_ID
```

### 4. Run

```bash
python -m bot
```

Add the bot to a Telegram group and send `/start`.

## Commands

### Group Commands

| Command | Description |
|---------|-------------|
| `/start` | Register the group and show help |
| `/setbirthday DD.MM` | Set your birthday |
| `/mybirthday` | Show your birthday |
| `/birthdays` | List all birthdays |
| `/removebirthday` | Remove your birthday |

### Admin Commands (via DM)

| Command | Description |
|---------|-------------|
| `/admin` | Open admin panel (select channel, manage birthdays & settings) |
| `/cancel` | Cancel current operation |

### Owner Commands (via DM)

| Command | Description |
|---------|-------------|
| `/grantadmin @user` or `USER_ID` | Grant admin role (select channel first via `/admin`) |
| `/revokeadmin @user` or `USER_ID` | Revoke admin role |

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | Yes | — | Bot API token |
| `BOT_OWNER_ID` | Yes | — | Your Telegram user ID |
| `DB_PATH` | No | `data/birthdays.db` | SQLite database path |
| `DEFAULT_TIMEZONE` | No | `UTC` | Default timezone for new channels |
| `DEFAULT_GREETING_TIME` | No | `09:00` | Default greeting time |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## Deployment

See [DEPLOY.md](DEPLOY.md) for a step-by-step guide to deploy on Google Cloud (free tier).

## Tech Stack

- **Python 3.11+** with asyncio
- **aiogram 3.x** — async Telegram bot framework
- **SQLite** via aiosqlite — zero-infrastructure database
- **APScheduler** — cron-like job scheduling with timezone support
