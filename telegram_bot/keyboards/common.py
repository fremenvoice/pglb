from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def back_to_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 В главное меню")]],
        resize_keyboard=True
    )

def back_to_welcome_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔁 На экран приветствия")]],
        resize_keyboard=True
    )
