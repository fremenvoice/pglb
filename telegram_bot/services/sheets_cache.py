import sys
import os
import csv
import json
import logging
import requests
from io import StringIO

from telegram_bot.services.database import get_connection

from telegram_bot.app.config import (
    SPREADSHEET_ID_OPERATORS,
    SPREADSHEET_ID_CONSULTANTS,
    SPREADSHEET_ID_PHONES,
    GID_OPERATORS,
    GID_CONSULTANTS,
    GID_PHONES,
)

logger = logging.getLogger(__name__)
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

def fetch_csv(spreadsheet_id: str, gid: int) -> list[list[str]]:
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url)
    response.raise_for_status()

    csv_data = StringIO(response.text)
    reader = csv.reader(csv_data)
    return [row for row in reader if row and any(cell.strip() for cell in row)]

def load_all_from_sheets():
    operators = fetch_csv(SPREADSHEET_ID_OPERATORS, GID_OPERATORS)
    consultants = fetch_csv(SPREADSHEET_ID_CONSULTANTS, GID_CONSULTANTS)
    phones = fetch_csv(SPREADSHEET_ID_PHONES, GID_PHONES)

    return {
        "operators": [row[0].strip() for row in operators if row],
        "consultants": [row[0].strip() for row in consultants if row],
        "phones": [
            {"full_name": row[0].strip(), "username": row[2].strip()}
            for row in phones if len(row) >= 3 and row[2].strip()
        ]
    }

def sync_users_to_db():
    data = load_all_from_sheets()
    fixed_roles = load_fixed_roles()

    operator_fios = set(data["operators"])
    consultant_fios = set(data["consultants"])
    phone_map = {p["full_name"]: p["username"] for p in data["phones"]}

    for username, (fio, _) in fixed_roles.items():
        phone_map[fio] = username  # гарантируем наличие username → full_name

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Убедимся, что роли существуют
            for role in {"operator", "consultant", "admin"}:
                cur.execute("INSERT INTO roles (name) VALUES (%s) ON CONFLICT DO NOTHING", (role,))

            conn.commit()  # 🔥 обязательно до использования ролей

            for fio, username in phone_map.items():
                roles = []

                if username in fixed_roles:
                    fixed_role = fixed_roles[username][1]
                    roles = [fixed_role]
                else:
                    if fio in operator_fios:
                        roles.append("operator")
                    if fio in consultant_fios:
                        roles.append("consultant")

                if not roles:
                    continue

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
                    role_id = cur.fetchone()[0]
                    cur.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_id))

        conn.commit()
    logger.info("✅ Пользователи синхронизированы с БД.")

if __name__ == "__main__":
    sync_users_to_db()