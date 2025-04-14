import logging
import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton as AiogramInlineKeyboardButton



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
    username = callback.from_user.username
    label = callback.data.split("menu:")[1]

    info = get_user_info(username)
    if not info or not info["roles"]:
        await callback.answer("❌ Нет доступа.")
        return

    data = await state.get_data()
    user_role = info["roles"][0]
    admin_subrole = data.get("admin_subrole")
    current_role = admin_subrole if user_role == "admin" and admin_subrole else user_role

    active_ids = data.get("active_message_ids", [])
    for msg_id in active_ids:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")

    data["active_message_ids"] = []
    await state.update_data(data)

    menu = menu_by_role.get(current_role, [])
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
                    reply_markup=get_back_to_menu_keyboard(current_role)
                )
                message_ids.append(sent_photo.message_id)

            elif filename == "qr_scanner.md":
                scanning_role = current_role if current_role in ("operator", "consultant") else "admin"
                data["scanning_role"] = scanning_role
                await state.update_data(data)

                if scanning_role == "admin":
                    back_callback = "admin_back"
                    back_text = "Вернуться к выбору роли"
                else:
                    back_callback = f"back_to_menu:{scanning_role}"
                    back_text = "В главное меню"

                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [AiogramInlineKeyboardButton(text=back_text, callback_data=back_callback)]
                ])
                sent_msg = await callback.message.answer(text, reply_markup=kb)
                message_ids.append(sent_msg.message_id)

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
    username = callback.from_user.username
    info = get_user_info(username)
    if not info or "admin" not in info["roles"]:
        await callback.answer("⚠️ Доступ запрещён.")
        return

    data = await state.get_data()

    active_ids = data.get("active_message_ids", [])
    for msg_id in active_ids:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить старое сообщение {msg_id}: {e}")
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить текущее сообщение admin_menu: {e}")

    data["active_message_ids"] = []
    await state.update_data(data)

    if choice == "qr_scanner":
        # Обновляем состояние, чтобы роль была установлена как "admin"
        data["admin_subrole"] = None
        data["scanning_role"] = "admin"
        await state.update_data(data)

        # Получаем текст для QR-сканера
        text = get_text_block("qr_scanner.md")

        # Формируем клавиатуру с кнопкой для возврата
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [AiogramInlineKeyboardButton(text="Вернуться к выбору роли", callback_data="admin_back")]
        ])

        # Отправляем сообщение с текстом и клавиатурой
        new_msg = await callback.message.answer(text, reply_markup=kb)

        # Сохраняем ID активного сообщения
        data["active_message_ids"] = [new_msg.message_id]
        await state.update_data(data)

        # Завершаем обработку обновления
        await callback.answer()
        return

    if choice == "none":
        data["admin_subrole"] = None
        data["scanning_role"] = None
        await state.update_data(data)

        text = get_text_block("about_park.md")

        # Создаём клавиатуру с ОДНОЙ кнопкой — "🔁 На экран выбора роли"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [AiogramInlineKeyboardButton(text="🔁 На экран выбора роли", callback_data="admin_back")]
        ])

        new_msg = await callback.message.answer(text, reply_markup=kb)
        data["active_message_ids"] = [new_msg.message_id]
        await state.update_data(data)
        await callback.answer()
        return



    if choice in ("operator", "consultant"):
        data["admin_subrole"] = choice
        data["scanning_role"] = None
        await state.update_data(data)

        new_msg = await callback.message.answer(
            f"📋 Меню роли: {choice}",
            reply_markup=get_menu_inline_keyboard_for_role(choice, only_back=True)
        )
        data["active_message_ids"] = [new_msg.message_id]
        await state.update_data(data)
        await callback.answer()
        return

    await callback.answer("Неизвестная команда admin_menu.")


@router.callback_query(F.data == "admin_back")
async def handle_admin_back(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    info = get_user_info(username)
    if not info or "admin" not in info["roles"]:
        await callback.answer("⚠️ Доступ запрещён.")
        return

    full_name = info["full_name"]
    text = render_welcome(full_name, "admin")
    kb = get_admin_role_choice_keyboard()

    data = await state.get_data()
    active_ids = data.get("active_message_ids", [])
    for msg_id in active_ids:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except:
            pass
    try:
        await callback.message.delete()
    except:
        pass

    await state.clear()

    new_msg = await callback.message.answer(text, reply_markup=kb)
    await state.update_data({"active_message_ids": [new_msg.message_id]})
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_menu:"))
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    info = get_user_info(username)
    if not info or not info["roles"]:
        await callback.answer("❌ Нет доступа.")
        return

    data = await state.get_data()
    user_role = info["roles"][0]
    admin_subrole = data.get("admin_subrole")
    current_role = admin_subrole if user_role == "admin" and admin_subrole else user_role

    active_ids = data.get("active_message_ids", [])
    for msg_id in active_ids:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {msg_id}: {e}")
    try:
        await callback.message.delete()
    except:
        pass

    data["scanning_role"] = None
    data["active_message_ids"] = []
    await state.update_data(data)

    only_back = user_role == "admin"
    kb = get_menu_inline_keyboard_for_role(current_role, only_back=only_back)

    new_msg = await callback.message.answer(f"📋 Меню роли: {current_role}", reply_markup=kb)
    data["active_message_ids"] = [new_msg.message_id]
    await state.update_data(data)

    await callback.answer()
