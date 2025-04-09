from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from keyboards.operator import get_operator_main_keyboard
from keyboards.consultant import get_consultant_main_keyboard
from keyboards.admin import get_admin_role_choice_keyboard

# Обработчик для "Приступить к работе!"
async def start_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = get_user_role(update.effective_user.username)

    if role == "operator":
        # Переход в меню оператора
        text = "Вы выбрали меню оператора"
        keyboard = get_operator_main_keyboard()  # Создаём меню оператора
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    elif role == "consultant":
        # Переход в меню консультанта
        text = "Вы выбрали меню консультанта"
        keyboard = get_consultant_main_keyboard()  # Создаём меню консультанта
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    elif role == "admin" or role == "creator":
        # Переход в меню выбора роли
        text = "Выберите роль для меню"
        keyboard = get_admin_role_choice_keyboard()  # Меню для админа/создателя
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)

# Обработчик для кнопки "🔁 На экран приветствия"
async def back_to_roles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = get_user_role(update.effective_user.username)
    if role == "admin" or role == "creator":
        text = "Выберите роль для меню"
        keyboard = get_admin_role_choice_keyboard()  # Меню для админа/создателя
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
