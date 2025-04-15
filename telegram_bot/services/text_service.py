# telegram_bot/services/text_service.py

import os
import re
import logging
import asyncio
import aiofiles  # ← ДОБАВЛЕНО

logger = logging.getLogger(__name__)
BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "domain", "text_blocks")

# Кеш текстовых блоков: {filename: content}
_text_blocks: dict[str, str] = {}

role_display_names = {
    "admin": "Администратор",
    "consultant": "Консультант",
    "operator": "Оператор",
    "operator_rent": "Оператор арендатора"
}


def escape_markdown(text: str) -> str:
    escape_chars = r'([\\*_{}\[\]()#+\-.!])'
    return re.sub(escape_chars, r'\\\1', text)


def get_text_block(filename: str) -> str:
    """
    Быстрый доступ к текстовому блоку из кеша.
    Если файл не был загружен — выдаст предупреждение.
    """
    content = _text_blocks.get(filename)
    if content is None:
        logger.warning(f"⚠️ Блок текста {filename} не загружен в кеш.")
        return f"⚠️ Блок текста `{escape_markdown(filename)}` не найден."
    return content


def render_welcome(full_name: str, role: str) -> str:
    raw_template = get_text_block("welcome.md")
    role_display = role_display_names.get(role, role)

    full_name_safe = escape_markdown(full_name)
    role_safe = escape_markdown(role_display)

    return raw_template.format(ФИО=full_name_safe, role=role_safe)


async def preload_text_blocks():
    """
    Асинхронно загружает все .md файлы из text_blocks в память.
    """
    global _text_blocks
    _text_blocks = {}

    if not os.path.isdir(BASE_PATH):
        logger.warning(f"❌ Каталог text_blocks не найден: {BASE_PATH}")
        return

    for filename in os.listdir(BASE_PATH):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(BASE_PATH, filename)
        try:
            async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                content = await f.read()
                _text_blocks[filename] = content
                logger.info(f"📦 Загружен текстовый блок: {filename}")
        except Exception as e:
            logger.warning(f"❌ Ошибка при загрузке {filename}: {e}")
