# telegram_bot/services/sheets_cache.py

import os
import csv
import json
import aiohttp
import asyncio
from io import StringIO

from telegram_bot.services.log_service import setup_logger
from telegram_bot.services.database import get_sync_connection
from telegram_bot.app.config import (
    SPREADSHEET_ID_OPERATORS,
    SPREADSHEET_ID_CONSULTANTS,
    SPREADSHEET_ID_PHONES,
    SPREADSHEET_ID_OPERATORS_RENT,
    GID_OPERATORS,
    GID_CONSULTANTS,
    GID_PHONES,
    GID_OPERATORS_RENT,
)

logger = setup_logger()
USE_SHEETS_CACHE = os.getenv("USE_SHEETS_CACHE", "false").lower() == "true"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "sheets_data.json")
FIXED_ROLES_PATH = os.path.join(os.path.dirname(__file__), "fixed_roles.json")


def load_fixed_roles():
    if not os.path.exists(FIXED_ROLES_PATH):
        logger.warning("⚠️ Файл fixed_roles.json не найден")
        return {}

    with open(FIXED_ROLES_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    logger.info("\n📦 FIXED_ROLES:")
    for username, (fio, role) in raw.items():
        logger.info(f"- {username}: {fio} → {role}")
    return raw


async def fetch_csv(spreadsheet_id: str, gid: int) -> list[list[str]]:
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            csv_text = await response.text(encoding='utf-8')
            reader = csv.reader(StringIO(csv_text))
            return [row for row in reader if row and any(cell.strip() for cell in row)]


async def load_all_from_sheets(force_reload: bool = False) -> dict:
    if USE_SHEETS_CACHE and not force_reload and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                logger.info("💾 Загружаем данные из sheets-кеша")
                return json.load(f)
        except Exception as e:
            logger.warning(f"❌ Ошибка чтения кеша: {e}")

    logger.info("🌐 Загружаем данные из Google Sheets")
    operators = await fetch_csv(SPREADSHEET_ID_OPERATORS, GID_OPERATORS)
    consultants = await fetch_csv(SPREADSHEET_ID_CONSULTANTS, GID_CONSULTANTS)
    phones = await fetch_csv(SPREADSHEET_ID_PHONES, GID_PHONES)
    operators_rent = await fetch_csv(SPREADSHEET_ID_OPERATORS_RENT, GID_OPERATORS_RENT)

    result = {
        "operators": [row[0].strip() for row in operators if row],
        "consultants": [row[0].strip() for row in consultants if row],
        "phones": [
            {"full_name": row[0].strip(), "username": row[2].strip()}
            for row in phones if len(row) >= 3 and row[2].strip()
        ],
        "operators_rent": [
            {"full_name": row[0].strip(), "username": row[3].strip()}
            for row in operators_rent if len(row) >= 4 and row[3].strip()
        ]
    }

    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info("✅ Сохранили sheets-кеш локально")
    except Exception as e:
        logger.warning(f"❌ Не удалось сохранить кеш: {e}")

    return result


async def sync_users_to_db_async(force_reload: bool = False):
    data = await load_all_from_sheets(force_reload=force_reload)
    fixed_roles = load_fixed_roles()

    operator_fios = set(data["operators"])
    consultant_fios = set(data["consultants"])
    operator_rent_fios = {r["full_name"] for r in data["operators_rent"]}
    phone_map = {p["full_name"]: p["username"] for p in data["phones"]}

    for r in data["operators_rent"]:
        phone_map[r["full_name"]] = r["username"]

    for username, (fio, _) in fixed_roles.items():
        phone_map[fio] = username

    logger.info(f"📱 Пользователи: {phone_map}")
    logger.info(f"🏠 Арендаторы: {operator_rent_fios}")

    with get_sync_connection() as conn:
        with conn.cursor() as cur:
            for role in {"operator", "consultant", "admin", "operator_rent"}:
                cur.execute(
                    "INSERT INTO roles (name) VALUES (%s) ON CONFLICT DO NOTHING",
                    (role,)
                )
            conn.commit()

            for fio, username in phone_map.items():
                roles = []

                if username in fixed_roles:
                    roles = [fixed_roles[username][1]]
                else:
                    if fio in operator_fios:
                        roles.append("operator")
                    if fio in consultant_fios:
                        roles.append("consultant")
                    if fio in operator_rent_fios:
                        roles.append("operator_rent")

                if not roles:
                    continue

                logger.info(f"📥 {fio} ({username}) → {roles}")
                cur.execute("""
                    INSERT INTO users (full_name, username)
                    VALUES (%s, %s)
                    ON CONFLICT (username) DO UPDATE SET full_name = EXCLUDED.full_name
                    RETURNING id
                """, (fio, username))
                user_id = cur.fetchone()[0]

                cur.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))
                for role in set(roles):
                    cur.execute("SELECT id FROM roles WHERE name = %s", (role,))
                    res = cur.fetchone()
                    if not res:
                        logger.warning(f"❗ Роль '{role}' не найдена")
                        continue
                    role_id = res[0]
                    cur.execute(
                        "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                        (user_id, role_id)
                    )

        conn.commit()
    logger.info("✅ Синхронизация завершена")


if __name__ == "__main__":
    import sys
    force = "--force-reload" in sys.argv
    asyncio.run(sync_users_to_db_async(force_reload=force))
