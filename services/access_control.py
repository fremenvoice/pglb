from services.db import get_connection

def get_user_role(username: str) -> str | None:
    """
    Возвращает роль пользователя, если он найден и активен.
    Иначе — None.
    """
    if not username:
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT role FROM users
                WHERE username = %s AND is_active = TRUE
            """, (username,))
            result = cur.fetchone()

    return result["role"] if result else None
