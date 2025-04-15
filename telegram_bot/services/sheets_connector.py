# telegram_bot/services/sheets_connector.py

import csv
import aiohttp
import asyncio
import logging
from io import StringIO

logger = logging.getLogger(__name__)


async def fetch_csv(spreadsheet_id: str, gid: int) -> list[list[str]]:
    """
    Загружает CSV из Google Sheets по ID и GID таблицы.

    :param spreadsheet_id: ID таблицы Google Sheets
    :param gid: GID листа
    :return: Список строк (каждая строка — список ячеек)
    """
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    logger.info(f"📡 Запрос данных с Google Sheets: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                csv_data = StringIO(content.decode("utf-8-sig"))
                reader = csv.reader(csv_data)
                rows = [row for row in reader if row and any(cell.strip() for cell in row)]
                logger.info(f"✅ Получено {len(rows)} строк из GID={gid}")
                return rows
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке CSV из Google Sheets: {e}")
        return []

# Для отладки вручную
if __name__ == "__main__":
    async def main():
        test_id = "your_spreadsheet_id"
        test_gid = 0
        rows = await fetch_csv(test_id, test_gid)
        for row in rows:
            print(row)

    asyncio.run(main())
