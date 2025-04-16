# telegram_bot/core/dispatcher.py
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from telegram_bot.app.config import BOT_TOKEN

logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)

# FSM-хранилище
storage = MemoryStorage()

# Диспетчер с поддержкой FSM
dispatcher = Dispatcher(storage=storage)

logger.info("🧠 Dispatcher и Bot инициализированы")
