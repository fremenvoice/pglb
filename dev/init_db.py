from services.db import ensure_tables_exist

def main():
    ensure_tables_exist()
    print("✅ Таблица users создана (если её не было)")

if __name__ == "__main__":
    main()
