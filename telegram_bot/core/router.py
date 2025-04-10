from aiogram import Router

from telegram_bot.handlers import start, menu, admin_menu

def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(menu.router)
    router.include_router(admin_menu.router)  # ← подключаем
    return router
