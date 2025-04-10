from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram_bot.domain.menu_registry import menu_by_role

def get_menu_inline_keyboard_for_role(role: str) -> InlineKeyboardMarkup:
    items = menu_by_role.get(role, [])
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"menu:{label}")]
        for label, _ in items
    ]
    if role in {"operator", "consultant", "admin"}:
        buttons.append([InlineKeyboardButton(text="🔁 На экран выбора роли", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_role_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Меню операторов", callback_data="admin_menu:operator")],
        [InlineKeyboardButton(text="Меню консультантов", callback_data="admin_menu:consultant")],
        [InlineKeyboardButton(text="Без роли", callback_data="admin_menu:none")]
    ])
