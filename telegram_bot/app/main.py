import asyncio
from telegram_bot.core.dispatcher import bot, dp
from telegram_bot.core.router import setup_routers
from telegram_bot.services.log_service import setup_logger

logger = setup_logger()

async def main():
    dp.include_router(setup_routers())
    logger.info("🚀 Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔️ Бот остановлен")
