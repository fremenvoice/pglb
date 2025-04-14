import logging
import os

from aiogram import Router, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from telegram_bot.services.access_control import get_user_info
from telegram_bot.services.text_service import get_text_block, render_welcome
from telegram_bot.keyboards.inline import (
    get_admin_role_choice_keyboard
)

# Импорт обработчика меню
from telegram_bot.handlers.menu import back_to_main_menu as handle_back_to_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "/start")
async def start_handler(message: Message):
    user = message.from_user
    username = user.username

    logger.info(f"👤 Старт взаимодействия: @{username}")

    info = get_user_info(username)

    if not info or not info.get("is_active") or not info.get("roles"):
        logger.warning(f"🚫 Неавторизованный пользователь: @{username}")
        text = get_text_block("about_park.md")
        await message.answer(text)
        return

    full_name = info["full_name"]
    roles = info["roles"]
    primary_role = roles[0]

    logger.info(f"✅ Авторизован: @{username} | Роли: {roles}")

    # Отправка логотипа
    logo_path = os.path.join(os.path.dirname(__file__), "..", "domain", "img", "logo.png")
    photo = FSInputFile(logo_path)
    await message.answer_photo(photo)

    # Приветствие + кнопка
    welcome_text = render_welcome(full_name, primary_role)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Приступить к работе", callback_data="start_work")]
    ])
    await message.answer(welcome_text, reply_markup=keyboard)


@router.callback_query(F.data == "start_work")
async def handle_start_work(callback: CallbackQuery, state: FSMContext):
    user = callback.from_user
    username = user.username
    info = get_user_info(username)

    if not info or not info.get("roles"):
        await callback.message.edit_text("🚫 Роль не определена.")
        return

    roles = info["roles"]
    primary_role = roles[0]
    full_name = info["full_name"]

    logger.info(f"⚙️ @{username} нажал 'Приступить к работе'")

    if primary_role == "admin":
        # Для админов — редактируем сообщение с выбором меню
        text = render_welcome(full_name, primary_role)
        kb = get_admin_role_choice_keyboard()
        await callback.message.edit_text(text, reply_markup=kb)
    else:
        # Оператор / консультант — передаём в menu.py
        await callback.message.edit_reply_markup()  # удалим кнопку
        await callback.bot.send_chat_action(callback.message.chat.id, "typing")

        # Вызываем обработчик возврата в главное меню роли
        await handle_back_to_main_menu(
            callback=CallbackQuery(
                id=callback.id,
                from_user=callback.from_user,
                chat_instance=callback.chat_instance,
                message=callback.message,
                data=f"back_to_menu:{primary_role}"
            ),
            state=state
        )

    await callback.answer()
