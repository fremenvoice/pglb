from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, ContextTypes
from services.text_service import render_text_block, get_text_block
from services.access_control import get_user_role
from services.db import get_connection
from pathlib import Path

# Отображение ролей в читаемом виде
ROLE_LABELS = {
    "creator": "Создатель",
    "admin": "Администратор",
    "operator": "Оператор",
    "consultant": "Консультант"
}

def get_full_name(username: str) -> str | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT full_name FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
    return row["full_name"] if row else None

def get_admin_role_choice_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📋 Меню операторов", callback_data="admin_select_operator"),
            InlineKeyboardButton("📋 Меню консультантов", callback_data="admin_select_consultant")
        ],
        [
            InlineKeyboardButton("🙋 Без роли", callback_data="admin_select_none")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_start_work_button(role: str) -> InlineKeyboardMarkup:
    """
    Создаём кнопку "Приступить к работе!" только для операторов и консультантов.
    """
    if role == "operator" or role == "consultant":
        return InlineKeyboardMarkup([ 
            [InlineKeyboardButton("Приступить к работе!", callback_data="start_work")]
        ])
    return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    role = get_user_role(username)

    logo_path = Path("assets/logo.png")

    if role is None:
        # Для пользователей без роли - показываем только приветственное сообщение
        text = get_text_block("about_park.md")
        if logo_path.exists():
            with logo_path.open("rb") as photo:
                await update.message.reply_photo(photo=photo, caption=text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")
    else:
        # Для авторизованных пользователей
        full_name = get_full_name(username) or update.effective_user.full_name or username
        role_label = ROLE_LABELS.get(role, role)
        text = render_text_block("welcome.md", full_name=full_name, role_label=role_label)

        start_work_button = None
        keyboard = []

        # Для админов и создателей — меню выбора роли
        if role == "admin" or role == "creator":
            keyboard = list(get_admin_role_choice_keyboard().inline_keyboard)

        # Для операторов и консультантов — кнопка "Приступить к работе!"
        if role == "operator" or role == "consultant":
            start_work_button = get_start_work_button(role)

        if logo_path.exists():
            with logo_path.open("rb") as photo:
                # Отправляем фото с текстом и кнопками
                if start_work_button:
                    keyboard = start_work_button.inline_keyboard + keyboard
                await update.message.reply_photo(photo=photo, caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            # Отправляем только текст с кнопками
            if start_work_button:
                keyboard = start_work_button.inline_keyboard + keyboard
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

start_handler = CommandHandler("start", start_command)
