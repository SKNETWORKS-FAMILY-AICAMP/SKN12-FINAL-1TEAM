import os
import sqlite3
import json
from datetime import datetime

# 📌 절대경로로 DB 위치 지정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(BASE_DIR, "database", "history", "memory.sqlite")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_database():
    """데이터베이스 테이블 초기화"""
    with get_connection() as conn:
        c = conn.cursor()
        
        # 채팅 세션 테이블
        c.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                selected_agent TEXT DEFAULT NULL
            )
        """)
        
        # 기존 테이블에 selected_agent 컬럼 추가 (이미 있으면 무시)
        try:
            c.execute("ALTER TABLE chat_sessions ADD COLUMN selected_agent TEXT DEFAULT NULL")
        except sqlite3.OperationalError:
            # 컬럼이 이미 존재하는 경우
            pass
        
        # 채팅 메시지 테이블
        c.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
            )
        """)
        
        conn.commit()

# 데이터베이스 초기화 실행
init_database()

def add_session(session_id: str):
    now = datetime.now().isoformat()
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR IGNORE INTO chat_sessions (id, title, created_at, updated_at)
                VALUES (?, '', ?, ?)
            """, (session_id, now, now))
            conn.commit()
            print(f"✅ 세션 추가 성공: {session_id}")
    except Exception as e:
        print(f"❌ 세션 추가 실패: {session_id}, 오류: {e}")

def add_message(session_id: str, role: str, content: str, metadata: dict | None = None):
    now = datetime.now().isoformat()
    metadata_json = json.dumps(metadata or {})

    try:
        with get_connection() as conn:
            c = conn.cursor()

            # 메시지 저장
            c.execute("""
                INSERT INTO chat_messages (session_id, role, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, role, content, metadata_json, now))

            # 세션 업데이트
            c.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (now, session_id))

            # 첫 메시지면 title 설정
            if role == "user":
                c.execute("SELECT COUNT(*) FROM chat_messages WHERE session_id = ?", (session_id,))
                if c.fetchone()[0] == 1:
                    c.execute("UPDATE chat_sessions SET title = ? WHERE id = ?", (content[:30], session_id))

            conn.commit()
            print(f"✅ 메시지 추가 성공: {session_id}, {role}, {len(content)}글자")
    except Exception as e:
        print(f"❌ 메시지 추가 실패: {session_id}, {role}, 오류: {e}")

def get_recent_messages(session_id: str, limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT role, content FROM chat_messages
            WHERE session_id = ?
            ORDER BY id DESC LIMIT ?
        """, (session_id, limit))
        rows = c.fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def get_all_messages(session_id: str) -> list[dict]:
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT role, content, metadata, created_at FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))
        rows = c.fetchall()
    return [
        {
            "role": row[0],
            "content": row[1],
            "metadata": json.loads(row[2]) if row[2] else {},
            "created_at": row[3]
        }
        for row in rows
    ]

def get_session_selected_agent(session_id: str) -> str | None:
    """세션의 선택된 에이전트를 조회"""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT selected_agent FROM chat_sessions WHERE id = ?", (session_id,))
            result = c.fetchone()
            
            if result and result[0]:
                print(f"✅ 세션 {session_id}의 선택된 에이전트: {result[0]}")
                return result[0]
            else:
                print(f"📝 세션 {session_id}에 선택된 에이전트 없음")
                return None
                
    except Exception as e:
        print(f"❌ 에이전트 조회 실패: {session_id}, 오류: {e}")
        return None

def set_session_selected_agent(session_id: str, agent_name: str):
    """세션의 선택된 에이전트를 설정"""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE chat_sessions 
                SET selected_agent = ?, updated_at = ?
                WHERE id = ?
            """, (agent_name, datetime.now().isoformat(), session_id))
            conn.commit()
            print(f"✅ 세션 {session_id}의 에이전트 설정: {agent_name}")
            
    except Exception as e:
        print(f"❌ 에이전트 설정 실패: {session_id}, {agent_name}, 오류: {e}")

def clear_session_selected_agent(session_id: str):
    """세션의 선택된 에이전트를 초기화"""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE chat_sessions 
                SET selected_agent = NULL, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), session_id))
            conn.commit()
            print(f"✅ 세션 {session_id}의 에이전트 초기화")
            
    except Exception as e:
        print(f"❌ 에이전트 초기화 실패: {session_id}, 오류: {e}")

def get_all_sessions() -> list[dict]:
    """모든 채팅 세션 목록 조회"""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, title, created_at, updated_at, selected_agent
                FROM chat_sessions 
                ORDER BY updated_at DESC
            """)
            rows = c.fetchall()
            
            sessions = []
            for row in rows:
                sessions.append({
                    "id": row[0],
                    "title": row[1] if row[1] else f"채팅 {row[2][:10]}",
                    "created_at": row[2],
                    "updated_at": row[3],
                    "selected_agent": row[4]
                })
            
            print(f"✅ 세션 목록 조회 성공: {len(sessions)}개")
            return sessions
            
    except Exception as e:
        print(f"❌ 세션 목록 조회 실패: {e}")
        return []

def get_session_messages(session_id: str) -> list[dict]:
    """특정 세션의 모든 메시지 조회"""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT role, content, metadata, created_at 
                FROM chat_messages 
                WHERE session_id = ?
                ORDER BY created_at ASC
            """, (session_id,))
            rows = c.fetchall()
            
            messages = []
            for row in rows:
                # UI 호환 형식으로 변환
                message_type = 'user' if row[0] == 'user' else 'bot'
                if row[1].startswith('안녕하세요! NaruTalk'):
                    message_type = 'system'
                
                messages.append({
                    "type": message_type,
                    "content": row[1],
                    "metadata": json.loads(row[2]) if row[2] else {},
                    "timestamp": row[3][-8:] if len(row[3]) >= 8 else row[3],  # 시간만 추출
                    "agent": json.loads(row[2]).get("agent", "System") if row[2] else "System"
                })
            
            print(f"✅ 메시지 조회 성공: {session_id}, {len(messages)}개")
            return messages
            
    except Exception as e:
        print(f"❌ 메시지 조회 실패: {session_id}, {e}")
        return []
