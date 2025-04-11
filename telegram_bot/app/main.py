# telegram_bot/app/main.py

import asyncio
import logging

from telegram_bot.core.dispatcher import bot, dp
from telegram_bot.core.router import setup_routers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PGB_BOT")

async def main():
    dp.include_router(setup_routers())
    logger.info("🚀 Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔️ Бот остановлен")
