from aiogram import Router
from telegram_bot.handlers import start  # добавим menu, duties позже

def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    return router
