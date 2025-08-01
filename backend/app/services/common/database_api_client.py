"""
Database API 클라이언트
database 컨테이너의 API를 호출하는 클라이언트
"""
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseAPIClient:
    """Database API 클라이언트"""
    
    def __init__(self, base_url: str = "http://database:8000"):
        self.base_url = base_url
        self.session = None
    
    async def _get_session(self):
        """aiohttp 세션 생성"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """API 요청 수행"""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.request(method, url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    raise Exception(f"API request failed: {response.status}")
        except Exception as e:
            logger.error(f"Database API request error: {e}")
            raise
    
    async def save_message(
        self,
        session_id: str,
        role: str,
        message_text: str,
        employee_id: int,
        metadata: Optional[Dict] = None
    ) -> str:
        """메시지 저장"""
        data = {
            "session_id": session_id,
            "role": role,
            "message_text": message_text,
            "employee_id": employee_id,
            "metadata": metadata or {}
        }
        
        result = await self._make_request("POST", "/api/chat-history/save-message", data)
        return result["message_id"]
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = 50,
        offset: int = 0
    ) -> List[Dict]:
        """대화 기록 조회"""
        data = {
            "session_id": session_id,
            "limit": limit,
            "offset": offset
        }
        
        result = await self._make_request("POST", "/api/chat-history/get-history", data)
        return result["messages"]
    
    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """세션 정보 조회"""
        data = {
            "session_id": session_id
        }
        
        try:
            result = await self._make_request("POST", "/api/chat-history/get-session-info", data)
            return result["session"]
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return None
    
    async def health_check(self) -> bool:
        """헬스 체크"""
        try:
            result = await self._make_request("GET", "/api/chat-history/health")
            return result["status"] == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def close(self):
        """세션 종료"""
        if self.session:
            await self.session.close()
            self.session = None

# 싱글톤 인스턴스
database_api_client = DatabaseAPIClient() 