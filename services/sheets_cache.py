from services.sheets_connector import get_all_sheet_users
from services.db import get_connection

def get_static_users() -> list[dict]:
    return [
        {"username": "fremen_voice", "role": "creator", "full_name": "Даниил Иванов"},
        {"username": "Unchained7", "role": "admin", "full_name": "Артур Скопин"},
        {"username": "BogdyDogg", "role": "admin", "full_name": "Богдан Колибабчук"},
        {"username": "AdmLetnegoSada2024", "role": "admin", "full_name": "Дежурный администратор"},
        {"username": "Latekaterina85", "role": "admin", "full_name": "Екатерина Латкова"},
        {"username": "milana_andreevna_s", "role": "admin", "full_name": "Милана Суворова"},
        {"username": "Zakolebalas", "role": "admin", "full_name": "Ксения Кудряшова"},
    ]

def sync_users_from_sheets():
    users = get_all_sheet_users() + get_static_users()

    with get_connection() as conn:
        with conn.cursor() as cur:
            for user in users:
                username = user["username"]
                role = user["role"]
                full_name = user.get("full_name", "")

                cur.execute("""
                    INSERT INTO users (username, full_name, role)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (username) DO UPDATE
                    SET full_name = EXCLUDED.full_name,
                        role = EXCLUDED.role,
                        is_active = TRUE
                """, (username, full_name, role))

        conn.commit()
