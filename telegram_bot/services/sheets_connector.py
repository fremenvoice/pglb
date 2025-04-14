import csv
import aiohttp
import asyncio
from io import StringIO

async def fetch_csv(spreadsheet_id: str, gid: int) -> list[list[str]]:
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.read()
            csv_data = StringIO(content.decode("utf-8-sig"))
            reader = csv.reader(csv_data)
            return [row for row in reader if row and any(cell.strip() for cell in row)]
