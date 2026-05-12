import sqlite3
from app.config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================
# EXCLUDE FRAGMENT HELPER
# =====================================

def _exclude_fragment(exclude_names):
    exclude_names = [n for n in (exclude_names or []) if n]
    if not exclude_names:
        return "", []
    placeholders = ",".join("?" * len(exclude_names))
    return f" AND name NOT IN ({placeholders})", exclude_names


# =====================================
# CATEGORY SEARCH
# =====================================

def search_by_category(category, exclude_names=None):
    conn = get_connection()
    cursor = conn.cursor()

    print("SEARCH CATEGORY:", category)

    clause, vals = _exclude_fragment(exclude_names)

    sql = f"""
        SELECT
            name,
            description,
            tags,
            help_types,
            practical_help,
            website,
            instagram,
            facebook
        FROM initiatives
        WHERE category = ?
        COLLATE NOCASE
        {clause}
        ORDER BY RANDOM()
        LIMIT 5
    """

    cursor.execute(sql, (category, *vals))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# =====================================
# TAG SEARCH
# =====================================

def search_by_tag(query, exclude_names=None):
    conn = get_connection()
    cursor = conn.cursor()

    words = query.lower().split()
    conditions = []
    values = []

    for word in words:
        conditions.append("LOWER(tags) LIKE ?")
        values.append(f"%{word}%")

    clause, vals = _exclude_fragment(exclude_names)

    sql = f"""
        SELECT
            name,
            description,
            tags,
            help_types,
            practical_help,
            website,
            instagram,
            facebook
        FROM initiatives
        WHERE {" OR ".join(conditions)}
        {clause}
        ORDER BY RANDOM()
        LIMIT 5
    """

    cursor.execute(sql, [*values, *vals])
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# =====================================
# MIXED SEARCH
# =====================================

def search_mixed(category=None, query=None, exclude_names=None):

    print("SEARCH MIXED:", category, query)

    # =====================================
    # 1. CATEGORY PRIORITY
    # =====================================

    if category:
        results = search_by_category(category, exclude_names=exclude_names)
        if results:
            print("CATEGORY RESULTS FOUND")
            return results

    # =====================================
    # 2. TAG FALLBACK
    # =====================================

    if query:
        results = search_by_tag(query, exclude_names=exclude_names)
        if results:
            print("TAG RESULTS FOUND")
            return results

    print("NO RESULTS FOUND")
    return []


# =====================================
# RANDOM BALANCED
# =====================================

def random_initiatives(limit=3, category=None, exclude_names=None):
    conn = get_connection()
    cursor = conn.cursor()

    results = []

    clause, vals = _exclude_fragment(exclude_names)

    if category:
        sql = f"""
            SELECT
                name,
                description,
                tags,
                help_types,
                practical_help,
                website,
                instagram,
                facebook
            FROM initiatives
            WHERE category = ?
            {clause}
            ORDER BY RANDOM()
            LIMIT ?
        """
        cursor.execute(sql, (category, *vals, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # fallback mixed
    categories = ["Animals", "Environment", "Community"]
    for cat in categories:
        sql = f"""
            SELECT
                name,
                description,
                tags,
                help_types,
                practical_help,
                website,
                instagram,
                facebook
            FROM initiatives
            WHERE category = ?
            {clause}
            ORDER BY RANDOM()
            LIMIT 1
        """
        cursor.execute(sql, (cat, *vals))
        row = cursor.fetchone()
        if row:
            results.append(dict(row))

    conn.close()
    return results