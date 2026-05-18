from app.database.db import get_connection


MAX_HISTORY = 6


def save_message(user_id: str, role: str, content: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO history (user_id, role, content)
        VALUES (?, ?, ?)
        """,
        (str(user_id), role, content)
    )

    conn.commit()
    conn.close()


def get_recent_history(user_id: str, limit: int = MAX_HISTORY):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role, content
        FROM history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (str(user_id), limit)
    )

    rows = cur.fetchall()

    conn.close()

    rows = list(reversed(rows))

    return [
        {
            "role": r["role"],
            "content": r["content"]
        }
        for r in rows
    ]


def build_context_text(user_id: str):

    history = get_recent_history(user_id)

    if not history:
        return ""

    parts = []

    for h in history:
        role = h["role"]
        content = h["content"]

        parts.append(f"{role.upper()}: {content}")

    return "\n".join(parts)