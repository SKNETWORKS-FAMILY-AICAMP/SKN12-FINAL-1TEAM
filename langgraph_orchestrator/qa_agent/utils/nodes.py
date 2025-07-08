"""
QA Medical Agent Nodes
LangGraph 0.5+ compatible workflow nodes
"""
import json
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from .state import AgentState, IntentClassification, FinalResponse
from .tools import (
    search_medical_documents,
    get_medical_industry_context,
    validate_medical_response,
    format_medical_response
)


def extract_user_query(state: AgentState) -> AgentState:
    """
    사용자 쿼리 추출 노드
    """
    try:
        if state.get("messages") and len(state["messages"]) > 0:
            last_message = state["messages"][-1]
            if isinstance(last_message, HumanMessage):
                state["user_query"] = last_message.content
            else:
                state["user_query"] = str(last_message.content)
        else:
            state["user_query"] = state.get("user_query", "")
        
        # 메타데이터 초기화
        if "metadata" not in state:
            state["metadata"] = {}
        
        state["metadata"]["step"] = "query_extracted"
        return state
        
    except Exception as e:
        state["error"] = f"쿼리 추출 중 오류: {str(e)}"
        return state


def classify_intent(state: AgentState) -> AgentState:
    """
    의도 분류 노드 (GPT-4o-mini 사용)
    """
    try:
        query = state.get("user_query", "")
        if not query:
            state["error"] = "분류할 쿼리가 없습니다"
            return state
        
        # GPT-4o-mini로 빠른 의도 분류
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=1000
        )
        
        system_prompt = """
        당신은 의료업계 QA 시스템의 의도 분류 전문가입니다.
        사용자 질의를 다음 카테고리로 분류하세요:
        
        1. sales_strategy: 영업 전략, 고객 관계
        2. product_info: 제품 정보, 기술 사양
        3. regulatory: 규제, 인증, 법적 요구사항
        4. market_analysis: 시장 분석, 경쟁사 정보
        5. customer_support: 고객 지원, 사후 서비스
        6. general: 일반적인 문의
        
        JSON 형태로 응답하세요:
        {
            "intent": "category_name",
            "confidence": 0.95,
            "keywords": ["keyword1", "keyword2"],
            "suggested_services": ["service1", "service2"]
        }
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"질의: {query}"}
        ]
        
        response = llm.invoke(messages)
        
        try:
            intent_result = json.loads(response.content)
            state["intent"] = intent_result
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본값
            state["intent"] = {
                "intent": "general",
                "confidence": 0.5,
                "keywords": query.split()[:3],
                "suggested_services": ["search"]
            }
        
        state["metadata"]["step"] = "intent_classified"
        return state
        
    except Exception as e:
        print(f"⚠️ 의도 분류 중 오류 발생: {str(e)}")
        state["error"] = f"의도 분류 중 오류: {str(e)}"
        state["intent"] = {
            "intent": "general", 
            "confidence": 0.0,
            "keywords": [],
            "suggested_services": ["search"]
        }
        return state


def search_documents(state: AgentState) -> AgentState:
    """
    문서 검색 노드
    """
    try:
        query = state.get("user_query", "")
        intent = state.get("intent", {})
        
        if not query:
            state["error"] = "검색할 쿼리가 없습니다"
            return state
        
        # 의도에 따른 검색 전략 조정
        search_limit = 10 if intent.get("confidence", 0) > 0.8 else 5
        
        # 문서 검색 실행
        search_results = search_medical_documents.invoke({
            "query": query,
            "limit": search_limit
        })
        
        state["search_results"] = search_results
        state["metadata"]["step"] = "documents_searched"
        state["metadata"]["search_count"] = len(search_results)
        
        return state
        
    except Exception as e:
        state["error"] = f"문서 검색 중 오류: {str(e)}"
        state["search_results"] = []
        return state


def enhance_context(state: AgentState) -> AgentState:
    """
    컨텍스트 향상 노드 (GPT-4o-mini 사용)
    """
    try:
        query = state.get("user_query", "")
        search_results = state.get("search_results", [])
        intent = state.get("intent", {})
        
        if not search_results:
            state["enhanced_context"] = f"질의: {query}\n관련 문서를 찾지 못했습니다."
            return state
        
        # 의료업계 컨텍스트 추가
        industry_context = get_medical_industry_context.invoke()
        
        # GPT-4o-mini로 컨텍스트 향상
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=2000
        )
        
        # 검색 결과 요약
        search_summary = "\n".join([
            f"- {result.get('title', 'Unknown')}: {result.get('content', '')[:200]}..."
            for result in search_results[:3]
        ])
        
        system_prompt = f"""
        당신은 의료업계 전문 컨텍스트 향상 도우미입니다.
        
        업계 정보:
        {json.dumps(industry_context, ensure_ascii=False, indent=2)}
        
        사용자 의도: {intent.get('intent', 'general')}
        
        다음 검색 결과들을 의료업계 전문성을 고려하여 종합하고 향상시켜주세요:
        """
        
        user_prompt = f"""
        원본 질의: {query}
        
        검색 결과:
        {search_summary}
        
        위 정보를 바탕으로 의료업계 전문가 관점에서 종합적이고 실용적인 컨텍스트를 생성해주세요.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        state["enhanced_context"] = response.content
        state["metadata"]["step"] = "context_enhanced"
        
        return state
        
    except Exception as e:
        state["error"] = f"컨텍스트 향상 중 오류: {str(e)}"
        state["enhanced_context"] = f"질의: {query}\n기본 컨텍스트를 사용합니다."
        return state


def generate_response(state: AgentState) -> AgentState:
    """
    최종 응답 생성 노드 (GPT-4o 사용)
    """
    try:
        query = state.get("user_query", "")
        enhanced_context = state.get("enhanced_context", "")
        intent = state.get("intent", {})
        
        # GPT-4o로 고품질 최종 응답 생성
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=4000
        )
        
        system_prompt = """
        당신은 의료업계 전문 QA 시스템의 최고급 AI 어시스턴트입니다.
        다음 조건을 만족하는 고품질 응답을 생성하세요:
        
        1. 정확하고 신뢰할 수 있는 정보 제공
        2. 의료업계 전문성 반영
        3. 사용자 친화적이고 이해하기 쉬운 설명
        4. 필요시 추가 정보나 다음 단계 제안
        5. 한국어로 자연스럽고 전문적인 톤
        
        응답은 다음 JSON 형태로 제공하세요:
        {
            "answer": "주요 답변 내용",
            "summary": "핵심 요약",
            "recommendations": ["권장사항1", "권장사항2"],
            "confidence": 0.95,
            "sources": ["참고자료1", "참고자료2"]
        }
        """
        
        user_prompt = f"""
        사용자 질의: {query}
        사용자 의도: {intent.get('intent', 'general')}
        
        수집된 컨텍스트:
        {enhanced_context}
        
        위 정보를 바탕으로 종합적이고 정확한 답변을 생성해주세요.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        
        try:
            response_data = json.loads(response.content)
            state["final_response"] = response_data
            state["confidence_score"] = response_data.get("confidence", 0.8)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트 응답 사용
            state["final_response"] = {
                "answer": response.content,
                "summary": "응답이 생성되었습니다.",
                "recommendations": [],
                "confidence": 0.8,
                "sources": []
            }
            state["confidence_score"] = 0.8
        
        state["metadata"]["step"] = "response_generated"
        return state
        
    except Exception as e:
        state["error"] = f"응답 생성 중 오류: {str(e)}"
        state["final_response"] = {
            "answer": "죄송합니다. 현재 응답을 생성할 수 없습니다.",
            "summary": "오류 발생",
            "recommendations": [],
            "confidence": 0.0,
            "sources": []
        }
        state["confidence_score"] = 0.0
        return state


def validate_response(state: AgentState) -> AgentState:
    """
    응답 검증 노드
    """
    try:
        final_response = state.get("final_response", {})
        answer = final_response.get("answer", "")
        
        if not answer:
            state["error"] = "검증할 응답이 없습니다"
            return state
        
        # 의료업계 응답 검증
        validation_result = validate_medical_response.invoke({"response": answer})
        
        # 검증 결과를 메타데이터에 추가
        state["metadata"]["validation"] = validation_result
        state["metadata"]["step"] = "response_validated"
        
        # 검증 실패 시 경고 추가
        if not validation_result.get("is_valid", True):
            if "warnings" not in state["metadata"]:
                state["metadata"]["warnings"] = []
            state["metadata"]["warnings"].append("의료업계 관련성이 낮을 수 있습니다")
        
        return state
        
    except Exception as e:
        state["error"] = f"응답 검증 중 오류: {str(e)}"
        return state


def format_final_output(state: AgentState) -> AgentState:
    """
    최종 출력 포맷팅 노드
    """
    try:
        final_response = state.get("final_response", {})
        confidence_score = state.get("confidence_score", 0.0)
        
        answer = final_response.get("answer", "응답을 생성할 수 없습니다.")
        sources = final_response.get("sources", [])
        
        # 의료업계 전용 포맷팅
        formatted_result = format_medical_response.invoke({
            "answer": answer,
            "sources": sources,
            "confidence": confidence_score
        })
        
        # 최종 메시지 생성
        final_message = AIMessage(content=formatted_result["formatted_answer"])
        
        # 상태 업데이트
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(final_message)
        
        state["metadata"]["step"] = "output_formatted"
        state["metadata"]["formatting"] = formatted_result
        
        return state
        
    except Exception as e:
        state["error"] = f"출력 포맷팅 중 오류: {str(e)}"
        error_message = AIMessage(content="죄송합니다. 응답 처리 중 오류가 발생했습니다.")
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(error_message)
        return state 