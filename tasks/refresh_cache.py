from services.sheets_cache import sync_users_from_sheets

def main():
    print("🔄 Обновление пользователей из Google Sheets...")
    sync_users_from_sheets()
    print("✅ Обновление завершено.")

if __name__ == "__main__":
    main()
