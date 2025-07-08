"""
QA Medical Agent Tools
LangGraph 0.5+ compatible tools for medical industry QA
"""
import os
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


@tool
def search_medical_documents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    의료업계 문서 검색 도구
    
    Args:
        query: 검색 쿼리
        limit: 검색 결과 수 제한
        
    Returns:
        검색 결과 리스트
    """
    try:
        # 실제 구현에서는 검색 마이크로서비스 (포트 8001) 호출
        # 현재는 시뮬레이션 데이터 반환
        sample_results = [
            {
                "id": "doc_001",
                "title": "의료기기 영업 전략 가이드",
                "content": "의료기기 영업에서 중요한 것은 의료진과의 신뢰 관계 구축입니다. 제품의 기술적 우수성뿐만 아니라 의료진의 니즈를 파악하고 맞춤형 솔루션을 제공하는 것이 핵심입니다.",
                "score": 0.95,
                "source": "internal_docs",
                "metadata": {
                    "category": "sales",
                    "keywords": ["의료기기", "영업", "신뢰관계"]
                }
            },
            {
                "id": "doc_002",
                "title": "병원 구매 담당자와의 소통 방법",
                "content": "병원 구매 담당자와 효과적으로 소통하기 위해서는 비용 효율성, 품질 보증, 사후 서비스 등을 명확하게 제시해야 합니다.",
                "score": 0.88,
                "source": "internal_docs",
                "metadata": {
                    "category": "communication",
                    "keywords": ["병원", "구매담당자", "비용효율성"]
                }
            }
        ]
        
        # 쿼리와 관련성 체크 (간단한 키워드 매칭)
        filtered_results = []
        query_lower = query.lower()
        
        for result in sample_results:
            if any(keyword in query_lower for keyword in result["metadata"]["keywords"]):
                filtered_results.append(result)
        
        return filtered_results[:limit]
        
    except Exception as e:
        return [{"error": f"검색 중 오류 발생: {str(e)}"}]


@tool 
async def call_search_microservice(query: str, search_type: str = "enhanced") -> Dict[str, Any]:
    """
    검색 마이크로서비스 호출 도구 (포트 8001)
    
    Args:
        query: 검색 쿼리
        search_type: 검색 타입 (vector, keyword, enhanced)
        
    Returns:
        검색 서비스 응답
    """
    try:
        search_url = f"http://localhost:8001/api/v1/search/{search_type}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                search_url,
                json={
                    "query": query,
                    "limit": 10,
                    "user_id": "test_user"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"검색 서비스 오류: {response.status_code}"
                }
                
    except Exception as e:
        return {
            "success": False, 
            "error": f"검색 서비스 연결 실패: {str(e)}"
        }


@tool
def get_medical_industry_context() -> Dict[str, Any]:
    """
    의료업계 컨텍스트 정보 제공 도구
    
    Returns:
        의료업계 관련 컨텍스트 정보
    """
    return {
        "industry_info": {
            "sector": "의료업계",
            "focus_areas": [
                "의료기기 영업",
                "병원 관계 관리", 
                "규제 준수",
                "품질 보증",
                "사후 서비스"
            ],
            "key_stakeholders": [
                "의료진",
                "병원 구매담당자",
                "의료기기 업체",
                "규제기관"
            ],
            "common_challenges": [
                "신뢰 관계 구축",
                "비용 효율성 증명",
                "기술적 우수성 입증",
                "규제 요구사항 준수"
            ]
        },
        "current_trends": [
            "디지털 헬스케어",
            "AI 진단 도구",
            "원격 진료",
            "IoT 의료기기",
            "데이터 기반 의사결정"
        ]
    }


@tool
def validate_medical_response(response: str) -> Dict[str, Any]:
    """
    의료업계 응답 검증 도구
    
    Args:
        response: 검증할 응답 텍스트
        
    Returns:
        검증 결과
    """
    validation_rules = [
        "의료진 언급",
        "병원 관련 용어",
        "의료기기 언급",
        "품질 또는 안전성",
        "비용 효율성"
    ]
    
    response_lower = response.lower()
    matched_rules = []
    
    for rule in validation_rules:
        if any(keyword in response_lower for keyword in rule.split()):
            matched_rules.append(rule)
    
    relevance_score = len(matched_rules) / len(validation_rules)
    
    return {
        "is_valid": relevance_score >= 0.3,
        "relevance_score": relevance_score,
        "matched_rules": matched_rules,
        "suggestions": [
            "의료업계 전문 용어 추가",
            "구체적인 사례 포함",
            "데이터 기반 근거 제시"
        ] if relevance_score < 0.5 else []
    }


@tool
def format_medical_response(
    answer: str, 
    sources: List[str], 
    confidence: float
) -> Dict[str, Any]:
    """
    의료업계 전용 응답 포매팅 도구
    
    Args:
        answer: 기본 답변
        sources: 참고 소스들
        confidence: 신뢰도
        
    Returns:
        포매팅된 응답
    """
    # 의료업계 전문성 강화
    professional_prefix = "의료업계 전문 AI 어시스턴트 답변:\n\n"
    
    # 신뢰도에 따른 면책 조항
    disclaimer = ""
    if confidence < 0.8:
        disclaimer = "\n\n⚠️ 참고: 이 정보는 일반적인 가이드라인이며, 구체적인 의료 결정이나 진단에는 전문가와 상담하시기 바랍니다."
    
    formatted_answer = professional_prefix + answer + disclaimer
    
    return {
        "formatted_answer": formatted_answer,
        "confidence_level": "높음" if confidence >= 0.8 else "보통" if confidence >= 0.6 else "낮음",
        "source_count": len(sources),
        "has_disclaimer": bool(disclaimer),
        "medical_context": True
    } 