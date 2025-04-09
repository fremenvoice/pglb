import os
import logging

logger = logging.getLogger(__name__)
BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "domain", "text_blocks")

# Отображаемые названия ролей
role_display_names = {
    "admin": "Администратор",
    "consultant": "Консультант",
    "operator": "Оператор"
}


def get_text_block(filename: str) -> str:
    filepath = os.path.join(BASE_PATH, filename)
    if not os.path.isfile(filepath):
        logger.warning(f"⚠️ Текстовый блок не найден: {filename}")
        return f"⚠️ Блок текста '{filename}' не найден."

    logger.debug(f"📖 Загрузка текстового блока: {filename}")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def render_welcome(full_name: str, role: str) -> str:
    """
    Подставляет данные в welcome.md без экранирования.
    """
    raw_template = get_text_block("welcome.md")
    role_display = role_display_names.get(role, role)

    formatted = raw_template.format(ФИО=full_name, role=role_display)
    return formatted
