import logging
from aiogram import Router
from telegram_bot.handlers import start, menu, qr_scanner

logger = logging.getLogger(__name__)

def setup_routers() -> Router:
    router = Router()

    subrouters = [
        start.router,
        menu.router,
        qr_scanner.router
    ]

    for sub in subrouters:
        router.include_router(sub)
        logger.info(f"🔗 Подключён маршрутизатор: {sub}")

    return router
