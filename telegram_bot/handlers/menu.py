import logging
import os

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from telegram_bot.services.access_control import get_user_info
from telegram_bot.services.text_service import get_text_block, render_welcome
from telegram_bot.domain.menu_registry import menu_by_role
from telegram_bot.keyboards.inline import (
    get_menu_inline_keyboard_for_role,
    get_admin_role_choice_keyboard,
    get_admin_back_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("menu:"))
async def handle_menu_callback(callback: CallbackQuery):
    username = callback.from_user.username
    label = callback.data.split("menu:")[1]

    info = get_user_info(username)
    if not info or not info["roles"]:
        await callback.answer("❌ Нет доступа.")
        return

    role = info["roles"][0]
    menu = menu_by_role.get(role, [])

    for item_label, filename in menu:
        if item_label == label:
            if filename.endswith(".md") or filename.endswith(".txt"):
                text = get_text_block(filename)
                await callback.message.answer(text)
            else:
                await callback.message.answer(f"🔧 Действие `{filename}` пока не реализовано.")
            await callback.answer()
            return

    await callback.answer("⚠️ Раздел не найден.")


@router.callback_query(F.data.startswith("admin_menu:"))
async def handle_admin_menu_choice(callback: CallbackQuery):
    choice = callback.data.split("admin_menu:")[1]
    username = callback.from_user.username
    info = get_user_info(username)

    if not info or "admin" not in info.get("roles", []):
        await callback.answer("⚠️ Доступ запрещён.")
        return

    logger.info(f"👤 Админ @{username} выбрал: {choice}")

    if choice == "none":
        text = get_text_block("about_park.md")
        kb = get_admin_back_keyboard()  # ✅ Только кнопка назад
        await callback.message.edit_text(text, reply_markup=kb)
    else:
        kb = get_menu_inline_keyboard_for_role(choice)
        await callback.message.edit_text(f"📋 Меню роли: {choice}", reply_markup=kb)

    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def handle_admin_back(callback: CallbackQuery):
    username = callback.from_user.username
    info = get_user_info(username)

    if not info or "admin" not in info.get("roles", []):
        await callback.answer("⚠️ Доступ запрещён.")
        return

    full_name = info["full_name"]
    text = render_welcome(full_name, "admin")
    kb = get_admin_role_choice_keyboard()

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
