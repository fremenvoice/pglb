# telegram_bot/app/main.py
import asyncio
import logging

from telegram_bot.core.dispatcher import bot, dispatcher
from telegram_bot.core.router import setup_routers
from telegram_bot.services.text_service import preload_text_blocks
from telegram_bot.services.image_cache import preload_images
from telegram_bot.services.sheets_cache import sync_users_to_db_async
from telegram_bot.app.config import INTERVAL_SYNC

# Настройка базового логгирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PGB_BOT")


async def background_sync():
    """Фоновая задача для синхронизации данных из Google Sheets с базой."""
    while True:
        try:
            logger.info("Начало синхронизации с Google Sheets...")
            # Если force_reload=False, функция load_all_from_sheets сама решит, что делать, исходя из хэша.
            await sync_users_to_db_async(force_reload=False)
            logger.info("Синхронизация успешно завершена.")
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
        await asyncio.sleep(INTERVAL_SYNC)


async def main():
    # Предзагружаем текстовые блоки и изображения
    await preload_text_blocks()
    await preload_images()

    # Запускаем фоновое задание синхронизации
    asyncio.create_task(background_sync())

    # Настраиваем роутеры и запускаем опрос Telegram
    dispatcher.include_router(setup_routers())
    logger.info("🚀 Бот запущен")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔️ Бот остановлен")
