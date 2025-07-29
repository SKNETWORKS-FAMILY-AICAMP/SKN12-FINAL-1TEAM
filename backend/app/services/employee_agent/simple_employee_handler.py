"""
Simple Employee Handler

직원 실적 분석을 위한 간단한 핸들러 (연결 확인용)
"""

from typing import Dict, Any
from datetime import datetime

async def process_employee_request(query: str, session_id: str = None) -> Dict[str, Any]:
    """
    직원 분석 요청 처리 (연결 확인용)
    
    Args:
        query: 사용자 쿼리
        session_id: 세션 ID
        
    Returns:
        처리 결과 딕셔너리
    """
    
    # 현재는 연결 확인용 메시지만 반환
    system_message = f"""📊 **Employee Agent에 연결되었습니다!**

🔗 **연결 정보:**
- 에이전트: Employee Agent (직원 실적 분석)
- 입력값: "{query}"
- 세션 ID: {session_id or 'None'}
- 현재 상태: 연결 완료
- 처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 **LLM 선택 이유:**
사용자의 쿼리에서 직원, 실적, 성과, 평가, 인사 등의 키워드가 감지되어 
직원 실적 분석 전문 에이전트로 라우팅되었습니다.

📈 **에이전트 기능:**
- 직원별 실적 분석 및 평가
- 성과 트렌드 분석
- 목표 달성률 계산
- 종합 평가 보고서 생성
- 개선 방안 제시

⚙️ **현재 상태:** 기본 연결 테스트 모드
🔧 **다음 단계:** 실제 분석 엔진 연동 예정"""

    return {
        "success": True,
        "agent": "employee_agent",
        "response": system_message,
        "stage": "connected",
        "employee_name": "연결 확인",
        "period": "테스트 모드",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    } 