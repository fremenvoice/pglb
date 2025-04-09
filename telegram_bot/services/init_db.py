from services.database import get_connection

def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    username TEXT UNIQUE,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                    PRIMARY KEY (user_id, role_id)
                );
            """)
        conn.commit()

if __name__ == "__main__":
    init_db()
    print("✅ Таблицы успешно созданы.")
