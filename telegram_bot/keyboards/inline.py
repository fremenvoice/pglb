from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram_bot.domain.menu_registry import menu_by_role

def get_menu_inline_keyboard_for_role(role: str, only_back: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    if not only_back:
        items = menu_by_role.get(role, [])
        for label, _ in items:
            buttons.append([InlineKeyboardButton(text=label, callback_data=f"menu:{label}")])
    if role in {"admin", "operator", "consultant"}:
        buttons.append([InlineKeyboardButton(text="🔁 На экран выбора роли", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_role_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Меню операторов", callback_data="admin_menu:operator")],
        [InlineKeyboardButton(text="Меню консультантов", callback_data="admin_menu:consultant")],
        [InlineKeyboardButton(text="Без роли", callback_data="admin_menu:none")],
        [InlineKeyboardButton(text="QR-сканер", callback_data="admin_menu:qr_scanner")]
    ])

def get_back_to_menu_keyboard(role: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data=f"back_to_menu:{role}")]
    ])
