from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Таблицы Google Sheets
SPREADSHEET_ID_OPERATORS = os.getenv("SPREADSHEET_ID_OPERATORS")
SPREADSHEET_ID_CONSULTANTS = os.getenv("SPREADSHEET_ID_CONSULTANTS")
SPREADSHEET_ID_PHONES = os.getenv("SPREADSHEET_ID_PHONES")
SPREADSHEET_ID_OPERATORS_RENT = os.getenv("SPREADSHEET_ID_OPERATORS_RENT")  # Новая таблица арендаторов

# GID-листы
GID_OPERATORS = int(os.getenv("GID_OPERATORS", "0"))
GID_CONSULTANTS = int(os.getenv("GID_CONSULTANTS", "0"))
GID_PHONES = int(os.getenv("GID_PHONES", "0"))
GID_OPERATORS_RENT = int(os.getenv("GID_OPERATORS_RENT", "0"))  # Новый GID для аренды

QR_API_URL = os.getenv("QR_API_URL")
QR_API_KEY = os.getenv("QR_API_KEY")