import sqlite3
from app.config import DATABASE_PATH


def get_connection():
    print("DB PATH:", DATABASE_PATH)
    return sqlite3.connect(DATABASE_PATH)


def search_by_category(category):

    conn = get_connection()
    cursor = conn.cursor()

    print("SEARCH CATEGORY:", category)

    cursor.execute("""
        SELECT name, description
        FROM initiatives
        WHERE category = ?
        LIMIT 5
    """, (category,))

    rows = cursor.fetchall()

    print("FOUND ROWS:", rows)

    conn.close()

    return [
        {
            "name": row[0],
            "description": row[1]
        }
        for row in rows
    ]


def search_by_tag(query):

    conn = get_connection()
    cursor = conn.cursor()

    print("SEARCH TAG:", query)

    cursor.execute("""
        SELECT name, description
        FROM initiatives
        WHERE tags LIKE ?
        LIMIT 5
    """, (f"%{query}%",))

    rows = cursor.fetchall()

    print("FOUND TAG ROWS:", rows)

    conn.close()

    return [
        {
            "name": row[0],
            "description": row[1]
        }
        for row in rows
    ]


def random_initiatives(limit=3):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, description
        FROM initiatives
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    print("RANDOM ROWS:", rows)

    conn.close()

    return [
        {
            "name": row[0],
            "description": row[1]
        }
        for row in rows
    ]