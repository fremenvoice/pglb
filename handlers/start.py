from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from domain.text_blocks.about_park import get_about_park_text

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пока нет логики проверки ролей — всегда показываем info блок
    text = get_about_park_text()
    await update.message.reply_text(text, parse_mode="Markdown")

start_handler = CommandHandler("start", start_command)
