import csv
import requests
from io import StringIO

def fetch_csv(spreadsheet_id: str, gid: int) -> list[list[str]]:
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url)
    response.raise_for_status()

    # Пробуем сначала с utf-8-sig, а не просто utf-8
    csv_data = StringIO(response.content.decode("utf-8-sig"))
    reader = csv.reader(csv_data)
    return [row for row in reader if row and any(cell.strip() for cell in row)]
