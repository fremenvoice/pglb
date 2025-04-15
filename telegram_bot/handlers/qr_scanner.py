import logging
import re
import cv2
import numpy as np
import asyncio
from pyzbar.pyzbar import decode
import aiohttp

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, PhotoSize, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery
)

from telegram_bot.services.access_control import get_user_info
from telegram_bot.app.config import QR_API_URL, QR_API_KEY

router = Router()
logger = logging.getLogger(__name__)


def extract_card_number(qr_data: str) -> str | None:
    match = re.search(r"f_persAcc=(\d+)", qr_data)
    return match.group(1) if match else None


async def fetch_card_info(card_number: str) -> dict | None:
    params = {"cardNumber": card_number, "apikey": QR_API_KEY}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(QR_API_URL, params=params) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return None


async def update_active_messages(message: Message, state: FSMContext, new_ids: list[int]):
    data = await state.get_data()
    delete_tasks = [
        message.bot.delete_message(message.chat.id, msg_id)
        for msg_id in data.get("active_message_ids", [])
    ]
    results = await asyncio.gather(*delete_tasks, return_exceptions=True)
    for msg_id, result in zip(data.get("active_message_ids", []), results):
        if isinstance(result, Exception):
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {result}")

    await state.update_data({
        **data,
        "active_message_ids": new_ids
    })


async def send_qr_scanner(message: Message, role: str, state: FSMContext):
    if role == "operator_rent":
        msg = await message.answer("🔍 Отправьте фото с QR-кодом карты. Сканирование начнётся автоматически.")
    else:
        kb = _qr_keyboard(role)
        msg = await message.answer("🔍 Отправьте фото с QR-кодом или выберите действие:", reply_markup=kb)

    await update_active_messages(message, state, [msg.message_id])


@router.message(F.photo)
async def global_qr_handler(message: Message, state: FSMContext):
    username = message.from_user.username
    info = get_user_info(username)
    if not info or not info["roles"]:
        logger.info(f"@{username} не авторизован, игнорируем фото.")
        return

    data = await state.get_data()
    user_role = info["roles"][0]
    scanning_role = data.get("scanning_role") or data.get("admin_subrole") or user_role
    data["scanning_role"] = scanning_role

    await update_active_messages(message, state, [])

    progress_msg = await message.answer("📸 Распознаю QR-код...")
    await state.update_data({
        **data,
        "active_message_ids": [progress_msg.message_id, message.message_id]
    })

    photo: PhotoSize = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    img_array = np.frombuffer(file_bytes.read(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    decoded = decode(img)

    await progress_msg.delete()

    if not decoded:
        await _send_qr_response(message, "❌ Не удалось распознать QR.", scanning_role, state=state)
        return

    qr_text = decoded[0].data.decode("utf-8")
    card_number = extract_card_number(qr_text)
    if not card_number:
        await _send_qr_response(message, "❌ В QR-коде нет f_persAcc.", scanning_role, state=state)
        return

    data_api = await fetch_card_info(card_number)
    if not data_api:
        await _send_qr_response(message, "❌ Ошибка при запросе к серверу.", scanning_role, state=state)
        return

    balance = data_api.get("Balance", "неизвестно")
    history = data_api.get("BalanceHistory", [])

    text = f"**Номер карты**: `{card_number}`\n**Баланс**: `{balance}`\n\n"
    if history:
        text += "**История операций**:\n"
        for h in history:
            sign = "+" if h.get("isReplenishment") else "-"
            val = h.get("value", "?")
            dt = h.get("date", "?")
            place = h.get("parkObjectName", "")
            text += f"{dt} {sign}{val} {place}\n"

    await _send_qr_response(message, text, scanning_role, state=state, markdown=True)


async def _send_qr_response(
    message: Message,
    text: str,
    role: str,
    *,
    state: FSMContext,
    markdown: bool = False
):
    kb = _qr_keyboard(role)
    msg = await message.answer(
        text,
        parse_mode="Markdown" if markdown else None,
        reply_markup=kb if kb else None
    )
    await update_active_messages(message, state, [msg.message_id])


@router.callback_query(F.data == "qr_again")
async def handle_qr_again(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    scanning_role = data.get("scanning_role")

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")

    kb = _qr_keyboard(scanning_role)
    msg = await callback.message.answer(
        "Пожалуйста, отправьте новое фото с QR-кодом.",
        reply_markup=kb if kb else None
    )
    data["active_message_ids"].append(msg.message_id)
    await state.update_data(data)
    await callback.answer()


def _qr_keyboard(scanning_role: str) -> InlineKeyboardMarkup | None:
    if scanning_role == "operator_rent":
        return None

    if scanning_role == "admin":
        back_callback = "admin_back"
        back_text = "Вернуться к выбору роли"
    else:
        back_callback = f"back_to_menu:{scanning_role}"
        back_text = "В главное меню"

    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Сканировать ещё", callback_data="qr_again"),
                          InlineKeyboardButton(text=back_text, callback_data=back_callback)]]
    )
