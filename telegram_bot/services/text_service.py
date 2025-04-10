import os
import logging
import re

logger = logging.getLogger(__name__)
BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "domain", "text_blocks")

role_display_names = {
    "admin": "Администратор",
    "consultant": "Консультант",
    "operator": "Оператор"
}

def escape_markdown(text: str) -> str:
    escape_chars = r'([\\`*_{}\[\]()#+\-.!])'
    return re.sub(escape_chars, r'\\\1', text)

def get_text_block(filename: str) -> str:
    filepath = os.path.join(BASE_PATH, filename)
    if not os.path.isfile(filepath):
        logger.warning(f"⚠️ Текстовый блок не найден: {filename}")
        escaped_filename = escape_markdown(filename)
        return f"⚠️ Блок текста {escaped_filename} не найден."

    logger.debug(f"📖 Загрузка текстового блока: {filename}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def render_welcome(full_name: str, role: str) -> str:
    raw_template = get_text_block("welcome.md")
    role_display = role_display_names.get(role, role)
    formatted = raw_template.format(ФИО=full_name, role=role_display)
    return formatted
