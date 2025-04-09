from aiogram import Bot, Dispatcher
from app.config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

async def on_startup():
    print("Бот запущен")

if __name__ == "__main__":
    import asyncio
    asyncio.run(on_startup())
