from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.db.repositories import Repository
from bot.keyboards.inline import build_admin_menu_kb
from bot.middlewares.auth import OwnerAuthMiddleware
from bot.services.admin import AdminService
from bot.states.admin_fsm import AdminFSM

router = Router(name="owner")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.message.middleware(OwnerAuthMiddleware())


async def _resolve_user(
    args: str | None, channel_id: int, repo: Repository
) -> tuple[int, str] | None:
    """Resolve a user argument to (user_id, display_name).

    Accepts @username or numeric user ID. Returns None if invalid.
    """
    text = (args or "").strip()
    if not text:
        return None

    if text.startswith("@"):
        username = text[1:]
        if not username:
            return None
        known = await repo.find_user_by_username(channel_id, username)
        if not known:
            return None
        return known["user_id"], f"@{username} (ID: {known['user_id']})"

    if text.isdigit():
        uid = int(text)
        return uid, str(uid)

    return None


@router.message(Command("grantadmin"), AdminFSM.main_menu)
async def cmd_grant_admin(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    admin_service: AdminService,
    repo: Repository,
) -> None:
    data = await state.get_data()
    channel_id = data.get("channel_id")
    if not channel_id:
        await message.answer("Please select a channel first using /admin.")
        return

    resolved = await _resolve_user(command.args, channel_id, repo)
    if not resolved:
        await message.answer(
            "Usage: /grantadmin @username or /grantadmin USER_ID\n"
            "(Select a channel first via /admin)"
        )
        return

    user_id, display = resolved
    await admin_service.grant_admin(channel_id, user_id, granted_by=message.from_user.id)
    await message.answer(
        f"✅ User {display} is now an admin for channel <b>{data.get('channel_title', channel_id)}</b>.",
        reply_markup=build_admin_menu_kb(),
    )


@router.message(Command("revokeadmin"), AdminFSM.main_menu)
async def cmd_revoke_admin(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    admin_service: AdminService,
    repo: Repository,
) -> None:
    data = await state.get_data()
    channel_id = data.get("channel_id")
    if not channel_id:
        await message.answer("Please select a channel first using /admin.")
        return

    resolved = await _resolve_user(command.args, channel_id, repo)
    if not resolved:
        await message.answer(
            "Usage: /revokeadmin @username or /revokeadmin USER_ID\n"
            "(Select a channel first via /admin)"
        )
        return

    user_id, display = resolved
    removed = await admin_service.revoke_admin(channel_id, user_id)
    if removed:
        await message.answer(
            f"✅ Admin rights revoked for user {display}.",
            reply_markup=build_admin_menu_kb(),
        )
    else:
        await message.answer(
            f"User {display} is not an admin for this channel.",
            reply_markup=build_admin_menu_kb(),
        )
