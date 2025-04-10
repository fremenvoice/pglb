import logging
import os

from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from telegram_bot.services.access_control import get_user_info
from telegram_bot.services.text_service import get_text_block, render_welcome
from telegram_bot.keyboards.operator import get_operator_keyboard
from telegram_bot.keyboards.consultant import get_consultant_keyboard
from telegram_bot.keyboards.admin import get_admin_role_selector, get_back_to_role_selector

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Меню операторов")
async def show_operator_menu_for_admin(message: Message):
    await message.answer("Меню оператора", reply_markup=get_operator_keyboard())
    await message.answer("🔁", reply_markup=get_back_to_role_selector())


@router.message(F.text == "Меню консультантов")
async def show_consultant_menu_for_admin(message: Message):
    await message.answer("Меню консультанта", reply_markup=get_consultant_keyboard())
    await message.answer("🔁", reply_markup=get_back_to_role_selector())


@router.message(F.text == "Без роли")
async def show_guest_placeholder_for_admin(message: Message):
    text = get_text_block("about_park.md")
    await message.answer(text, reply_markup=get_back_to_role_selector())


@router.message(F.text == "🔁 На экран выбора роли")
async def return_to_role_selection(message: Message):
    # Повторяем welcome
    username = message.from_user.username
    info = get_user_info(username)

    if not info:
        await message.answer("Ошибка авторизации.")
        return

    full_name = info["full_name"]
    roles = info["roles"]
    primary_role = roles[0]

    logo_path = os.path.join(os.path.dirname(__file__), "..", "domain", "img", "logo.png")
    photo = FSInputFile(logo_path)
    await message.answer_photo(photo)

    welcome_text = render_welcome(full_name, primary_role)
    await message.answer(welcome_text, reply_markup=get_admin_role_selector())
