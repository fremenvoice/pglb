# telegram_bot/handlers/start.py
import asyncio
import logging
import os

from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.fsm.context import FSMContext

from telegram_bot.services.access_control import get_user_info
from telegram_bot.services.text_service import get_text_block, render_welcome
from telegram_bot.keyboards.inline import get_admin_role_choice_keyboard
from telegram_bot.handlers.qr_scanner import send_qr_scanner
from telegram_bot.handlers.menu import show_main_menu_for_role
from telegram_bot.core.states import ContextState

router = Router()
logger = logging.getLogger(__name__)


async def safe_delete_by_id(bot: Bot, chat_id: int, message_id: int):
    """
    Вспомогательная функция для асинхронного удаления сообщения по chat_id и message_id.
    """
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message_id}: {e}")


@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    username = message.from_user.username
    logger.info(f"👤 Старт взаимодействия: @{username}")
    info = await get_user_info(username)

    if not info or not info.get("is_active") or not info.get("roles"):
        logger.warning(f"🚫 Неавторизованный пользователь: @{username}")
        text = await get_text_block("about_park.md")
        await message.answer(text)
        return

    full_name = info["full_name"]
    primary_role = info["roles"][0]
    logger.info(f"✅ Авторизован: @{username} | Роли: {info['roles']}")

    await state.clear()

    logo = None
    try:
        from telegram_bot.services.image_cache import get_image
        logo = get_image("logo.png")
    except Exception:
        logger.warning("❌ Логотип logo.png не найден в кеше.")

    if logo:
        await message.answer_photo(logo)

    welcome_text = render_welcome(full_name, primary_role)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[ 
            [InlineKeyboardButton(text="🚀 Приступить к работе", callback_data="start_work")]
        ]
    )
    await message.answer(welcome_text, reply_markup=keyboard)


@router.callback_query(F.data == "start_work")
async def handle_start_work(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    info = await get_user_info(username)

    if not info or not info.get("roles"):
        await callback.message.edit_text("🚫 Роль не определена.")
        return

    full_name = info["full_name"]
    primary_role = info["roles"][0]
    logger.info(f"⚙️ @{username} нажал 'Приступить к работе'")

    # Вместо прямого удаления используем safe_delete_by_id через create_task
    asyncio.create_task(safe_delete_by_id(callback.message.bot, callback.message.chat.id, callback.message.message_id))

    if primary_role == "admin":
        await state.set_state(ContextState.admin_selected_role)
        text = render_welcome(full_name, primary_role)
        kb = get_admin_role_choice_keyboard()
        new_msg = await callback.message.answer(text, reply_markup=kb)
        await state.update_data({"active_message_ids": [new_msg.message_id]})

    elif primary_role == "operator_rent":
        await send_qr_scanner(callback.message, role="operator_rent", state=state)

    else:
        await asyncio.gather(
            callback.bot.send_chat_action(callback.message.chat.id, "typing"),
            show_main_menu_for_role(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                role=primary_role,
                state=state
            )
        )

    await callback.answer()
