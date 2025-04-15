# telegram_bot/app/main.py

import asyncio
import logging

from telegram_bot.core.dispatcher import bot, dispatcher
from telegram_bot.core.router import setup_routers

# Настройка базового логгирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PGB_BOT")

async def main():
    dispatcher.include_router(setup_routers())
    logger.info("🚀 Бот запущен")
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔️ Бот остановлен")
