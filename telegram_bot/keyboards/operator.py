from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from telegram_bot.domain.menu_registry import menu_by_role

def get_operator_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text=label)]
        for label, _ in menu_by_role["operator"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )
