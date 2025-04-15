# telegram_bot/services/database.py

import os
import logging
import asyncpg
import psycopg2
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 🔄 Асинхронное подключение
async def get_async_connection():
    try:
        conn = await asyncpg.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432)
        )
        logger.debug("⚡ Асинхронное соединение с БД установлено")
        return conn
    except Exception as e:
        logger.exception("❌ Ошибка asyncpg-подключения к базе данных")
        raise

# 🧱 Синхронное подключение (устаревшее, но оставлено)
def get_sync_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432)
        )
        logger.debug("🛢️ Синхронное соединение с БД установлено")
        return conn
    except Exception as e:
        logger.exception("❌ Ошибка psycopg2-подключения к базе данных")
        raise
