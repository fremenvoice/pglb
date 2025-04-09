import csv
import requests
from app.config import (
    SHEET_OPERATORS_ID, SHEET_OPERATORS_GID,
    SHEET_CONSULTANTS_ID, SHEET_CONSULTANTS_GID,
    SHEET_PHONES_ID, SHEET_PHONES_GID
)

def get_csv_url(sheet_id: str, gid: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

def fetch_csv_rows(sheet_id: str, gid: str) -> list[list[str]]:
    url = get_csv_url(sheet_id, gid)
    response = requests.get(url)
    response.raise_for_status()

    decoded = response.content.decode("utf-8")
    reader = csv.reader(decoded.splitlines())
    return list(reader)

def get_fio_list(sheet_id: str, gid: str) -> list[str]:
    rows = fetch_csv_rows(sheet_id, gid)
    return [row[0].strip() for row in rows if row and row[0].strip()]

def get_fio_username_mapping(sheet_id: str, gid: str) -> dict:
    rows = fetch_csv_rows(sheet_id, gid)
    mapping = {}
    for row in rows:
        if len(row) >= 3:
            fio = row[0].strip()
            username = row[2].strip().lstrip("@")
            if fio and username:
                mapping[fio] = username
    return mapping

def get_all_sheet_users() -> list[dict]:
    # 1. Списки ФИО по ролям
    operator_fios = get_fio_list(SHEET_OPERATORS_ID, SHEET_OPERATORS_GID)
    consultant_fios = get_fio_list(SHEET_CONSULTANTS_ID, SHEET_CONSULTANTS_GID)

    # 2. Сопоставление ФИО → username
    fio_to_username = get_fio_username_mapping(SHEET_PHONES_ID, SHEET_PHONES_GID)

    # 3. Собираем пользователей с ФИО и username
    result = []

    for fio in operator_fios:
        username = fio_to_username.get(fio)
        if username:
            result.append({
                "username": username,
                "full_name": fio,
                "role": "operator"
            })

    for fio in consultant_fios:
        username = fio_to_username.get(fio)
        if username:
            result.append({
                "username": username,
                "full_name": fio,
                "role": "consultant"
            })

    return result
