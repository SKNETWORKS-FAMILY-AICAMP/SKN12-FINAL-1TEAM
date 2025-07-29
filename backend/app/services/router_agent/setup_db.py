# backend/app/services/router_agent/setup_db.py
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
DB_PATH = os.path.join(BASE_DIR, "database", "history", "memory.sqlite")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # chat_sessions 테이블
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        title TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # chat_messages 테이블
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,
        content TEXT,
        metadata TEXT,
        created_at TEXT,
        FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()
    print(f"✅ DB 초기화 완료: {DB_PATH}")

if __name__ == "__main__":
    init_db()
