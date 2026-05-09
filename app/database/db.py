import sqlite3
from app.config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # важно: доступ по имени поля
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS initiatives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        category TEXT NOT NULL,
        -- animals / ecology / people / community / education / homeless / elderly

        tags TEXT,
        -- keyword-based search fallback

        help_types TEXT,
        -- volunteering, money, awareness, logistics

        practical_help TEXT,
        -- WHAT USER CAN ACTUALLY DO (critical field)

        website TEXT,
        instagram TEXT,
        facebook TEXT,

        description TEXT,
                         
        city TEXT,
        source TEXT,  

        activity_status TEXT DEFAULT 'active'
    );

    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        query TEXT,
        answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        rating INTEGER,
        comment TEXT
    );
    """)

    conn.commit()
    conn.close()