# telegram_bot/services/access_control.py

import logging
import time
from typing import Optional
from telegram_bot.services.database import get_async_connection

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 30
_user_cache: dict[str, tuple[float, dict]] = {}  # username -> (timestamp, data)


async def get_user_info(username: str) -> Optional[dict]:
    """
    Асинхронно возвращает информацию о пользователе с кешированием.
    """
    if not username:
        logger.warning("🛑 Запрос без username")
        return None

    now = time.time()
    cached = _user_cache.get(username)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        logger.debug(f"⚡ Данные пользователя @{username} из кеша")
        return cached[1]

    logger.debug(f"🔍 Запрос к БД о пользователе @{username}")

    conn = await get_async_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id, full_name, is_active FROM users WHERE username = $1", username
        )
        if not row:
            logger.info(f"🙅 Пользователь @{username} не найден")
            return None

        roles = await conn.fetch(
            """
            SELECT r.name FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = $1
            """,
            row["id"]
        )
        role_names = [r["name"] for r in roles]

        result = {
            "full_name": row["full_name"],
            "roles": role_names,
            "is_active": row["is_active"]
        }

        logger.info(f"✅ Пользователь @{username} найден: {row['full_name']} | Роли: {role_names}")
        _user_cache[username] = (now, result)
        return result
    finally:
        await conn.close()


def clear_user_info_cache():
    """
    Ручной сброс кеша пользователей.
    """
    _user_cache.clear()
    logger.info("🧹 Кеш user_info сброшен вручную")


async def has_role(username: str, role: str) -> bool:
    info = await get_user_info(username)
    result = info is not None and role in info["roles"]
    logger.debug(f"🔑 @{username} has_role('{role}') = {result}")
    return result


async def is_authorized(username: str) -> bool:
    info = await get_user_info(username)
    result = info is not None and info["is_active"] and len(info["roles"]) > 0
    logger.debug(f"🔐 @{username} is_authorized() = {result}")
    return result
