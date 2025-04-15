# telegram_bot/handlers/menu.py
import asyncio
import logging
import os
import urllib.parse

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from telegram_bot.services.access_control import get_user_info
from telegram_bot.services.text_service import get_text_block, render_welcome
from telegram_bot.domain.menu_registry import menu_by_role
from telegram_bot.keyboards.inline import (
    get_menu_inline_keyboard_for_role,
    get_admin_role_choice_keyboard,
    get_back_to_menu_keyboard
)
from telegram_bot.handlers.qr_scanner import send_qr_scanner

logger = logging.getLogger(__name__)
router = Router()


async def delete_active_messages(bot: Bot, chat_id: int, ids: list[int]):
    import asyncio

    async def delete_one(msg_id: int):
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

    await asyncio.gather(*(delete_one(msg_id) for msg_id in ids))



@router.callback_query(F.data.startswith("menu:"))
async def handle_menu_callback(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    encoded_label = callback.data.split("menu:")[1]
    label = urllib.parse.unquote(encoded_label)

    info = get_user_info(username)
    if not info or not info["roles"]:
        await callback.answer("❌ Нет доступа.")
        return

    data = await state.get_data()
    user_role = info["roles"][0]
    admin_subrole = data.get("admin_subrole")
    current_role = admin_subrole if user_role == "admin" and admin_subrole else user_role

    await delete_active_messages(callback.bot, callback.message.chat.id, data.get("active_message_ids", []))
    data["active_message_ids"] = []
    await state.update_data(data)

    menu = menu_by_role.get(current_role, [])
    message_ids = []

    for item_label, filename in menu:
        if item_label == label:
            text = get_text_block(filename)

            if filename == "qr_scanner.md":
                data["scanning_role"] = current_role
                await state.update_data(data)
                await send_qr_scanner(callback.message, current_role, state)
                await callback.answer()
                return

            if filename in ("visitors.md", "emergency.md"):
                sent_text = await callback.message.answer(text)
                message_ids.append(sent_text.message_id)

                img_filename = "sitmap.png" if filename == "visitors.md" else "fireext.png"
                img_path = os.path.join("telegram_bot", "domain", "img", img_filename)
                sent_photo = await callback.message.answer_photo(
                    photo=FSInputFile(img_path),
                    reply_markup=get_back_to_menu_keyboard(current_role)
                )
                message_ids.append(sent_photo.message_id)
            else:
                sent_msg = await callback.message.answer(
                    text,
                    reply_markup=get_back_to_menu_keyboard(current_role)
                )
                message_ids.append(sent_msg.message_id)

            data["active_message_ids"] = message_ids
            await state.update_data(data)
            await callback.answer()
            return

    await callback.answer("⚠️ Раздел не найден.")


@router.callback_query(F.data.startswith("admin_menu:"))
async def handle_admin_menu_choice(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split("admin_menu:")[1]
    info = get_user_info(callback.from_user.username)
    if not info or "admin" not in info["roles"]:
        await callback.answer("⚠️ Доступ запрещён.")
        return

    data = await state.get_data()
    await delete_active_messages(callback.bot, callback.message.chat.id, data.get("active_message_ids", []))
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить текущее сообщение admin_menu: {e}")

    if choice == "operator_rent":
        await state.update_data({
            "admin_subrole": "operator_rent",
            "scanning_role": "operator_rent",
            "active_message_ids": []
        })
        await send_qr_scanner(callback.message, role="operator_rent")
        await callback.answer()
        return

    if choice == "qr_scanner":
        text = get_text_block("qr_scanner.md")
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Вернуться к выбору роли", callback_data="admin_back")]]
        )
        msg = await callback.message.answer(text, reply_markup=kb)
        await state.update_data({
            "admin_subrole": None,
            "scanning_role": "admin",
            "active_message_ids": [msg.message_id]
        })
        await callback.answer()
        return

    if choice == "none":
        text = get_text_block("about_park.md")
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔁 На экран выбора роли", callback_data="admin_back")]]
        )
        msg = await callback.message.answer(text, reply_markup=kb)
        await state.update_data({
            "admin_subrole": None,
            "scanning_role": None,
            "active_message_ids": [msg.message_id]
        })
        await callback.answer()
        return

    if choice in ("operator", "consultant"):
        kb = get_menu_inline_keyboard_for_role(choice, only_back=True)
        msg = await callback.message.answer(f"📋 Меню роли: {choice}", reply_markup=kb)
        await state.update_data({
            "admin_subrole": choice,
            "scanning_role": None,
            "active_message_ids": [msg.message_id]
        })
        await callback.answer()
        return

    await callback.answer("❌ Неизвестная команда admin_menu.")


@router.callback_query(F.data == "admin_back")
async def handle_admin_back(callback: CallbackQuery, state: FSMContext):
    info = get_user_info(callback.from_user.username)
    if not info or "admin" not in info["roles"]:
        await callback.answer("⚠️ Доступ запрещён.")
        return

    full_name = info["full_name"]
    kb = get_admin_role_choice_keyboard()
    text = render_welcome(full_name, "admin")

    data = await state.get_data()
    await delete_active_messages(callback.bot, callback.message.chat.id, data.get("active_message_ids", []))
    try:
        await callback.message.delete()
    except:
        pass

    await state.clear()

    msg = await callback.message.answer(text, reply_markup=kb)
    await state.update_data({"active_message_ids": [msg.message_id]})
    await callback.answer()


async def show_main_menu_for_role(bot: Bot, chat_id: int, role: str, state: FSMContext):
    kb = get_menu_inline_keyboard_for_role(role, only_back=(role != "operator_rent"))
    msg = await bot.send_message(chat_id, f"📋 Меню роли: {role}", reply_markup=kb)
    await state.update_data({
        "admin_subrole": None if role not in ("operator", "consultant") else role,
        "scanning_role": None,
        "active_message_ids": [msg.message_id]
    })


@router.callback_query(F.data.startswith("back_to_menu:"))
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    info = get_user_info(callback.from_user.username)
    if not info or not info["roles"]:
        await callback.answer("❌ Нет доступа.")
        return

    data = await state.get_data()
    user_role = info["roles"][0]
    admin_subrole = data.get("admin_subrole")
    current_role = admin_subrole if user_role == "admin" and admin_subrole else user_role

    await delete_active_messages(callback.bot, callback.message.chat.id, data.get("active_message_ids", []))
    try:
        await callback.message.delete()
    except:
        pass

    kb = get_menu_inline_keyboard_for_role(current_role, only_back=(user_role == "admin"))
    msg = await callback.message.answer(f"📋 Меню роли: {current_role}", reply_markup=kb)
    await state.update_data({
        "scanning_role": None,
        "active_message_ids": [msg.message_id]
    })
    await callback.answer()
