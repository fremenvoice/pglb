import logging
import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from telegram_bot.services.access_control import get_user_info
from telegram_bot.services.text_service import get_text_block
from telegram_bot.domain.menu_registry import menu_by_role
from telegram_bot.keyboards.inline import (
    get_menu_inline_keyboard_for_role,
    get_admin_role_choice_keyboard,
    get_back_to_menu_keyboard
)

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("menu:"))
async def handle_menu_callback(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    label = callback.data.split("menu:")[1]

    info = get_user_info(username)
    if not info or not info["roles"]:
        await callback.answer("❌ Нет доступа.")
        return

    # Получаем роль из FSM (для админа), либо основную
    data = await state.get_data()
    role = data.get("role") or info["roles"][0]
    menu = menu_by_role.get(role, [])

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить сообщение: {e}")

    for item_label, filename in menu:
        if item_label == label:
            if filename.endswith(".md") or filename.endswith(".txt"):
                text = get_text_block(filename)
                await callback.message.answer(text)

                # Картинка + кнопка (если нужно)
                img_path = None
                if filename == "visitors.md":
                    img_path = os.path.join("telegram_bot", "domain", "img", "sitmap.png")
                elif filename == "emergency.md":
                    img_path = os.path.join("telegram_bot", "domain", "img", "fireext.png")

                if img_path:
                    # Отправляем картинку с кнопкой
                    await callback.message.answer_photo(
                        photo=FSInputFile(img_path),
                        reply_markup=get_back_to_menu_keyboard(role)
                    )
                else:
                    # Только текст с кнопкой
                    await callback.message.answer(
                        text,
                        reply_markup=get_back_to_menu_keyboard(role)
                    )

                await callback.answer()
                return
            else:
                await callback.message.answer(f"🔧 Действие `{filename}` пока не реализовано.")
                await callback.answer()
                return

    await callback.answer("⚠️ Раздел не найден.")


@router.callback_query(F.data.startswith("admin_menu:"))
async def handle_admin_menu_choice(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split("admin_menu:")[1]
    username = callback.from_user.username
    info = get_user_info(username)

    if not info or "admin" not in info.get("roles", []):
        await callback.answer("⚠️ Доступ запрещён.")
        return

    logger.info(f"👤 Админ @{username} выбрал: {choice}")

    await state.update_data(role=choice)

    if choice == "none":
        text = get_text_block("about_park.md")
        kb = get_menu_inline_keyboard_for_role("admin", only_back=True)
        await callback.message.edit_text(text, reply_markup=kb)
    else:
        kb = get_menu_inline_keyboard_for_role(choice)
        await callback.message.edit_text(f"📋 Меню роли: {choice}", reply_markup=kb)

    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def handle_admin_back(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    info = get_user_info(username)

    if not info or "admin" not in info.get("roles", []):
        await callback.answer("⚠️ Доступ запрещён.")
        return

    full_name = info["full_name"]
    text = render_welcome(full_name, "admin")
    kb = get_admin_role_choice_keyboard()

    await state.clear()
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_menu:"))
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    info = get_user_info(username)
    if not info or not info["roles"]:
        await callback.answer("❌ Нет доступа.")
        return

    data = await state.get_data()
    role = data.get("role") or info["roles"][0]
    kb = get_menu_inline_keyboard_for_role(role)

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить сообщение с кнопкой: {e}")

    try:
        await callback.message.reply_to_message.delete()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить текстовое сообщение: {e}")

    await callback.message.answer(f"📋 Меню роли: {role}", reply_markup=kb)
    await callback.answer()
