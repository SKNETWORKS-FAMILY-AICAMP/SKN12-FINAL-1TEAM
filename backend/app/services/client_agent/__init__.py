"""
Client Agent Module
거래처 및 병원 실적 분석 전문 에이전트
"""
from typing import Dict, Any
from .client_agent import ClientAgent

# 싱글톤 인스턴스 생성
agent = ClientAgent()

async def run(query: str, session_id: str = "default") -> Dict[str, Any]:
    """
    RouterAgent에서 호출하는 표준 인터페이스
    
    Args:
        query: 사용자 쿼리 (예: "우리가족의원 2024년 1월~3월 분석")
        session_id: 세션 ID
        
    Returns:
        분석 결과 딕셔너리
    """
    try:
        # 전체 LangGraph 파이프라인 실행
        result = await agent.run_pipeline_from_query(query)
        
        # RouterAgent가 기대하는 형식으로 변환
        return {
            "success": True,
            "response": result.get("final_report", "분석 결과를 생성하지 못했습니다."),
            "report": result.get("final_report"),
            "agent": "client_agent",
            "session_id": session_id,
            "grade_result": result.get("grade_result"),
            "metadata": {
                "company_name": result.get("company_name"),
                "start_month": result.get("start_month"),
                "end_month": result.get("end_month"),
                "grade": result.get("grade_result", {}).get("최종등급") if result.get("grade_result") else None,
                "analysis_components": {
                    "grade_report": bool(result.get("grade_report")),
                    "same_grade_report": bool(result.get("same_grade_report")),
                    "growth_report": bool(result.get("growth_report")),
                    "strategy_report": bool(result.get("strategy_report"))
                }
            }
        }
    except Exception as e:
        # 에러 처리
        error_message = f"분석 중 오류가 발생했습니다: {str(e)}"
        
        # 간단한 폴백 응답 제공
        if "병원" in query or "의원" in query or "약국" in query:
            fallback_response = f"죄송합니다. {query}에 대한 분석을 수행할 수 없습니다. 데이터를 확인해주세요."
        else:
            fallback_response = "거래처 정보 분석 중 문제가 발생했습니다. 거래처명과 기간을 확인해주세요."
        
        return {
            "success": False,
            "response": fallback_response,
            "error": error_message,
            "agent": "client_agent",
            "session_id": session_id
        }

# 모듈 공개 인터페이스
__all__ = ['agent', 'run', 'ClientAgent']