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
from bot.utils.user_resolver import resolve_user

router = Router(name="owner")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.message.middleware(OwnerAuthMiddleware())


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

    resolved = await resolve_user(command.args or "", channel_id, repo)
    if not resolved:
        await message.answer(
            "Usage: /grantadmin @username or /grantadmin USER_ID\n"
            "(Select a channel first via /admin)"
        )
        return

    await admin_service.grant_admin(channel_id, resolved.user_id, granted_by=message.from_user.id)
    await message.answer(
        f"✅ User {resolved.display} is now an admin for channel <b>{data.get('channel_title', channel_id)}</b>.",
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

    resolved = await resolve_user(command.args or "", channel_id, repo)
    if not resolved:
        await message.answer(
            "Usage: /revokeadmin @username or /revokeadmin USER_ID\n"
            "(Select a channel first via /admin)"
        )
        return

    removed = await admin_service.revoke_admin(channel_id, resolved.user_id)
    if removed:
        await message.answer(
            f"✅ Admin rights revoked for user {resolved.display}.",
            reply_markup=build_admin_menu_kb(),
        )
    else:
        await message.answer(
            f"User {resolved.display} is not an admin for this channel.",
            reply_markup=build_admin_menu_kb(),
        )
