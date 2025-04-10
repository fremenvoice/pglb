from aiogram import Router
from telegram_bot.handlers import start, menu  # добавили menu

def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(menu.router)  # ← подключаем меню
    return router
