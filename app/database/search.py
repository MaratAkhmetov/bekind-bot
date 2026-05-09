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

    print("FOUND CATEGORY ROWS:", rows)

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


def search_mixed(category=None, query=None):

    print("SEARCH MIXED")
    print("CATEGORY:", category)
    print("QUERY:", query)

    # 1. category search
    if category and category != "unclear":

        results = search_by_category(category)

        if results and len(results) > 0:
            print("RETURNING CATEGORY RESULTS")
            return results

    # 2. tag search fallback
    if query:

        results = search_by_tag(query)

        if results and len(results) > 0:
            print("RETURNING TAG RESULTS")
            return results

    print("NO RESULTS FOUND")

    return []


def random_initiatives(limit=3):

    conn = get_connection()
    cursor = conn.cursor()

    # ✅ CHECK TOTAL RECORDS
    cursor.execute("""
        SELECT COUNT(*)
        FROM initiatives
    """)

    count = cursor.fetchone()[0]

    print("TOTAL INITIATIVES:", count)

    # ✅ RANDOM QUERY
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