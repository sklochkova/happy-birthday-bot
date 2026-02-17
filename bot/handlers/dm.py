from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.repositories import Repository
from bot.keyboards.inline import (
    AdminActionCB,
    ChannelSelectCB,
    build_admin_menu_kb,
    build_channel_select_kb,
)
from bot.services.admin import AdminService
from bot.services.birthday import BirthdayService
from bot.services.scheduler import SchedulerService
from bot.states.admin_fsm import AdminFSM
from bot.utils.date_helpers import format_birthday, parse_birthday

router = Router(name="dm_admin")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


# ── /admin — entry point ──────────────────────────────────────────────


@router.message(Command("admin"))
async def cmd_admin(
    message: Message, state: FSMContext, admin_service: AdminService
) -> None:
    channels = await admin_service.get_admin_channels(message.from_user.id)
    if not channels:
        await message.answer("You are not an admin of any channel.")
        return

    if len(channels) == 1:
        ch = channels[0]
        await state.update_data(channel_id=ch["id"], channel_title=ch["title"])
        await state.set_state(AdminFSM.main_menu)
        await message.answer(
            f"Managing: <b>{ch['title'] or ch['id']}</b>",
            reply_markup=build_admin_menu_kb(),
        )
    else:
        await state.set_state(AdminFSM.select_channel)
        await message.answer(
            "Select a channel to manage:",
            reply_markup=build_channel_select_kb(channels),
        )


@router.callback_query(ChannelSelectCB.filter(), AdminFSM.select_channel)
async def on_channel_selected(
    callback: CallbackQuery,
    callback_data: ChannelSelectCB,
    state: FSMContext,
    repo: Repository,
) -> None:
    channel = await repo.get_channel(callback_data.channel_id)
    title = channel["title"] if channel else str(callback_data.channel_id)
    await state.update_data(
        channel_id=callback_data.channel_id, channel_title=title
    )
    await state.set_state(AdminFSM.main_menu)
    await callback.message.edit_text(
        f"Managing: <b>{title}</b>",
        reply_markup=build_admin_menu_kb(),
    )
    await callback.answer()


# ── Admin menu actions ────────────────────────────────────────────────


@router.callback_query(AdminActionCB.filter(F.action == "switch_ch"), AdminFSM.main_menu)
async def on_switch_channel(
    callback: CallbackQuery, state: FSMContext, admin_service: AdminService
) -> None:
    channels = await admin_service.get_admin_channels(callback.from_user.id)
    if len(channels) <= 1:
        await callback.answer("You only have one channel.", show_alert=True)
        return
    await state.set_state(AdminFSM.select_channel)
    await callback.message.edit_text(
        "Select a channel to manage:",
        reply_markup=build_channel_select_kb(channels),
    )
    await callback.answer()


@router.callback_query(AdminActionCB.filter(F.action == "add_bd"), AdminFSM.main_menu)
async def on_add_birthday(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.add_birthday_user)
    await callback.message.edit_text(
        "Send me the user to set birthday for:\n\n"
        "• <b>@username</b> — if the user has sent a message in the group\n"
        "• <b>numeric user ID</b>\n"
        "• <b>forward a message</b> from that user"
    )
    await callback.answer()


@router.callback_query(AdminActionCB.filter(F.action == "rm_bd"), AdminFSM.main_menu)
async def on_remove_birthday(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.remove_birthday_user)
    await callback.message.edit_text(
        "Send me the user whose birthday you want to remove:\n\n"
        "• <b>@username</b>\n"
        "• <b>numeric user ID</b>"
    )
    await callback.answer()


@router.callback_query(AdminActionCB.filter(F.action == "list_bd"), AdminFSM.main_menu)
async def on_list_birthdays(
    callback: CallbackQuery,
    state: FSMContext,
    birthday_service: BirthdayService,
) -> None:
    data = await state.get_data()
    channel_id = data["channel_id"]
    birthdays = await birthday_service.list_birthdays(channel_id)

    if not birthdays:
        text = "No birthdays registered in this channel yet."
    else:
        lines = ["🎂 <b>Birthdays:</b>\n"]
        for bd in birthdays:
            name = bd["first_name"] or "Unknown"
            username_part = f" (@{bd['username']})" if bd["username"] else ""
            date_str = format_birthday(bd["birth_day"], bd["birth_month"])
            lines.append(f"  {date_str} — {name}{username_part} [ID: {bd['user_id']}]")
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=build_admin_menu_kb())
    await callback.answer()


@router.callback_query(AdminActionCB.filter(F.action == "set_time"), AdminFSM.main_menu)
async def on_set_time(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.set_time)
    await callback.message.edit_text(
        "Send me the greeting time in HH:MM format (24h, e.g. 09:00)."
    )
    await callback.answer()


@router.callback_query(AdminActionCB.filter(F.action == "set_tz"), AdminFSM.main_menu)
async def on_set_timezone(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.set_timezone)
    await callback.message.edit_text(
        "Send me the timezone in Region/City format (e.g. Europe/London, US/Eastern, Asia/Tokyo)."
    )
    await callback.answer()


# ── Add birthday flow ─────────────────────────────────────────────────


@router.message(AdminFSM.add_birthday_user)
async def on_add_birthday_user(
    message: Message, state: FSMContext, repo: Repository
) -> None:
    # Support forwarded messages to detect user ID
    if message.forward_from:
        user_id = message.forward_from.id
        first_name = message.forward_from.first_name
        username = message.forward_from.username
        await state.update_data(
            target_user_id=user_id,
            target_first_name=first_name,
            target_username=username,
        )
        await state.set_state(AdminFSM.add_birthday_date)
        name_display = first_name or str(user_id)
        await message.answer(
            f"Got it! Setting birthday for <b>{name_display}</b> (ID: {user_id}).\n"
            f"Now send the date in DD.MM format."
        )
        return

    # Forwarded message but user has privacy enabled — no user ID available
    if message.forward_date or message.forward_sender_name:
        await message.answer(
            "This user has privacy settings that hide their identity in forwarded messages.\n\n"
            "Please use <b>@username</b> or a <b>numeric user ID</b> instead."
        )
        return

    text = message.text.strip() if message.text else ""

    # Support @username lookup
    if text.startswith("@"):
        username = text[1:]
        if not username:
            await message.answer("Please send a valid @username.")
            return
        data = await state.get_data()
        channel_id = data["channel_id"]
        known = await repo.find_user_by_username(channel_id, username)
        if not known:
            await message.answer(
                f"User @{username} not found in the channel cache.\n"
                "The user must have sent at least one message in the group "
                "after the bot was added.\n\n"
                "You can also use a numeric user ID or forward a message from the user."
            )
            return
        await state.update_data(
            target_user_id=known["user_id"],
            target_first_name=known["first_name"],
            target_username=known["username"],
        )
        await state.set_state(AdminFSM.add_birthday_date)
        name_display = known["first_name"] or f"@{username}"
        await message.answer(
            f"Got it! Setting birthday for <b>{name_display}</b> (ID: {known['user_id']}).\n"
            f"Now send the date in DD.MM format."
        )
        return

    # Otherwise try to parse numeric ID
    if not text.isdigit():
        await message.answer(
            "Please send a @username, numeric user ID, or forward a message from the user."
        )
        return

    user_id = int(text)
    await state.update_data(
        target_user_id=user_id, target_first_name=None, target_username=None
    )
    await state.set_state(AdminFSM.add_birthday_date)
    await message.answer(f"Setting birthday for user ID {user_id}.\nNow send the date in DD.MM format.")


@router.message(AdminFSM.add_birthday_date)
async def on_add_birthday_date(
    message: Message,
    state: FSMContext,
    birthday_service: BirthdayService,
) -> None:
    text = message.text.strip() if message.text else ""
    try:
        day, month = parse_birthday(text)
    except ValueError as e:
        await message.answer(f"❌ {e}\nTry again (DD.MM):")
        return

    data = await state.get_data()
    channel_id = data["channel_id"]
    target_user_id = data["target_user_id"]

    await birthday_service.set_birthday(
        channel_id=channel_id,
        user_id=target_user_id,
        username=data.get("target_username"),
        first_name=data.get("target_first_name"),
        day=day,
        month=month,
        set_by=message.from_user.id,
    )

    await state.set_state(AdminFSM.main_menu)
    await message.answer(
        f"✅ Birthday set: user {target_user_id} → {format_birthday(day, month)}",
        reply_markup=build_admin_menu_kb(),
    )


# ── Remove birthday flow ─────────────────────────────────────────────


@router.message(AdminFSM.remove_birthday_user)
async def on_remove_birthday_user(
    message: Message,
    state: FSMContext,
    birthday_service: BirthdayService,
    repo: Repository,
) -> None:
    text = message.text.strip() if message.text else ""
    data = await state.get_data()
    channel_id = data["channel_id"]

    # Support @username lookup
    if text.startswith("@"):
        username = text[1:]
        if not username:
            await message.answer("Please send a valid @username.")
            return
        known = await repo.find_user_by_username(channel_id, username)
        if not known:
            await message.answer(
                f"User @{username} not found in the channel cache.\n"
                "Try using a numeric user ID instead."
            )
            return
        user_id = known["user_id"]
        display = f"@{username} (ID: {user_id})"
    elif text.isdigit():
        user_id = int(text)
        display = str(user_id)
    else:
        await message.answer(
            "Please send a @username or numeric user ID."
        )
        return

    removed = await birthday_service.remove_birthday(channel_id, user_id)

    await state.set_state(AdminFSM.main_menu)
    if removed:
        await message.answer(
            f"✅ Birthday removed for user {display}.",
            reply_markup=build_admin_menu_kb(),
        )
    else:
        await message.answer(
            f"No birthday found for user {display}.",
            reply_markup=build_admin_menu_kb(),
        )


# ── Set time flow ─────────────────────────────────────────────────────


@router.message(AdminFSM.set_time)
async def on_set_time_input(
    message: Message,
    state: FSMContext,
    repo: Repository,
    scheduler_service: SchedulerService,
) -> None:
    text = message.text.strip() if message.text else ""
    if not re.match(r"^\d{1,2}:\d{2}$", text):
        await message.answer("Please use HH:MM format (e.g. 09:00).")
        return

    hour, minute = map(int, text.split(":"))
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        await message.answer("Invalid time. Hours: 0-23, minutes: 0-59.")
        return

    greeting_time = f"{hour:02d}:{minute:02d}"
    data = await state.get_data()
    channel_id = data["channel_id"]

    await repo.update_channel_greeting_time(channel_id, greeting_time)

    # Update the scheduler job
    channel = await repo.get_channel(channel_id)
    scheduler_service.update_channel_job(
        channel_id, greeting_time, channel["timezone"]
    )

    await state.set_state(AdminFSM.main_menu)
    await message.answer(
        f"✅ Greeting time set to {greeting_time}.",
        reply_markup=build_admin_menu_kb(),
    )


# ── Set timezone flow ─────────────────────────────────────────────────


@router.message(AdminFSM.set_timezone)
async def on_set_timezone_input(
    message: Message,
    state: FSMContext,
    repo: Repository,
    scheduler_service: SchedulerService,
) -> None:
    text = message.text.strip() if message.text else ""

    # Validate timezone
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        ZoneInfo(text)
    except (ZoneInfoNotFoundError, KeyError):
        await message.answer(
            "❌ Unknown timezone. Use Region/City format (e.g. Europe/London, US/Eastern)."
        )
        return

    data = await state.get_data()
    channel_id = data["channel_id"]

    await repo.update_channel_timezone(channel_id, text)

    channel = await repo.get_channel(channel_id)
    scheduler_service.update_channel_job(
        channel_id, channel["greeting_time"], text
    )

    await state.set_state(AdminFSM.main_menu)
    await message.answer(
        f"✅ Timezone set to {text}.",
        reply_markup=build_admin_menu_kb(),
    )


# ── /cancel — exit any FSM state ──────────────────────────────────────


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Nothing to cancel.")
        return
    await state.clear()
    await message.answer("Cancelled. Use /admin to start again.")
