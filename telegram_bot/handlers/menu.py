import logging
import os

from aiogram import Router, F
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

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("menu:"))
async def handle_menu_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обработка выбора пункта меню (menu_by_role[role]).
    Если qr_scanner.md => scanning_role=role (admin/operator/consultant).
    """
    username = callback.from_user.username
    label = callback.data.split("menu:")[1]

    info = get_user_info(username)
    if not info or not info["roles"]:
        await callback.answer("❌ Нет доступа.")
        return

    data = await state.get_data()
    role = data.get("role") or info["roles"][0]
    menu = menu_by_role.get(role, [])

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить старое меню: {e}")

    message_ids = []

    for item_label, filename in menu:
        if item_label == label:
            text = get_text_block(filename)

            if filename in ("visitors.md", "emergency.md"):
                sent_text = await callback.message.answer(text)
                message_ids.append(sent_text.message_id)

                img_filename = "sitmap.png" if filename == "visitors.md" else "fireext.png"
                img_path = os.path.join("telegram_bot", "domain", "img", img_filename)
                sent_photo = await callback.message.answer_photo(
                    photo=FSInputFile(img_path),
                    reply_markup=get_back_to_menu_keyboard(role)
                )
                message_ids.append(sent_photo.message_id)

            elif filename == "qr_scanner.md":
                # Включаем режим сканирования
                await state.update_data(scanning_role=role)
                # Отправляем инструкцию + кнопку возврата

                # Если админ => "Вернуться к выбору роли" (admin_back)
                # Иначе => "В главное меню" (back_to_menu:role)
                if role == "admin":
                    back_callback = "admin_back"
                    back_text = "Вернуться к выбору роли"
                else:
                    back_callback = f"back_to_menu:{role}"
                    back_text = "В главное меню"

                kb = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text=back_text, callback_data=back_callback)
                ]])
                sent_msg = await callback.message.answer(text, reply_markup=kb)
                message_ids.append(sent_msg.message_id)

            else:
                # Прочие пункты: просто текст + "В главное меню"
                sent_msg = await callback.message.answer(
                    text,
                    reply_markup=get_back_to_menu_keyboard(role)
                )
                message_ids.append(sent_msg.message_id)

            active_ids = data.get("active_message_ids", [])
            active_ids += message_ids
            await state.update_data(active_message_ids=active_ids)

            await callback.answer()
            return

    await callback.answer("⚠️ Раздел не найден.")


@router.callback_query(F.data.startswith("admin_menu:"))
async def handle_admin_menu_choice(callback: CallbackQuery, state: FSMContext):
    """
    Когда админ на экране выбора ролей нажимает какую-то кнопку,
    e.g. admin_menu:operator => role=operator
         admin_menu:qr_scanner => role=admin + scanning_role=admin
    """
    choice = callback.data.split("admin_menu:")[1]
    username = callback.from_user.username
    info = get_user_info(username)

    if not info or "admin" not in info["roles"]:
        await callback.answer("⚠️ Доступ запрещён.")
        return

    # Если выбрал admin_menu:qr_scanner => scanning_role=admin
    if choice == "qr_scanner":
        await state.update_data(role="admin", scanning_role="admin")
        text = get_text_block("qr_scanner.md")
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Вернуться к выбору роли", callback_data="admin_back")
        ]])
        # Редактируем текущее сообщение => инструкции
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return

    # Иначе operator/consultant/none
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
    """
    Возврат к "выбору роли" для админа. Удаляем все active_message_ids, scanning_role.
    """
    username = callback.from_user.username
    info = get_user_info(username)
    if not info or "admin" not in info["roles"]:
        await callback.answer("⚠️ Доступ запрещён.")
        return

    from telegram_bot.services.text_service import render_welcome
    full_name = info["full_name"]
    text = render_welcome(full_name, "admin")
    kb = get_admin_role_choice_keyboard()

    data = await state.get_data()
    active_ids = data.get("active_message_ids", [])
    for msg_id in active_ids:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить admin_back-кнопку: {e}")

    # Очищаем FSM
    await state.clear()

    # Отправляем список ролей
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_menu:"))
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    В главное меню для operator/consultant
    """
    username = callback.from_user.username
    info = get_user_info(username)
    if not info or not info["roles"]:
        await callback.answer("❌ Нет доступа.")
        return

    data = await state.get_data()
    role = data.get("role") or info["roles"][0]

    # Удаляем все ID (включая фото, bot-сообщения)
    active_ids = data.get("active_message_ids", [])
    for msg_id in active_ids:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

    # Удаляем кнопку
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить кнопку меню: {e}")

    # Очищаем FSM (но при желании оставляем role)
    data["active_message_ids"] = []
    data["scanning_role"] = None
    await state.update_data(data)

    kb = get_menu_inline_keyboard_for_role(role)
    new_msg = await callback.message.answer(f"📋 Меню роли: {role}", reply_markup=kb)
    await state.update_data(active_message_ids=[new_msg.message_id])

    await callback.answer()
