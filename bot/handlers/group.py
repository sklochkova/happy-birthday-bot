from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.config import settings
from bot.db.repositories import Repository
from bot.middlewares.auth import UserTrackingMiddleware
from bot.services.birthday import BirthdayService
from bot.utils.date_helpers import format_birthday, parse_birthday

router = Router(name="group")
router.message.filter(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
router.message.outer_middleware(UserTrackingMiddleware())


@router.message(Command("start"))
async def cmd_start(message: Message, repo: Repository) -> None:
    await repo.upsert_channel(
        chat_id=message.chat.id,
        title=message.chat.title,
        timezone=settings.default_timezone,
        greeting_time=settings.default_greeting_time,
    )
    await message.answer(
        "🎂 <b>Happy Birthday Bot</b>\n\n"
        "I track birthdays and send greetings!\n\n"
        "<b>Commands:</b>\n"
        "/setbirthday DD.MM — set your birthday\n"
        "/mybirthday — show your birthday\n"
        "/birthdays — list all birthdays\n"
        "/removebirthday — remove your birthday"
    )


@router.message(Command("setbirthday"))
async def cmd_set_birthday(
    message: Message,
    command: CommandObject,
    repo: Repository,
    birthday_service: BirthdayService,
) -> None:
    if not command.args:
        await message.answer("Usage: /setbirthday DD.MM (e.g. /setbirthday 15.06)")
        return

    try:
        day, month = parse_birthday(command.args)
    except ValueError as e:
        await message.answer(f"❌ {e}")
        return

    # Ensure channel is registered
    channel = await repo.get_channel(message.chat.id)
    if not channel:
        await repo.upsert_channel(
            message.chat.id,
            message.chat.title,
            settings.default_timezone,
            settings.default_greeting_time,
        )

    await birthday_service.set_birthday(
        channel_id=message.chat.id,
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        day=day,
        month=month,
        set_by=message.from_user.id,
    )
    await message.answer(f"✅ Your birthday is set to {format_birthday(day, month)}!")


@router.message(Command("mybirthday"))
async def cmd_my_birthday(
    message: Message, birthday_service: BirthdayService
) -> None:
    bd = await birthday_service.get_birthday(message.chat.id, message.from_user.id)
    if bd:
        await message.answer(
            f"🎂 Your birthday: {format_birthday(bd['birth_day'], bd['birth_month'])}"
        )
    else:
        await message.answer(
            "You haven't set your birthday yet. Use /setbirthday DD.MM"
        )


@router.message(Command("birthdays"))
async def cmd_birthdays(
    message: Message, birthday_service: BirthdayService
) -> None:
    birthdays = await birthday_service.list_birthdays(message.chat.id)
    if not birthdays:
        await message.answer("No birthdays registered yet. Be the first! /setbirthday DD.MM")
        return

    lines = ["🎂 <b>Birthdays in this chat:</b>\n"]
    for bd in birthdays:
        name = bd["first_name"] or "Unknown"
        username_part = f" (@{bd['username']})" if bd["username"] else ""
        date_str = format_birthday(bd["birth_day"], bd["birth_month"])
        lines.append(f"  {date_str} — {name}{username_part}")

    await message.answer("\n".join(lines))


@router.message(Command("removebirthday"))
async def cmd_remove_birthday(
    message: Message, birthday_service: BirthdayService
) -> None:
    removed = await birthday_service.remove_birthday(
        message.chat.id, message.from_user.id
    )
    if removed:
        await message.answer("✅ Your birthday has been removed.")
    else:
        await message.answer("You don't have a birthday set.")
