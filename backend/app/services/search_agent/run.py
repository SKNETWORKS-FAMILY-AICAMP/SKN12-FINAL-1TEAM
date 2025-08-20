"""
Search Agent Run Module - 완전한 LLM 기반 아키텍처
"""
import os
import json
from typing import Dict, Any, Optional
from .search_agent import create_search_agent

def ensure_formatted_response(response: str, query: str) -> str:
    """
    응답이 정해진 형식을 따르는지 확인하고 필요시 보정
    
    Args:
        response: 원본 응답
        query: 사용자 쿼리
        
    Returns:
        형식화된 응답
    """
    # 필수 섹션들이 있는지 확인
    required_sections = ["## 📌", "## 🔍", "## 📊", "## 💡"]
    
    # 모든 섹션이 있으면 그대로 반환
    if all(section in response for section in required_sections):
        return response
    
    # 형식이 없으면 기본 템플릿으로 래핑
    formatted = f"""## 📌 요약
{query}에 대한 검색 결과입니다.

## 🔍 주요 정보
{response}

## 📊 상세 내용
위 내용이 검색된 전체 정보입니다.

## 💡 추가 정보
- 검색 완료
- 데이터 출처: 통합 검색 시스템"""
    
    return formatted

async def run(query: str, session_id: str, api_token: Optional[str] = None) -> Dict[str, Any]:
    """
    검색 에이전트 실행 - 완전한 LLM 기반 툴 선택 및 자연어 응답 생성
    
    Args:
        query: 사용자 질문
        session_id: 세션 ID
        api_token: JWT 토큰 (검색 API 인증용)
        
    Returns:
        검색 결과 딕셔너리
    """
    try:
        # 검색 에이전트 생성 (JWT 토큰 포함)
        agent = create_search_agent(api_token=api_token)
        
        # 시스템 상태 확인
        health = agent.check_api_health()
        
        # 완전한 LLM 기반 툴 선택
        # LangGraph React 에이전트가 자동으로 적절한 툴을 선택하고
        # 결과를 자연어로 변환하여 제공합니다
        
        # 에이전트 앱 생성
        app = agent.create_agent()
        
        # 초기 상태 설정
        initial_state = {
            "messages": [{"role": "user", "content": query}],
            "next": "agent"
        }
        
        # LLM 기반 툴 선택 및 실행
        result = app.invoke(initial_state)
        
        # 결과에서 응답 추출
        if "messages" in result and len(result["messages"]) > 1:
            last_message = result["messages"][-1]
            # AIMessage 객체에서 content 추출
            if hasattr(last_message, "content"):
                response = last_message.content
            elif "content" in last_message:
                response = last_message["content"]
            else:
                # 최후의 수단으로 str 사용
                response = str(last_message) if last_message else "응답을 생성할 수 없습니다."
        else:
            response = "응답을 생성할 수 없습니다."
        
        # 응답 형식 검증 및 보정
        response = ensure_formatted_response(response, query)
        
        search_type = "LLM 기반 자동 선택 (자연어 응답)"
        
        # 성공 응답
        return {
            "success": True,
            "response": response,
            "report": f"[Search Agent - {search_type}]\n{response}",
            "agent": "search_agent",
            "session_id": session_id,
            "search_type": search_type,
            "api_health": health,
            "llm_based": True
        }
        
    except Exception as e:
        # 오류 응답
        error_message = f"검색 에이전트 실행 중 오류가 발생했습니다: {str(e)}"
        return {
            "success": False,
            "response": error_message,
            "report": f"[Search Agent - Error]\n{error_message}",
            "agent": "search_agent",
            "session_id": session_id,
            "error": str(e),
            "llm_based": True
        }

def run_sync(query: str, session_id: str, api_token: Optional[str] = None) -> Dict[str, Any]:
    """
    동기식 검색 에이전트 실행 (테스트용) - 완전한 LLM 기반 및 자연어 응답
    
    Args:
        query: 사용자 질문
        session_id: 세션 ID
        api_token: JWT 토큰 (검색 API 인증용)
        
    Returns:
        검색 결과 딕셔너리
    """
    try:
        # 검색 에이전트 생성 (JWT 토큰 포함)
        agent = create_search_agent(api_token=api_token)
        
        # 시스템 상태 확인
        health = agent.check_api_health()
        
        # 완전한 LLM 기반 툴 선택
        # LangGraph React 에이전트가 자동으로 적절한 툴을 선택하고
        # 결과를 자연어로 변환하여 제공합니다
        
        # 에이전트 앱 생성
        app = agent.create_agent()
        
        # 초기 상태 설정
        initial_state = {
            "messages": [{"role": "user", "content": query}],
            "next": "agent"
        }
        
        # LLM 기반 툴 선택 및 실행
        result = app.invoke(initial_state)
        
        # 결과에서 응답 추출
        if "messages" in result and len(result["messages"]) > 1:
            last_message = result["messages"][-1]
            # AIMessage 객체에서 content 추출
            if hasattr(last_message, "content"):
                response = last_message.content
            elif "content" in last_message:
                response = last_message["content"]
            else:
                # 최후의 수단으로 str 사용
                response = str(last_message) if last_message else "응답을 생성할 수 없습니다."
        else:
            response = "응답을 생성할 수 없습니다."
        
        # 응답 형식 검증 및 보정
        response = ensure_formatted_response(response, query)
        
        search_type = "LLM 기반 자동 선택 (자연어 응답)"
        
        # 성공 응답
        return {
            "success": True,
            "response": response,
            "report": f"[Search Agent - {search_type}]\n{response}",
            "agent": "search_agent",
            "session_id": session_id,
            "search_type": search_type,
            "api_health": health,
            "llm_based": True
        }
        
    except Exception as e:
        # 오류 응답
        error_message = f"검색 에이전트 실행 중 오류가 발생했습니다: {str(e)}"
        return {
            "success": False,
            "response": error_message,
            "report": f"[Search Agent - Error]\n{error_message}",
            "agent": "search_agent",
            "session_id": session_id,
            "error": str(e),
            "llm_based": True
        }