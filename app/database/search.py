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

    words = query.lower().split()

    conditions = []
    values = []

    for word in words:
        conditions.append("LOWER(tags) LIKE ?")
        values.append(f"%{word}%")

    sql = f"""
        SELECT
            name,
            description,
            website,
            instagram,
            facebook
        FROM initiatives
        WHERE {" OR ".join(conditions)}
        LIMIT 5
    """

    cursor.execute(sql, values)

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


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