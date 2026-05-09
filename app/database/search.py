from app.database.db import get_connection


def search_by_category(category: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM initiatives
        WHERE category = ?
        LIMIT 10
    """, (category,))

    results = cursor.fetchall()
    conn.close()
    return results


def search_by_tag(query: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM initiatives
        WHERE tags LIKE ?
        LIMIT 10
    """, (f"%{query}%",))

    results = cursor.fetchall()
    conn.close()
    return results


def random_initiatives(limit: int = 3):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM initiatives
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))

    results = cursor.fetchall()
    conn.close()
    return results


# 🔥 NEW: smarter hybrid search (ВАЖНО)
def search_mixed(category=None, query=None):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT * FROM initiatives
        WHERE 1=1
    """

    params = []

    if category and category != "unclear":
        sql += " AND category = ?"
        params.append(category)

    if query:
        sql += " AND tags LIKE ?"
        params.append(f"%{query}%")

    sql += " LIMIT 10"

    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()

    return results