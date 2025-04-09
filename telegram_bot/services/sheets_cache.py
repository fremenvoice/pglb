import os
import csv
import requests
from io import StringIO

from telegram_bot.services.database import get_connection
from telegram_bot.services.sheets_connector import fetch_csv
from telegram_bot.app.config import (
    SPREADSHEET_ID_OPERATORS,
    SPREADSHEET_ID_CONSULTANTS,
    SPREADSHEET_ID_PHONES,
    GID_OPERATORS,
    GID_CONSULTANTS,
    GID_PHONES,
)

# Фиксированные админы: username -> full_name
FIXED_ADMINS = {
    "fremen_voice": "Даниил Иванов",
    "Unchained7": "Артур Скопин",
    "BogdyDogg": "Богдан Колибабчук",
    "AdmLetnegoSada2024": "Дежурный администратор",
    "Latekaterina85": "Екатерина Латкова",
    "milana_andreevna_s": "Милана Суворова",
    "Zakolebalas": "Ксения Кудряшова",
}


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
    operator_fios = set(data["operators"])
    consultant_fios = set(data["consultants"])
    phone_map = {p["full_name"]: p["username"] for p in data["phones"]}

    # Добавим фиксированных админов, если их нет в таблице
    for username, full_name in FIXED_ADMINS.items():
        if full_name not in phone_map:
            phone_map[full_name] = username

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Убедимся, что роли есть
            for role in ["operator", "consultant", "admin"]:
                cur.execute("INSERT INTO roles (name) VALUES (%s) ON CONFLICT DO NOTHING", (role,))

            # Создание или обновление пользователей
            for fio, username in phone_map.items():
                roles = []

                if fio in operator_fios:
                    roles.append("operator")
                if fio in consultant_fios:
                    roles.append("consultant")
                if username in FIXED_ADMINS:
                    roles.append("admin")

                if not roles:
                    continue  # не подходит по условиям

                # Вставим/обновим пользователя
                cur.execute("""
                    INSERT INTO users (full_name, username)
                    VALUES (%s, %s)
                    ON CONFLICT (username) DO UPDATE SET full_name = EXCLUDED.full_name
                    RETURNING id
                """, (fio, username))
                user_id = cur.fetchone()[0]

                # Очистим старые роли
                cur.execute("DELETE FROM user_roles WHERE user_id = %s", (user_id,))

                # Назначим роли
                for role in roles:
                    cur.execute("SELECT id FROM roles WHERE name = %s", (role,))
                    role_id = cur.fetchone()[0]
                    cur.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_id))

        conn.commit()
    print("✅ Пользователи синхронизированы с БД.")


if __name__ == "__main__":
    sync_users_to_db()
