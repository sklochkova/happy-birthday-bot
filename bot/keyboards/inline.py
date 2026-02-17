from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ChannelSelectCB(CallbackData, prefix="ch_sel"):
    channel_id: int


class AdminActionCB(CallbackData, prefix="adm_act"):
    action: str


def build_channel_select_kb(channels: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(
            text=ch["title"] or f"Chat {ch['id']}",
            callback_data=ChannelSelectCB(channel_id=ch["id"]),
        )
    builder.adjust(1)
    return builder.as_markup()


def build_admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    actions = [
        ("➕ Add birthday", "add_bd"),
        ("➖ Remove birthday", "rm_bd"),
        ("📋 List birthdays", "list_bd"),
        ("✏️ Edit user", "edit_user"),
        ("🕐 Set greeting time", "set_time"),
        ("🌍 Set timezone", "set_tz"),
        ("⚙️ Settings", "settings"),
        ("🔄 Switch channel", "switch_ch"),
    ]
    for text, action in actions:
        builder.button(text=text, callback_data=AdminActionCB(action=action))
    builder.adjust(2)
    return builder.as_markup()
