# telegram_bot/handlers/admin_menu.py
import logging
import os
import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from telegram_bot.services.access_control import get_user_info
from telegram_bot.services.text_service import render_welcome
from telegram_bot.keyboards.inline import get_admin_role_choice_keyboard
from telegram_bot.handlers.qr_scanner import send_qr_scanner

logger = logging.getLogger(__name__)
router = Router()


async def safe_delete_by_id(bot, chat_id: int, message_id: int):
    """
    Вспомогательная функция для асинхронного удаления сообщения по chat_id и message_id.
    """
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение {message_id}: {e}")


@router.callback_query(F.data == "admin_back")
async def return_to_role_selection(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    info = await get_user_info(username)

    if not info:
        await callback.answer("Ошибка авторизации.")
        return

    full_name = info["full_name"]
    primary_role = info["roles"][0]

    # Удаляем предыдущие сообщения фоновой задачей
    data = await state.get_data()
    for msg_id in data.get("active_message_ids", []):
        asyncio.create_task(safe_delete_by_id(callback.bot, callback.message.chat.id, msg_id))
    # Удаляем текущее сообщение
    asyncio.create_task(safe_delete_by_id(callback.bot, callback.message.chat.id, callback.message.message_id))

    # Отправляем логотип и welcome
    logo_path = os.path.join(os.path.dirname(__file__), "..", "domain", "img", "logo.png")
    await callback.message.answer_photo(FSInputFile(logo_path))

    welcome_text = render_welcome(full_name, primary_role)
    kb = get_admin_role_choice_keyboard()
    new_msg = await callback.message.answer(welcome_text, reply_markup=kb)

    await state.clear()
    await state.update_data(active_message_ids=[new_msg.message_id])
    await callback.answer()


@router.callback_query(F.data == "admin_menu:operator_rent")
async def admin_operator_rent_entry(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # Удаляем предыдущее сообщение
    for msg_id in data.get("active_message_ids", []):
        asyncio.create_task(safe_delete_by_id(callback.bot, callback.message.chat.id, msg_id))
    asyncio.create_task(safe_delete_by_id(callback.bot, callback.message.chat.id, callback.message.message_id))

    await state.update_data({
        "admin_subrole": "operator_rent",
        "scanning_role": "operator_rent"
    })

    await send_qr_scanner(callback.message, role="operator_rent")
    await callback.answer()
