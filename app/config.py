import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

SHEET_OPERATORS_ID = os.getenv("SHEET_OPERATORS_ID")
SHEET_OPERATORS_GID = os.getenv("SHEET_OPERATORS_GID")

SHEET_CONSULTANTS_ID = os.getenv("SHEET_CONSULTANTS_ID")
SHEET_CONSULTANTS_GID = os.getenv("SHEET_CONSULTANTS_GID")

SHEET_PHONES_ID = os.getenv("SHEET_PHONES_ID")
SHEET_PHONES_GID = os.getenv("SHEET_PHONES_GID")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "pgb_bot")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
