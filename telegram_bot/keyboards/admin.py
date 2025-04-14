from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_admin_role_selector() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Меню операторов")],
            [KeyboardButton(text="Меню консультантов")],
            [KeyboardButton(text="Без роли")]
        ],
        resize_keyboard=True
    )


def get_back_to_role_selector(is_admin: bool = False) -> ReplyKeyboardMarkup | None:
    if not is_admin:
        return None
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔁 На экран выбора роли")]],
        resize_keyboard=True
    )
