from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.start import start_command  # Импортируем start_command из handlers/start.py
from handlers.menu import start_work, back_to_roles  # Импортируем обработчики из handlers/menu.py
from app.config import BOT_TOKEN
from services.db import ensure_tables_exist
from services.sheets_cache import sync_users_from_sheets

def main():
    # 🧱 Гарантируем, что таблицы созданы
    ensure_tables_exist()

    # 🔄 Синхронизируем пользователей из Google Sheets
    sync_users_from_sheets()

    # 🚀 Инициализация приложения
    app = Application.builder().token(BOT_TOKEN).build()

    # Привязываем обработчики
    app.add_handler(CommandHandler("start", start_command))  # Обработчик команды /start
    app.add_handler(CallbackQueryHandler(start_work, pattern="start_work"))  # Обработчик кнопки "Приступить к работе!"
    app.add_handler(CallbackQueryHandler(back_to_roles, pattern="back_to_roles"))  # Обработчик кнопки "🔁 На экран приветствия"

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
