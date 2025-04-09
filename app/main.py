from telegram.ext import ApplicationBuilder
from handlers.start import start_handler
from app.config import BOT_TOKEN

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(start_handler)

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
