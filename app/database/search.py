import sqlite3
from app.config import DATABASE_PATH


def get_connection():

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# =====================================
# CATEGORY SEARCH
# =====================================

def search_by_category(category):

    conn = get_connection()
    cursor = conn.cursor()

    print("SEARCH CATEGORY:", category)

    cursor.execute("""
        SELECT
            name,
            description,
            website,
            instagram,
            facebook
        FROM initiatives
        WHERE category = ?
        COLLATE NOCASE
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

    print("SEARCH TAG:", query)

    keywords = query.split()

    results = []

    for word in keywords:

        cursor.execute("""
            SELECT
                name,
                description,
                website,
                instagram,
                facebook
            FROM initiatives
            WHERE LOWER(tags) LIKE LOWER(?)
            LIMIT 5
        """, (f"%{word}%",))

        rows = cursor.fetchall()

        for row in rows:
            item = dict(row)

            # avoid duplicates
            if item not in results:
                results.append(item)

    conn.close()

    return results[:5]


# =====================================
# MIXED SEARCH
# =====================================

def search_mixed(category=None, query=None):

    print("SEARCH MIXED:", category, query)

    # =====================================
    # 1. CATEGORY PRIORITY
    # =====================================

    if category:

        results = search_by_category(category)

        if results:
            print("CATEGORY RESULTS FOUND")
            return results

    # =====================================
    # 2. TAG FALLBACK
    # =====================================

    if query:

        results = search_by_tag(query)

        if results:
            print("TAG RESULTS FOUND")
            return results

    print("NO RESULTS FOUND")

    return []


# =====================================
# RANDOM BALANCED
# =====================================

def random_initiatives():

    conn = get_connection()
    cursor = conn.cursor()

    categories = [
        "Animals",
        "Environment",
        "Community"
    ]

    results = []

    for category in categories:

        cursor.execute("""
            SELECT
                name,
                description,
                website,
                instagram,
                facebook
            FROM initiatives
            WHERE category = ?
            ORDER BY RANDOM()
            LIMIT 1
        """, (category,))

        row = cursor.fetchone()

        if row:
            results.append(dict(row))

    conn.close()

    return results