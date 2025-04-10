import logging
import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

from telegram_bot.services.access_control import get_user_info
from telegram_bot.services.text_service import get_text_block, render_welcome
from telegram_bot.domain.menu_registry import menu_by_role
from telegram_bot.keyboards.inline import (
    get_menu_inline_keyboard_for_role,
    get_admin_role_choice_keyboard,
    get_back_to_menu_keyboard
)
from telegram_bot.core.states import AdminMenuContextState, QRScannerState

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

    data = await state.get_data()
    role = data.get("role") or info["roles"][0]
    menu = menu_by_role.get(role, [])

    # Удаляем текущее меню
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить меню: {e}")

    for item_label, filename in menu:
        if item_label == label:
            text = get_text_block(filename)

            # Массив message_ids для удаления при возврате
            message_ids = []

            # 1) "Посетители" или "ЧП" → текст + картинка
            if filename in ("visitors.md", "emergency.md"):
                sent_text_msg = await callback.message.answer(text)
                message_ids.append(sent_text_msg.message_id)

                img_filename = "sitmap.png" if filename == "visitors.md" else "fireext.png"
                img_path = os.path.join("telegram_bot", "domain", "img", img_filename)

                sent_photo_msg = await callback.message.answer_photo(
                    photo=FSInputFile(img_path),
                    reply_markup=get_back_to_menu_keyboard(role)
                )
                message_ids.append(sent_photo_msg.message_id)

            # 2) "qr_scanner.md" → отправляем текст и переводим в FSM для ожидания фото
            elif filename == "qr_scanner.md":
                sent_msg = await callback.message.answer(text)
                message_ids.append(sent_msg.message_id)

                # Устанавливаем FSM состояние → ждём фото
                await state.set_state(QRScannerState.waiting_for_photo)

            # 3) Остальные разделы → текст + кнопка
            else:
                sent_msg = await callback.message.answer(
                    text,
                    reply_markup=get_back_to_menu_keyboard(role)
                )
                message_ids.append(sent_msg.message_id)

            # Сохраняем ID отправленных сообщений
            await state.update_data(active_message_ids=message_ids)
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

    active_message_ids = data.get("active_message_ids", [])
    for msg_id in active_message_ids:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить сообщение {msg_id}: {e}")

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"⚠️ Не удалось удалить кнопку возврата: {e}")

    kb = get_menu_inline_keyboard_for_role(role)
    sent_menu_msg = await callback.message.answer(f"📋 Меню роли: {role}", reply_markup=kb)

    await state.update_data(active_message_ids=[sent_menu_msg.message_id])
    await callback.answer()
