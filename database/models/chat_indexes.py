"""
채팅 관련 테이블의 인덱스 정의
"""
from sqlalchemy import Index, Text

# ChatHistory 테이블 인덱스
def create_chat_history_indexes():
    """ChatHistory 테이블의 인덱스 생성"""
    indexes = [
        # 세션별 메시지 조회를 위한 인덱스
        Index('idx_chat_history_session_id', 'session_id'),
        
        # 시간순 정렬을 위한 인덱스
        Index('idx_chat_history_created_at', 'created_at'),
        
        # 직원별 메시지 조회를 위한 인덱스
        Index('idx_chat_history_employee_id', 'employee_id'),
        
        # 역할별 메시지 조회를 위한 인덱스
        Index('idx_chat_history_role', 'role'),
        
        # 복합 인덱스: 세션 + 시간
        Index('idx_chat_history_session_created', 'session_id', 'created_at'),
        
        # 복합 인덱스: 직원 + 시간
        Index('idx_chat_history_employee_created', 'employee_id', 'created_at'),
        
        # 만료 시간 인덱스 (TTL 정리를 위한)
        Index('idx_chat_history_expires_at', 'expires_at'),
    ]
    return indexes

# ChatSession 테이블 인덱스
def create_chat_session_indexes():
    """ChatSession 테이블의 인덱스 생성"""
    indexes = [
        # 직원별 세션 조회를 위한 인덱스
        Index('idx_chat_session_employee_id', 'employee_id'),
        
        # 상태별 세션 조회를 위한 인덱스
        Index('idx_chat_session_status', 'session_status'),
        
        # 마지막 활동 시간 인덱스
        Index('idx_chat_session_last_activity', 'last_activity'),
        
        # 복합 인덱스: 직원 + 상태
        Index('idx_chat_session_employee_status', 'employee_id', 'session_status'),
        
        # 복합 인덱스: 직원 + 마지막 활동
        Index('idx_chat_session_employee_activity', 'employee_id', 'last_activity'),
    ]
    return indexes 