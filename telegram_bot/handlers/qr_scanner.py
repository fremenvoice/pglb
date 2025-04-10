import logging
import re
import requests
import cv2
import numpy as np
from pyzbar.pyzbar import decode

from aiogram import Router, F
from aiogram.types import Message, PhotoSize, InlineKeyboardMarkup, InlineKeyboardButton
from telegram_bot.services.access_control import get_user_info

router = Router()
logger = logging.getLogger(__name__)

QR_API_URL = "http://10.0.0.4/Api/Card/GetBalanceAndHistory"
API_KEY = "APIKEYGLOBAL"

def extract_card_number(qr_data: str) -> str | None:
    match = re.search(r"f_persAcc=(\d+)", qr_data)
    return match.group(1) if match else None

@router.message(F.photo)
async def global_qr_handler(message: Message):
    """
    Глобальный обработчик фотографий от авторизованных пользователей.
    """
    username = message.from_user.username
    from telegram_bot.services.access_control import get_user_info
    info = get_user_info(username)

    # Если пользователь не авторизован, игнорируем или высылаем предупреждение
    if not info or not info.get("roles"):
        logger.info(f"Пользователь @{username} не авторизован, пропускаем фото.")
        return

    # Есть роль, значит можем сканировать
    await message.answer("⏳ Обрабатываю QR-код...")

    photo: PhotoSize = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_bytes = await message.bot.download_file(file.file_path)

    # Распознаём через opencv + pyzbar
    import io
    img_array = np.frombuffer(file_bytes.read(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    decoded = decode(img)
    if not decoded:
        await message.answer("❌ Не удалось распознать QR. Возможно, это не QR-код.")
        return

    qr_text = decoded[0].data.decode("utf-8")
    logger.info(f"QR data from @{username}: {qr_text}")

    card_number = extract_card_number(qr_text)
    if not card_number:
        await message.answer("❌ Не найдено f_persAcc в QR-коде.")
        return

    # Запрос к API
    try:
        resp = requests.get(QR_API_URL, params={
            "cardNumber": card_number,
            "apikey": API_KEY
        }, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        balance = data.get("Balance", "неизвестно")
        history = data.get("BalanceHistory", [])

        text = f"**Номер карты**: `{card_number}`\n" \
               f"**Баланс**: `{balance}`\n\n"

        if history:
            text += "**История операций**:\n"
            for h in history:
                sign = "+" if h.get("isReplenishment") else "-"
                val = h.get("value", "?")
                dt = h.get("date", "?")
                place = h.get("parkObjectName", "")
                text += f"{dt} {sign}{val} {place}\n"

        # Берём первую роль для возврата
        user_roles = info["roles"]
        main_role = user_roles[0] if user_roles else "operator"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Сканировать ещё", callback_data="qr_again"),
                InlineKeyboardButton(text="В главное меню", callback_data=f"back_to_menu:{main_role}")
            ]
        ])

        await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("❌ Ошибка при запросе к серверу.")

@router.callback_query(F.data == "qr_again")
async def handle_qr_again(callback):
    """
    Кнопка «Сканировать ещё» - удаляем сообщение и просим прислать новое фото
    """
    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer("📷 Отправьте новое фото с QR-кодом...")
    await callback.answer()
