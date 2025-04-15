import os
from dotenv import load_dotenv

load_dotenv()

def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"❌ Обязательная переменная окружения '{name}' не найдена.")
    return value

# Telegram Bot
BOT_TOKEN = _get_env("BOT_TOKEN", required=True)

# Google Sheets IDs
SPREADSHEET_ID_OPERATORS = _get_env("SPREADSHEET_ID_OPERATORS", required=True)
SPREADSHEET_ID_CONSULTANTS = _get_env("SPREADSHEET_ID_CONSULTANTS", required=True)
SPREADSHEET_ID_PHONES = _get_env("SPREADSHEET_ID_PHONES", required=True)
SPREADSHEET_ID_OPERATORS_RENT = _get_env("SPREADSHEET_ID_OPERATORS_RENT", required=True)

# Google Sheets GIDs
GID_OPERATORS = int(_get_env("GID_OPERATORS", "0"))
GID_CONSULTANTS = int(_get_env("GID_CONSULTANTS", "0"))
GID_PHONES = int(_get_env("GID_PHONES", "0"))
GID_OPERATORS_RENT = int(_get_env("GID_OPERATORS_RENT", "0"))

# QR API
QR_API_URL = _get_env("QR_API_URL", required=True)
QR_API_KEY = _get_env("QR_API_KEY", required=True)
