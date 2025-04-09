import logging
import os

from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from telegram_bot.services.access_control import get_user_info
from telegram_bot.services.text_service import get_text_block, render_welcome

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

    # Приветствие
    welcome_text = render_welcome(full_name, primary_role)
    await message.answer(welcome_text)
