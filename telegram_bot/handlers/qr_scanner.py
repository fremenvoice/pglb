# telegram_bot/handlers/qr_scanner.py

import logging
import re
import requests
import cv2
import numpy as np
from pyzbar.pyzbar import decode

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    PhotoSize,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from telegram_bot.services.access_control import get_user_info

router = Router()
logger = logging.getLogger(__name__)

QR_API_URL = "http://10.0.0.4/Api/Card/GetBalanceAndHistory"
QR_API_KEY = "APIKEYGLOBAL"

def extract_card_number(qr_data: str) -> str|None:
    match = re.search(r"f_persAcc=(\d+)", qr_data)
    return match.group(1) if match else None

@router.message(F.photo)
async def global_qr_handler(message: Message, state: FSMContext):
    """
    Если user авторизован — обрабатываем QR.
    ДО этого удаляем текущее меню (active_message_ids) — чтобы «старый» пункт меню не висел.
    Если scanning_role=None => берем subrole (если админ выбрал operator/consultant) или user_role.
    В результате: после ответа, в chat остается только сообщения от сканирования.
    """
    username = message.from_user.username
    info = get_user_info(username)
    if not info or not info["roles"]:
        logger.info(f"@{username} не авторизован, игнорируем фото.")
        return

    data = await state.get_data()
    user_role = info["roles"][0]
    admin_subrole = data.get("admin_subrole")  # None / "operator" / "consultant"
    scanning_role = data.get("scanning_role")  # None / "operator" / "consultant" / "admin"

    # 1) Сносим текущее меню (если есть). Так не будет «хвостов».
    active_ids = data.get("active_message_ids", [])
    for msg_id in active_ids:
        try:
            await message.bot.delete_message(message.chat.id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

    # Очистим, потому что сейчас будет логика сканирования
    data["active_message_ids"] = []
    await state.update_data(data)

    # 2) Определяем scanning_role
    if not scanning_role:
        scanning_role = admin_subrole or user_role
        data["scanning_role"] = scanning_role
        await state.update_data(data)

    # 3) «Распознаю QR...»
    progress_msg = await message.answer("📸 Распознаю QR-код...")

    # Запомним ид
    active_ids = data["active_message_ids"]
    active_ids.append(progress_msg.message_id)
    active_ids.append(message.message_id)  # фото
    data["active_message_ids"] = active_ids
    await state.update_data(data)

    # 4) Скачиваем файл и пытаемся распознать
    photo: PhotoSize = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)

    img_array = np.frombuffer(file_bytes.read(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    decoded = decode(img)

    if not decoded:
        await progress_msg.delete()
        kb = _qr_keyboard(scanning_role)
        err_msg = await message.answer("❌ Не удалось распознать QR.", reply_markup=kb)
        data["active_message_ids"].append(err_msg.message_id)
        await state.update_data(data)
        return

    qr_text = decoded[0].data.decode("utf-8")
    card_number = extract_card_number(qr_text)
    if not card_number:
        await progress_msg.delete()
        kb = _qr_keyboard(scanning_role)
        e_msg = await message.answer("❌ В QR-коде нет f_persAcc.", reply_markup=kb)
        data["active_message_ids"].append(e_msg.message_id)
        await state.update_data(data)
        return

    # 5) Запрос к API
    try:
        resp = requests.get(QR_API_URL, params={
            "cardNumber": card_number,
            "apikey": QR_API_KEY
        }, timeout=10)
        resp.raise_for_status()
        data_api = resp.json()

        balance = data_api.get("Balance", "неизвестно")
        history = data_api.get("BalanceHistory", [])

        text = f"**Номер карты**: `{card_number}`\n" \
               f"**Баланс**: `{balance}`\n\n"
        if history:
            text += "**История операций**:\n"
            for h in history:
                sign = "+" if h.get("isReplenishment") else "-"
                val = h.get("value","?")
                dt = h.get("date","?")
                place = h.get("parkObjectName","")
                text += f"{dt} {sign}{val} {place}\n"

        await progress_msg.delete()
        kb = _qr_keyboard(scanning_role)
        r_msg = await message.answer(text, parse_mode="Markdown", reply_markup=kb)
        data["active_message_ids"].append(r_msg.message_id)
        await state.update_data(data)

    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await progress_msg.delete()
        kb = _qr_keyboard(scanning_role)
        e_msg = await message.answer("❌ Ошибка при запросе к серверу.", reply_markup=kb)
        data["active_message_ids"].append(e_msg.message_id)
        await state.update_data(data)

@router.callback_query(F.data == "qr_again")
async def handle_qr_again(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        await callback.message.delete()
    except:
        pass

    new_msg = await callback.message.answer("Пожалуйста, отправьте новое фото с QR-кодом.")
    data["active_message_ids"].append(new_msg.message_id)
    await state.update_data(data)
    await callback.answer()


def _qr_keyboard(scanning_role: str) -> InlineKeyboardMarkup:
    """
    Если scanning_role='admin' => «Вернуться к выбору роли» => admin_back
    Иначе => back_to_menu:{operator/consultant} => «В главное меню»
    """
    if scanning_role == "admin":
        back_callback = "admin_back"
        back_text = "Вернуться к выбору роли"
    else:
        back_callback = f"back_to_menu:{scanning_role}"
        back_text = "В главное меню"

    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Сканировать ещё", callback_data="qr_again"),
            InlineKeyboardButton(text=back_text, callback_data=back_callback)
        ]]
    )
