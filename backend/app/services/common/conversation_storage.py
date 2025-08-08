"""
대화 저장 시스템
PostgreSQL API (8010 포트)와 연동하여 대화 내역을 저장/조회합니다.
"""
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class ConversationStorage:
    """
    대화 저장 및 조회를 위한 클래스
    PostgreSQL API와 통신하여 대화 내역을 관리합니다.
    """
    
    def __init__(self, base_url: str = "http://localhost:8010", token: Optional[str] = None):
        """
        초기화
        
        Args:
            base_url: PostgreSQL API 주소 (기본값: http://localhost:8010)
            token: JWT 토큰 (선택사항)
        """
        self.base_url = base_url
        self.token = token or os.getenv("CHAT_API_TOKEN")
        self.employee_id = 1  # 기본값 (필요시 변경 가능)
        
    def _get_headers(self) -> Dict[str, str]:
        """인증 헤더 생성"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def save_message(
        self, 
        session_id: str, 
        role: str, 
        message: str,
        employee_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        메시지 저장
        
        Args:
            session_id: 세션 ID
            role: 메시지 역할 ('user' 또는 'assistant')
            message: 메시지 내용
            employee_id: 직원 ID (선택사항)
            
        Returns:
            저장된 메시지 정보 또는 None (실패 시)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat-history/save-message",
                    json={
                        "session_id": session_id,
                        "employee_id": employee_id or self.employee_id,
                        "role": role,
                        "message_text": message
                    },
                    headers=self._get_headers()
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    logger.info(f"메시지 저장 성공: session_id={session_id}, role={role}")
                    return response.json()
                else:
                    logger.warning(f"메시지 저장 실패: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.ConnectError:
            logger.warning(f"PostgreSQL API 연결 실패: {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"메시지 저장 중 오류: {e}")
            return None
    
    async def get_conversation(
        self, 
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        대화 내역 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            메시지 목록 (빈 리스트 반환 시 실패)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat-history/get-history",
                    json={
                        "session_id": session_id,
                        "limit": 50,
                        "offset": 0
                    },
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    messages = result.get("messages", [])
                    logger.info(f"대화 조회 성공: session_id={session_id}, 메시지 수={len(messages)}")
                    return messages
                elif response.status_code == 404:
                    logger.info(f"대화 내역 없음: session_id={session_id}")
                    return []
                else:
                    logger.warning(f"대화 조회 실패: {response.status_code} - {response.text}")
                    return []
                    
        except httpx.ConnectError:
            logger.warning(f"PostgreSQL API 연결 실패: {self.base_url}")
            return []
        except Exception as e:
            logger.error(f"대화 조회 중 오류: {e}")
            return []
    
    async def get_session_info(
        self, 
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        세션 정보 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            세션 정보 또는 None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat-history/get-session-info",
                    json={"session_id": session_id},
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("session") if result.get("success") else None
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"세션 정보 조회 중 오류: {e}")
            return None
    
    async def get_user_sessions(
        self, 
        employee_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        사용자의 모든 세션 목록 조회
        
        Args:
            employee_id: 직원 ID
            
        Returns:
            세션 목록
        """
        try:
            emp_id = employee_id or self.employee_id
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/chat-history/sessions/{emp_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("sessions", []) if result.get("success") else []
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"세션 목록 조회 중 오류: {e}")
            return []
    
    async def update_session_title(
        self, 
        session_id: str, 
        title: str
    ) -> Optional[Dict[str, Any]]:
        """
        세션 제목 업데이트
        
        Args:
            session_id: 세션 ID
            title: 새 제목
            
        Returns:
            업데이트된 세션 정보 또는 None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    f"{self.base_url}/api/chat-history/session/{session_id}/title",
                    json={"session_id": session_id, "title": title},
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"세션 제목 업데이트 중 오류: {e}")
            return None
    
    async def health_check(self) -> bool:
        """
        API 상태 확인
        
        Returns:
            API 정상 작동 여부
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/chat-history/health")
                return response.status_code == 200
        except:
            return False


# 동기 래퍼 함수 (필요시 사용)
def save_message_sync(session_id: str, role: str, message: str) -> Optional[Dict[str, Any]]:
    """동기 방식으로 메시지 저장"""
    import asyncio
    storage = ConversationStorage()
    return asyncio.run(storage.save_message(session_id, role, message))


def get_conversation_sync(session_id: str) -> List[Dict[str, Any]]:
    """동기 방식으로 대화 조회"""
    import asyncio
    storage = ConversationStorage()
    return asyncio.run(storage.get_conversation(session_id))