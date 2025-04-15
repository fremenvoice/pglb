import psycopg2
import logging
from typing import Optional
from functools import lru_cache

from telegram_bot.services.database import get_connection

logger = logging.getLogger(__name__)

@lru_cache(maxsize=256)
def get_user_info(username: str) -> Optional[dict]:
    if not username:
        logger.warning("🛑 Запрос без username")
        return None

    logger.debug(f"🔍 Проверка пользователя: @{username}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, full_name, is_active FROM users WHERE username = %s
            """, (username,))
            row = cur.fetchone()

            if not row:
                logger.info(f"🙅 Пользователь @{username} не найден в базе")
                return None

            user_id, full_name, is_active = row

            cur.execute("""
                SELECT r.name FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = %s
            """, (user_id,))
            roles = [r[0] for r in cur.fetchall()]

            logger.info(f"✅ Пользователь @{username} найден: {full_name} | Роли: {roles}")

            return {
                "full_name": full_name,
                "roles": roles,
                "is_active": is_active
            }


def has_role(username: str, role: str) -> bool:
    info = get_user_info(username)
    result = info is not None and role in info["roles"]
    logger.debug(f"🔑 @{username} has_role('{role}') = {result}")
    return result


def is_authorized(username: str) -> bool:
    info = get_user_info(username)
    result = info is not None and info["is_active"] and len(info["roles"]) > 0
    logger.debug(f"🔐 @{username} is_authorized() = {result}")
    return result
