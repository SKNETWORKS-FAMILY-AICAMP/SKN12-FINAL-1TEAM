"""
Employee Agent Run Module
"""
from typing import Dict, Any

async def run(query: str, session_id: str) -> Dict[str, Any]:
    """직원 관련 쿼리 처리"""
    
    # 간단한 키워드 분석
    query_lower = query.lower()
    
    # 구체적인 응답 생성
    if "실적" in query_lower:
        if "김철수" in query:
            response = "김철수 사원의 실적 분석:\n- 2024년 상반기 매출: 3억 2천만원\n- 전년 대비: +15.3%\n- 주요 거래처: A병원(40%), B약국(35%)\n- 평가등급: A"
        else:
            response = f"직원 실적 조회를 위해 구체적인 직원명을 입력해주세요.\n현재 조회: '{query}'"
    elif "평가" in query_lower:
        response = f"직원 평가 조회:\n- 평가 기준: 매출실적(40%), 고객만족도(30%), 업무태도(30%)\n- 평가 주기: 분기별\n- 요청사항: {query}"
    elif "조직도" in query_lower:
        response = "영업본부 조직도:\n├─ 영업1팀 (팀장: 박영수)\n│  ├─ 김철수 과장\n│  └─ 이영희 대리\n└─ 영업2팀 (팀장: 최민수)\n   ├─ 정대호 과장\n   └─ 강미나 대리"
    else:
        response = f"직원 정보를 조회합니다.\n요청사항: {query}\n\n구체적인 직원명이나 부서명을 입력하시면 더 상세한 정보를 제공할 수 있습니다."
    
    return {
        "success": True,
        "response": response,
        "report": response,
        "agent": "employee_agent",
        "session_id": session_id
    }