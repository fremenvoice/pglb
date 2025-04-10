import logging
import re
import requests
import cv2
import numpy as np
from pyzbar.pyzbar import decode

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PhotoSize

from telegram_bot.core.states import QRScannerState
from telegram_bot.app.config import QR_API_URL, QR_API_KEY

router = Router()
logger = logging.getLogger(__name__)

def extract_card_number(qr_data: str) -> str | None:
    """
    Извлекаем f_persAcc=NNNNNN из строки QR-кода
    Пример:
    https://qr.sbplat.ru/qrid?oi=parkiizhevska&si=dkparkticket&type=92&f_persAcc=1783844276300003
    """
    match = re.search(r"f_persAcc=(\d+)", qr_data)
    return match.group(1) if match else None

@router.message(QRScannerState.waiting_for_photo, F.photo)
async def handle_qr_photo(message: Message, state: FSMContext):
    await message.answer("⏳ Сканирую QR-код...")

    # Скачиваем фото
    photo: PhotoSize = message.photo[-1]
    photo_file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(photo_file.file_path)

    # Преобразуем в OpenCV-формат
    img_array = np.frombuffer(file_bytes.read(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # Распознаем QR-код
    decoded = decode(img)
    if not decoded:
        await message.answer("❌ Не удалось распознать QR. Попробуйте снова.")
        return

    qr_text = decoded[0].data.decode("utf-8")
    logger.info(f"QR data: {qr_text}")

    card_number = extract_card_number(qr_text)
    if not card_number:
        await message.answer("❌ В QR-коде нет параметра f_persAcc.")
        return

    # Запрос к API
    try:
        params = {"cardNumber": card_number, "apikey": QR_API_KEY}
        resp = requests.get(QR_API_URL, params=params, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        balance = data.get("Balance", "неизвестно")
        history = data.get("BalanceHistory", [])

        text = f"**Номер карты**: `{card_number}`\n**Баланс**: `{balance}`\n\n"
        if history:
            text += "**История операций**:\n"
            for entry in history:
                sign = "+" if entry.get("isReplenishment") else "-"
                val = entry.get("value", "?")
                dt = entry.get("date", "?")
                place = entry.get("parkObjectName", "")
                text += f"{dt} {sign}{val} {place}\n"

        await message.answer(text, parse_mode="Markdown")
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("❌ Ошибка при запросе к серверу.")

    # Завершаем состояние
    await state.clear()

@router.message(QRScannerState.waiting_for_photo)
async def handle_non_photo_in_qr(message: Message):
    """Если пришло не фото, а что-то другое, просим повторить"""
    await message.answer("⚠️ Отправьте фото с QR-кодом или вернитесь в главное меню.")
