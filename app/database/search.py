import sqlite3
from app.config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================
# CATEGORY SEARCH (ЖЁСТКАЯ ЛОГИКА)
# =====================================
def search_by_category(category):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, description, website, instagram, facebook
        FROM initiatives
        WHERE category = ?
        LIMIT 5
    """, (category,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# =====================================
# TAG SEARCH
# =====================================
def search_by_tag(query):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, description, website, instagram, facebook
        FROM initiatives
        WHERE tags LIKE ?
        LIMIT 5
    """, (f"%{query}%",))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# =====================================
# MIXED SEARCH (CONTROLLED)
# =====================================
def search_mixed(category=None, query=None):

    print("SEARCH MIXED:", category, query)

    # 1. category priority
    if category:
        results = search_by_category(category)
        if results:
            return results

    # 2. tag fallback
    if query:
        results = search_by_tag(query)
        if results:
            return results

    return []


# =====================================
# BALANCED RANDOM (ВАЖНО)
# =====================================
def random_initiatives(limit=3, category=None):

    conn = get_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("""
            SELECT name, description, website, instagram, facebook
            FROM initiatives
            WHERE category = ?
            ORDER BY RANDOM()
            LIMIT ?
        """, (category, limit))
    else:
        cursor.execute("""
            SELECT name, description, website, instagram, facebook
            FROM initiatives
            ORDER BY RANDOM()
            LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]