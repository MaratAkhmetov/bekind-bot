from app.database.db import get_connection


def search_by_category(category: str):
    conn = get_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM initiatives
        WHERE LOWER(category) = LOWER(?)
        LIMIT 10
    """, (category,))

    results = cursor.fetchall()
    conn.close()
    return results


def search_by_tag(query: str):
    conn = get_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    query = f"%{query.lower()}%"

    cursor.execute("""
        SELECT * FROM initiatives
        WHERE LOWER(tags) LIKE ?
           OR LOWER(name) LIKE ?
           OR LOWER(description) LIKE ?
        LIMIT 10
    """, (query, query, query))

    results = cursor.fetchall()
    conn.close()
    return results


def search_mixed(query: str):
    conn = get_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    query = f"%{query.lower()}%"

    cursor.execute("""
        SELECT *,
        (
            CASE
                WHEN LOWER(name) LIKE ? THEN 3
                WHEN LOWER(tags) LIKE ? THEN 2
                WHEN LOWER(description) LIKE ? THEN 1
                ELSE 0
            END
        ) as score
        FROM initiatives
        WHERE score > 0
        ORDER BY score DESC
        LIMIT 10
    """, (query, query, query))

    results = cursor.fetchall()
    conn.close()
    return results


def random_initiatives(limit: int = 3):
    conn = get_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM initiatives
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))

    results = cursor.fetchall()
    conn.close()
    return results


def smart_search(category=None, query=None):
    if category:
        return search_by_category(category)

    if query:
        return search_mixed(query)

    return random_initiatives()


def dict_factory(cursor, row):
    """Return dict instead of tuple"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d