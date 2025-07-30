"""
채팅 히스토리 관리 모듈
세션별 대화 기록을 저장하고 관리합니다.
"""
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import aiosqlite
import sqlite3
import logging

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """채팅 히스토리 관리 클래스"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: 데이터베이스 경로. None이면 기본 경로 사용
        """
        if db_path is None:
            # 기본 경로: backend/chat_history/chat_history.db
            base_dir = Path(__file__).parent.parent.parent
            self.db_path = base_dir / "chat_history" / "chat_history.db"
        else:
            self.db_path = Path(db_path)
            
        # 디렉토리 생성
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 동기 방식으로 초기화 (앱 시작 시)
        self._init_db_sync()
        
    def _init_db_sync(self):
        """동기 방식으로 데이터베이스 초기화"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    message_text TEXT NOT NULL,
                    metadata TEXT,
                    
                    -- 인덱스를 위한 설정
                    INDEX idx_session_id (session_id),
                    INDEX idx_timestamp (timestamp)
                )
            """)
            
            # 세션 정보 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            conn.commit()
            logger.info(f"ChatHistory DB initialized at: {self.db_path}")
    
    async def save_message(
        self, 
        session_id: str, 
        role: str, 
        message_text: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        메시지 저장
        
        Args:
            session_id: 세션 ID
            role: 'user' 또는 'assistant'
            message_text: 메시지 내용
            metadata: 추가 메타데이터 (agent_name, model, etc.)
            
        Returns:
            message_id: 생성된 메시지 ID
        """
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            # 세션이 없으면 생성
            await self._ensure_session_exists(db, session_id)
            
            # 메시지 저장
            await db.execute("""
                INSERT INTO chat_history 
                (session_id, message_id, timestamp, role, message_text, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                message_id,
                timestamp,
                role,
                message_text,
                json.dumps(metadata or {})
            ))
            
            # 세션 last_activity 업데이트
            await db.execute("""
                UPDATE chat_sessions 
                SET last_activity = ? 
                WHERE session_id = ?
            """, (timestamp, session_id))
            
            await db.commit()
            
        logger.info(f"Message saved: session={session_id}, role={role}, id={message_id}")
        return message_id
    
    async def _ensure_session_exists(self, db, session_id: str):
        """세션이 존재하는지 확인하고 없으면 생성"""
        cursor = await db.execute(
            "SELECT session_id FROM chat_sessions WHERE session_id = ?",
            (session_id,)
        )
        result = await cursor.fetchone()
        
        if not result:
            timestamp = datetime.utcnow().isoformat()
            await db.execute("""
                INSERT INTO chat_sessions (session_id, created_at, last_activity, metadata)
                VALUES (?, ?, ?, ?)
            """, (session_id, timestamp, timestamp, "{}"))
    
    async def get_conversation_history(
        self, 
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict]:
        """
        대화 기록 조회
        
        Args:
            session_id: 세션 ID
            limit: 가져올 메시지 수 (None이면 전체)
            offset: 시작 위치
            
        Returns:
            메시지 리스트
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            query = """
                SELECT message_id, timestamp, role, message_text, metadata
                FROM chat_history
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
                
            cursor = await db.execute(query, (session_id,))
            rows = await cursor.fetchall()
            
        messages = []
        for row in rows:
            messages.append({
                "message_id": row[0],
                "timestamp": row[1],
                "role": row[2],
                "content": row[3],
                "metadata": json.loads(row[4])
            })
            
        return messages
    
    async def get_recent_context(
        self, 
        session_id: str, 
        message_count: int = 10
    ) -> List[Dict]:
        """
        최근 대화 컨텍스트 가져오기 (최신 N개)
        
        Args:
            session_id: 세션 ID
            message_count: 가져올 메시지 수
            
        Returns:
            최근 메시지 리스트
        """
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                SELECT message_id, timestamp, role, message_text, metadata
                FROM chat_history
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, message_count))
            
            rows = await cursor.fetchall()
            
        # 시간 순서대로 정렬 (오래된 것부터)
        messages = []
        for row in reversed(rows):
            messages.append({
                "message_id": row[0],
                "timestamp": row[1],
                "role": row[2],
                "content": row[3],
                "metadata": json.loads(row[4])
            })
            
        return messages
    
    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """세션 정보 조회"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                SELECT created_at, last_activity, metadata
                FROM chat_sessions
                WHERE session_id = ?
            """, (session_id,))
            
            row = await cursor.fetchone()
            
        if row:
            return {
                "session_id": session_id,
                "created_at": row[0],
                "last_activity": row[1],
                "metadata": json.loads(row[2])
            }
        return None
    
    async def delete_old_sessions(self, days: int = 30):
        """오래된 세션 삭제"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            # CASCADE로 chat_history도 함께 삭제됨
            await db.execute("""
                DELETE FROM chat_sessions
                WHERE last_activity < ?
            """, (cutoff_str,))
            
            await db.commit()
            
        logger.info(f"Deleted sessions older than {days} days")

# 싱글톤 인스턴스
chat_history_manager = ChatHistoryManager()