# telegram_bot/services/text_service.py

import os
import logging
import re

logger = logging.getLogger(__name__)

# Путь к папке с текстами
BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "domain", "text_blocks")

# Отображаемые названия ролей
role_display_names = {
    "admin": "Администратор",
    "consultant": "Консультант",
    "operator": "Оператор",
    "operator_rent": "Оператор арендатора"
}


def escape_markdown(text: str) -> str:
    """
    Экранирует спецсимволы Telegram MarkdownV2.
    """
    escape_chars = r'([\\*_{}\[\]()#+\-.!])'
    return re.sub(escape_chars, r'\\\1', text)


def get_text_block(filename: str) -> str:
    """
    Загружает и возвращает текстовый блок Markdown.
    """
    filepath = os.path.join(BASE_PATH, filename)
    if not os.path.isfile(filepath):
        logger.warning(f"⚠️ Текстовый блок не найден: {filename}")
        return f"⚠️ Блок текста *{escape_markdown(filename)}* не найден."

    logger.debug(f"📖 Загрузка текстового блока: {filename}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def render_welcome(full_name: str, role: str) -> str:
    """
    Возвращает шаблон приветствия с подставленным именем и ролью.
    """
    raw_template = get_text_block("welcome.md")
    role_display = role_display_names.get(role, role)

    # Экранируем переменные для Markdown
    full_name_safe = escape_markdown(full_name)
    role_safe = escape_markdown(role_display)

    return raw_template.format(ФИО=full_name_safe, role=role_safe)
