"""
QA Medical Agent Main Module
LangGraph 0.5+ compatible StateGraph implementation
"""

import os
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from .utils import (
    AgentState,
    extract_user_query,
    classify_intent,
    search_documents,
    enhance_context,
    generate_response,
    validate_response,
    format_final_output,
    search_medical_documents,
    get_medical_industry_context,
    validate_medical_response,
    format_medical_response
)


def should_continue(state: AgentState) -> str:
    """
    워크플로우 분기 조건 함수
    """
    # 오류가 있는 경우 종료
    if state.get("error"):
        return "end"
    
    # 검색 결과가 없는 경우 컨텍스트 향상 건너뛰기
    search_results = state.get("search_results", [])
    if not search_results:
        return "generate_response"
    
    # 정상적인 플로우 계속
    return "continue"


def needs_validation(state: AgentState) -> str:
    """
    검증 필요 여부 판단
    """
    confidence_score = state.get("confidence_score", 0.0)
    
    # 신뢰도가 낮은 경우 검증 수행
    if confidence_score < 0.7:
        return "validate"
    
    # 높은 신뢰도의 경우 바로 포맷팅
    return "format"


def create_graph() -> StateGraph:
    """
    LangGraph 0.5+ StateGraph 생성
    
    Returns:
        StateGraph: 컴파일된 의료업계 QA 워크플로우
    """
    
    # StateGraph 초기화
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("extract_query", extract_user_query)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("search_documents", search_documents)
    workflow.add_node("enhance_context", enhance_context)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("validate_response", validate_response)
    workflow.add_node("format_output", format_final_output)
    
    # 시작점 설정
    workflow.add_edge(START, "extract_query")
    
    # 순차 실행 경로
    workflow.add_edge("extract_query", "classify_intent")
    workflow.add_edge("classify_intent", "search_documents")
    
    # 조건부 분기: 검색 결과에 따라 다른 경로
    workflow.add_conditional_edges(
        "search_documents",
        should_continue,
        {
            "continue": "enhance_context",
            "generate_response": "generate_response",
            "end": END
        }
    )
    
    workflow.add_edge("enhance_context", "generate_response")
    
    # 조건부 분기: 신뢰도에 따라 검증 여부 결정
    workflow.add_conditional_edges(
        "generate_response",
        needs_validation,
        {
            "validate": "validate_response",
            "format": "format_output"
        }
    )
    
    workflow.add_edge("validate_response", "format_output")
    
    # 종료점 설정
    workflow.add_edge("format_output", END)
    
    # 그래프 컴파일
    return workflow.compile()


def run_agent(
    query: str,
    user_id: str = "default_user",
    session_id: str = "default_session"
) -> Dict[str, Any]:
    """
    QA 에이전트 실행 함수
    
    Args:
        query: 사용자 질의
        user_id: 사용자 ID
        session_id: 세션 ID
        
    Returns:
        Dict[str, Any]: 에이전트 실행 결과
    """
    try:
        # 그래프 생성
        app = create_graph()
        
        # 초기 상태 설정
        initial_state = AgentState(
            messages=[HumanMessage(content=query)],
            user_query=query,
            intent=None,
            search_results=[],
            enhanced_context=None,
            final_response=None,
            confidence_score=None,
            metadata={
                "user_id": user_id,
                "session_id": session_id,
                "start_time": "2024-01-01T00:00:00Z",
                "workflow_version": "1.0"
            },
            error=None
        )
        
        # 그래프 실행
        final_state = app.invoke(initial_state)
        
        # 결과 반환
        return {
            "success": True,
            "query": query,
            "response": final_state.get("final_response", {}),
            "confidence": final_state.get("confidence_score", 0.0),
            "metadata": final_state.get("metadata", {}),
            "messages": [
                {
                    "role": "assistant" if isinstance(msg, AIMessage) else "user",
                    "content": msg.content
                }
                for msg in final_state.get("messages", [])
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "response": {
                "answer": "죄송합니다. 시스템 오류가 발생했습니다.",
                "summary": "오류 발생",
                "recommendations": [],
                "confidence": 0.0,
                "sources": []
            },
            "confidence": 0.0,
            "metadata": {
                "error": str(e),
                "user_id": user_id,
                "session_id": session_id
            },
            "messages": []
        }


def test_agent():
    """
    에이전트 테스트 함수
    """
    test_queries = [
        "의료기기 영업 시 병원 구매담당자와 어떻게 소통해야 하나요?",
        "MRI 장비 영업 전략을 알려주세요",
        "의료 규제 요구사항에 대해 설명해주세요"
    ]
    
    print("🏥 의료업계 QA 에이전트 테스트 시작")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 테스트 {i}: {query}")
        print("-" * 30)
        
        result = run_agent(query, user_id=f"test_user_{i}")
        
        if result["success"]:
            response = result["response"]
            print(f"✅ 성공 (신뢰도: {result['confidence']:.2f})")
            print(f"📝 답변: {response.get('answer', '답변 없음')[:100]}...")
        else:
            print(f"❌ 실패: {result['error']}")
    
    print("\n🎉 테스트 완료!")


if __name__ == "__main__":
    # 테스트 실행
    test_agent() 