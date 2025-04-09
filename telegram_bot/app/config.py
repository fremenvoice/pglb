from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

SPREADSHEET_ID_OPERATORS = os.getenv("SPREADSHEET_ID_OPERATORS")
SPREADSHEET_ID_CONSULTANTS = os.getenv("SPREADSHEET_ID_CONSULTANTS")
SPREADSHEET_ID_PHONES = os.getenv("SPREADSHEET_ID_PHONES")

GID_OPERATORS = int(os.getenv("GID_OPERATORS", "0"))
GID_CONSULTANTS = int(os.getenv("GID_CONSULTANTS", "0"))
GID_PHONES = int(os.getenv("GID_PHONES", "0"))
