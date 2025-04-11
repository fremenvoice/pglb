# core/router.py
from aiogram import Router
from telegram_bot.handlers import start, menu, qr_scanner

def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(menu.router)
    router.include_router(qr_scanner.router)
    return router
