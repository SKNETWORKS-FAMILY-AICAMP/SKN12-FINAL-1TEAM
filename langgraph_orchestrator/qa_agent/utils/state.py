"""
QA Medical Agent State Definition
LangGraph 0.5+ compatible state management
"""
from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    QA 의료업계 에이전트 상태 정의
    """
    # 입력 메시지
    messages: List[BaseMessage]
    
    # 사용자 쿼리
    user_query: str
    
    # 의도 분류 결과
    intent: Optional[Dict[str, Any]]
    
    # 검색 결과들
    search_results: List[Dict[str, Any]]
    
    # 향상된 컨텍스트
    enhanced_context: Optional[str]
    
    # 최종 응답
    final_response: Optional[Dict[str, Any]]
    
    # 신뢰도 점수
    confidence_score: Optional[float]
    
    # 메타데이터
    metadata: Dict[str, Any]
    
    # 오류 정보
    error: Optional[str]


class SearchResult(TypedDict):
    """검색 결과 구조"""
    id: str
    title: str
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]


class IntentClassification(TypedDict):
    """의도 분류 결과 구조"""
    intent: str
    confidence: float
    keywords: List[str]
    suggested_services: List[str]


class FinalResponse(TypedDict):
    """최종 응답 구조"""
    answer: str
    summary: str
    recommendations: List[str]
    confidence: float
    sources: List[str]
    model_used: str 