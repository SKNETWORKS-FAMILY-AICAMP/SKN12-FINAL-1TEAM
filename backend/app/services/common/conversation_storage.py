"""
대화 저장 시스템
Docker PostgreSQL API (8010 포트)와 연동하여 대화 내역을 저장/조회합니다.

주요 기능:
1. 메시지 저장 (save_message, save_message_sync)
2. 대화 내역 조회 (get_conversation)
3. 세션 정보 관리 (get_session_info, update_session_title, delete_session)
4. 사용자별 세션 목록 조회 (get_user_sessions)

사용 예시:
    # 비동기 사용
    storage = ConversationStorage()
    await storage.save_message(session_id, "user", "안녕하세요")
    
    # 동기 사용 (router.py에서 사용)
    save_message_sync(session_id, "user", "안녕하세요")
"""
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import os

# 중앙 설정 import
from app.core.config import config

logger = logging.getLogger(__name__)


class ConversationStorage:
    """
    대화 저장 및 조회를 위한 클래스
    PostgreSQL API와 통신하여 대화 내역을 관리합니다.
    """
    
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        """
        초기화
        
        Args:
            base_url: PostgreSQL API 주소 (None이면 config에서 가져옴)
            token: JWT 토큰 (선택사항)
        """
        self.base_url = base_url or config.get_database_api_url()
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
    
    async def delete_session(
        self,
        session_id: str,
        employee_id: Optional[int] = None
    ) -> bool:
        """
        세션 삭제
        
        Args:
            session_id: 세션 ID
            employee_id: 직원 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            emp_id = employee_id or self.employee_id
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    f"{self.base_url}/api/chat-history/session/{session_id}",
                    params={"employee_id": emp_id},
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    logger.info(f"세션 삭제 성공: session_id={session_id}")
                    return True
                else:
                    logger.warning(f"세션 삭제 실패: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"세션 삭제 중 오류: {e}")
            return False
    
    async def delete_message(
        self,
        session_id: str,
        message_index: int,
        employee_id: Optional[int] = None
    ) -> bool:
        """
        특정 메시지 삭제
        PostgreSQL API가 개별 메시지 삭제를 지원하지 않으므로
        전체 메시지를 가져와서 필터링 후 재저장하는 방식 사용
        
        Args:
            session_id: 세션 ID
            message_index: 메시지 인덱스 (0부터 시작)
            employee_id: 직원 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            emp_id = employee_id or self.employee_id
            
            # 1. 현재 대화 내역을 가져옴
            messages = await self.get_conversation(session_id)
            
            if not messages or message_index < 0 or message_index >= len(messages):
                logger.warning(f"메시지를 찾을 수 없음: session_id={session_id}, index={message_index}")
                return False
            
            # 2. 세션 정보 저장 (제목 등)
            session_info = await self.get_session_info(session_id)
            session_title = session_info.get('session_title', '') if session_info else ''
            
            # 3. 삭제할 메시지를 제외한 메시지들
            remaining_messages = [msg for i, msg in enumerate(messages) if i != message_index]
            
            # 메시지가 하나도 남지 않으면 세션 전체 삭제
            if not remaining_messages:
                return await self.delete_session(session_id, emp_id)
            
            # 4. 기존 세션 삭제 (포스트맨 코드처럼 DELETE 사용)
            delete_success = await self.delete_session(session_id, emp_id)
            if not delete_success:
                logger.error(f"세션 삭제 실패: session_id={session_id}")
                return False
            
            # 5. 남은 메시지들을 다시 저장
            for msg in remaining_messages:
                save_result = await self.save_message(
                    session_id=session_id,
                    role=msg.get('role', 'user'),
                    message=msg.get('message_text', msg.get('content', msg.get('message', ''))),
                    employee_id=emp_id
                )
                if not save_result:
                    logger.error(f"메시지 재저장 실패: session_id={session_id}")
                    return False
            
            # 6. 세션 제목 복원
            if session_title:
                await self.update_session_title(session_id, session_title)
            
            logger.info(f"메시지 삭제 성공: session_id={session_id}, index={message_index}, 남은 메시지={len(remaining_messages)}")
            return True
                    
        except Exception as e:
            logger.error(f"메시지 삭제 중 오류: {e}")
            return False
    
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
def save_message_sync(session_id: str, role: str, message: str, employee_id: int = 1) -> Optional[Dict[str, Any]]:
    """동기 방식으로 메시지 저장 - httpx 동기 클라이언트 사용"""
    import httpx
    import logging
    
    logger = logging.getLogger(__name__)
    base_url = config.get_database_api_url()
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{base_url}/api/chat-history/save-message",
                json={
                    "session_id": session_id,
                    "employee_id": employee_id,
                    "role": role,
                    "message_text": message
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"메시지 저장 성공 (동기): session_id={session_id}, role={role}")
                return response.json()
            else:
                logger.warning(f"메시지 저장 실패 (동기): {response.status_code} - {response.text}")
                return None
                
    except httpx.ConnectError:
        logger.warning(f"PostgreSQL API 연결 실패 (동기): {base_url}")
        return None
    except Exception as e:
        logger.error(f"메시지 저장 중 오류 (동기): {e}")
        return None


def get_conversation_sync(session_id: str) -> List[Dict[str, Any]]:
    """동기 방식으로 대화 조회"""
    import asyncio
    storage = ConversationStorage()
    return asyncio.run(storage.get_conversation(session_id))