import os
from typing import Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv

# ────────────────────────────────────────────────────────────────────────────────
# 통합 그래프 import  
# ────────────────────────────────────────────────────────────────────────────────
from ..services.router_agent.unified_agent_graph import unified_graph

# ────────────────────────────────────────────────────────────────────────────────
# 메모리 저장소 (기존 세션 관리 유지)
# ────────────────────────────────────────────────────────────────────────────────
from ..services.router_agent.memory_store_sqlite import (
    add_session,
    add_message,
    get_all_sessions,
    get_session_messages,
    get_session_selected_agent,
    set_session_selected_agent,
    clear_session_selected_agent,
)

# ────────────────────────────────────────────────────────────────────────────────
# 환경 변수
# ────────────────────────────────────────────────────────────────────────────────
api_key = os.getenv("OPENAI_API_KEY")
print("router_api.py - OPENAI_API_KEY:", api_key[:10] + "…" if api_key else "없음")

router = APIRouter()

# ────────────────────────────────────────────────────────────────────────────────
# Pydantic 스키마
# ────────────────────────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    session_id: str
    query: str

class AgentSelectionRequest(BaseModel):
    session_id: str
    query: str
    selected_agent: str

class NewChatRequest(BaseModel):
    session_id: str

class ResetAgentRequest(BaseModel):
    session_id: str

# ────────────────────────────────────────────────────────────────────────────────
# 메인 라우터: 통합 LangGraph 사용
# ────────────────────────────────────────────────────────────────────────────────
@router.post("/router")
async def route_with_unified_graph(req: QueryRequest):
    """통합 LangGraph를 사용한 쿼리 처리"""
    try:
        # 1) 세션 보장 & 사용자 질문 저장
        add_session(req.session_id)
        add_message(req.session_id, "user", req.query)

        print(f"🚀 통합 그래프 처리 시작: {req.session_id}")
        
        # 2) 통합 그래프로 쿼리 처리
        result = await unified_graph.process_query(req.query, req.session_id)

        if not result.get("success"):
            # 실패한 경우
            add_message(
                req.session_id,
                "assistant",
                result.get("response", "처리 실패"),
                metadata={"error": result.get("error"), "stage": result.get("stage")}
            )
            
            return {
                "success": False,
                "response": result.get("response", "처리 중 오류가 발생했습니다."),
                "error": result.get("error"),
                "stage": result.get("stage"),
                "session_id": req.session_id
            }
        
        # 3) 성공한 경우 응답 저장
        response_text = result.get("response", "")
        agent_name = result.get("agent")
        stage = result.get("stage")
        
        # 에이전트가 결정된 경우 세션에 저장 (기존 로직 유지)
        if agent_name and agent_name in ["employee_agent", "client_agent", "create_document_agent", "search_agent"]:
            set_session_selected_agent(req.session_id, agent_name)
            print(f"✅ 세션 에이전트 저장: {agent_name}")
        
        # assistant 응답 저장
        add_message(
            req.session_id,
            "assistant",
            response_text,
            metadata={
                "agent": agent_name,
                "stage": stage,
                "unified_graph": True,
                "requires_followup": result.get("requires_followup", False),
                "user_selection_needed": result.get("user_selection_needed", False)
            }
        )

        # 4) 프론트엔드 응답 구성
        response_data = {
            "success": True,
            "response": response_text,
            "agent": agent_name,
            "stage": stage,
            "session_id": req.session_id,
            "unified_graph": True  # 통합 그래프 사용 표시
        }
        
        # 사용자 선택이 필요한 경우
        if result.get("user_selection_needed"):
            response_data.update({
                "needs_user_selection": True,
                "available_agents": result.get("available_agents", []),
                "message": "에이전트 선택이 필요합니다."
            })
        
        # 후속 입력이 필요한 경우 (문서 작성 등)
        if result.get("requires_followup"):
            response_data.update({
                "requires_followup": True,
                "message": "추가 입력이 필요합니다."
            })
        
        # 메모리 정보 (디버깅용)
        if result.get("memory"):
            response_data["memory_count"] = len(result["memory"])
        
        print(f"✅ 통합 그래프 처리 완료: {agent_name} ({stage})")
        return response_data

    except Exception as e:
        error_msg = f"통합 그래프 처리 중 오류: {str(e)}"
        print(f"❌ {error_msg}")
        
        # 오류 메시지 저장
        add_message(
            req.session_id,
            "assistant",
            "시스템 처리 중 오류가 발생했습니다.",
            metadata={"error": str(e), "unified_graph_error": True}
        )
        
        return {
            "success": False,
            "error": error_msg,
            "response": "시스템 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
            "session_id": req.session_id,
            "stage": "system_error"
        }

# ────────────────────────────────────────────────────────────────────────────────
# 기존 사용자 선택 엔드포인트 (통합 그래프 사용)
# ────────────────────────────────────────────────────────────────────────────────
@router.post("/select-agent")
async def process_agent_selection(req: AgentSelectionRequest):
    """사용자가 에이전트를 직접 선택한 경우 처리"""
    try:
        add_session(req.session_id)
        
        # 사용자 선택 정보 저장
        add_message(
            req.session_id,
            "user",
            f"[에이전트 선택] {req.selected_agent}: {req.query}",
            metadata={"manual_select": True, "selected_agent": req.selected_agent}
        )

        print(f"👤 사용자 직접 선택: {req.selected_agent}")
        
        # 선택된 에이전트를 명시적으로 포함한 쿼리로 재처리
        enhanced_query = f"[{req.selected_agent}] {req.query}"
        
        # 통합 그래프로 처리
        result = await unified_graph.process_query(enhanced_query, req.session_id)
        
        if result.get("success"):
            # 에이전트 세션에 저장
            set_session_selected_agent(req.session_id, req.selected_agent)
            
            response_text = result.get("response", "")
            
            # 선택 안내 메시지 추가  
            agent_display_names = {
                "employee_agent": "직원 실적 분석",
                "client_agent": "고객/거래처 분석", 
                "create_document_agent": "문서 초안 작성",
                "search_agent": "내부 데이터 검색"
            }
            
            agent_name = agent_display_names.get(req.selected_agent, req.selected_agent)
            enhanced_response = f"🎯 '{agent_name}'가 선택되었습니다.\n\n{response_text}"
            
            # 응답 저장
            add_message(
                req.session_id,
                "assistant",
                enhanced_response,
                metadata={
                    "agent": req.selected_agent,
                    "manual_select": True,
                    "unified_graph": True,
                    "stage": result.get("stage")
                }
            )
            
            return {
                "success": True,
                "agent": req.selected_agent,
                "response": enhanced_response,
                "stage": result.get("stage"),
                "agent_fixed": True,
                "unified_graph": True
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "선택된 에이전트 처리 실패"),
                "response": result.get("response", "처리 중 오류가 발생했습니다.")
            }
            
    except Exception as e:
        return {
            "success": False, 
            "error": str(e), 
            "message": "에이전트 선택 처리 중 오류"
        }

# ────────────────────────────────────────────────────────────────────────────────
# 기존 세션 관리 API들 (그대로 유지)
# ────────────────────────────────────────────────────────────────────────────────

@router.post("/new-chat")
def start_new_chat(req: NewChatRequest):
    """새로운 채팅 시작 (에이전트 초기화)"""
    try:
        add_session(req.session_id)
        clear_session_selected_agent(req.session_id)
        
        # 초기 시스템 메시지 추가
        add_message(
            req.session_id,
            "system", 
            "안녕하세요! NaruTalk AI Assistant입니다. 무엇을 도와드릴까요?",
            metadata={"new_chat": True, "unified_graph": True}
        )
        
        return {
            "success": True,
            "message": "새로운 채팅이 시작되었습니다. 질문해주시면 통합 AI가 적절히 처리해드립니다.",
            "session_id": req.session_id,
            "unified_graph": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/current-agent/{session_id}")
def get_current_agent(session_id: str):
    """현재 세션의 선택된 에이전트 확인"""
    try:
        selected_agent = get_session_selected_agent(session_id)
        
        agent_display_names = {
            "employee_agent": "직원 실적 분석",
            "client_agent": "고객/거래처 분석", 
            "create_document_agent": "문서 초안 작성",
            "search_agent": "내부 데이터 검색"
        }
        
        agent_descriptions = {
            "employee_agent": "사내 직원의 실적 분석, 성과 평가, 인사 정보 조회",
            "client_agent": "고객 분석, 거래처 매출 분석, 영업 성과 분석",
            "create_document_agent": "문서 초안 작성, 양식 생성, 컴플라이언스 검토",
            "search_agent": "내부 데이터베이스 검색, 정보 조회, 문서 검색"
        }
        
        if selected_agent:
            agent_info = {
                "agent_key": selected_agent,
                "agent_name": agent_display_names.get(selected_agent, selected_agent),
                "agent_description": agent_descriptions.get(selected_agent, ""),
            }
            return {
                "success": True,
                "has_selected_agent": True,
                "agent_info": agent_info,
                "message": f"현재 '{agent_info['agent_name']}'가 활성화되어 있습니다.",
                "unified_graph": True
            }
        else:
            return {
                "success": True,
                "has_selected_agent": False,
                "message": "통합 AI가 질문에 따라 적절한 에이전트를 자동 선택합니다.",
                "unified_graph": True
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/reset-agent")
def reset_session_agent(req: ResetAgentRequest):
    """현재 세션의 에이전트 초기화"""
    try:
        # 기존 에이전트 확인
        current_agent = get_session_selected_agent(req.session_id)
        
        # 에이전트 초기화
        clear_session_selected_agent(req.session_id)
        
        agent_display_names = {
            "employee_agent": "직원 실적 분석",
            "client_agent": "고객/거래처 분석", 
            "create_document_agent": "문서 초안 작성",
            "search_agent": "내부 데이터 검색"
        }
        
        # 초기화 메시지 추가
        reset_message = (
            f"🔄 **에이전트가 초기화되었습니다.**\n"
            f"{'이전: ' + agent_display_names.get(current_agent, current_agent) if current_agent else ''}\n\n"
            f"이제 통합 AI가 새로운 질문에 맞는 에이전트를 자동으로 선택합니다."
        )
        
        add_message(
            req.session_id,
            "system",
            reset_message,
            metadata={
                "agent_reset": True, 
                "previous_agent": current_agent,
                "unified_graph": True
            }
        )
        
        return {
            "success": True,
            "message": reset_message,
            "previous_agent": current_agent,
            "unified_graph": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ────────────────────────────────────────────────────────────────────────────────
# 시스템 정보 API들
# ────────────────────────────────────────────────────────────────────────────────

@router.get("/agents")
def get_available_agents():
    """사용 가능한 에이전트 목록"""
    try:
        available_agents = ["employee_agent", "client_agent", "create_document_agent", "search_agent"]
        
        agent_descriptions = {
            "employee_agent": "사내 직원의 실적 분석, 성과 평가, 인사 정보 조회",
            "client_agent": "고객 분석, 거래처 매출 분석, 영업 성과 분석", 
            "create_document_agent": "문서 초안 작성, 양식 생성, 컴플라이언스 검토",
            "search_agent": "내부 데이터베이스 검색, 정보 조회, 문서 검색"
        }
        
        agent_display_names = {
            "employee_agent": "직원 실적 분석",
            "client_agent": "고객/거래처 분석",
            "create_document_agent": "문서 초안 작성", 
            "search_agent": "내부 데이터 검색"
        }
        
        return {
            "success": True,
            "available_agents": available_agents,
            "agent_descriptions": agent_descriptions,
            "agent_display_names": agent_display_names,
            "unified_graph": True,
            "message": "통합 LangGraph 기반 다중 에이전트 시스템"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/system-info")
def get_system_info():
    """시스템 정보"""
    return {
        "success": True,
        "system": "NaruTalk AI - Unified Agent System",
        "version": "2.0.0",
        "architecture": "LangGraph + FastAPI",
        "agents": {
            "employee_agent": "직원 실적 분석",
            "client_agent": "고객/거래처 분석",
            "create_document_agent": "문서 초안 작성",
            "search_agent": "내부 데이터 검색"
        },
        "features": [
            "통합 LangGraph 워크플로우",
            "자동 에이전트 분류",
            "상태 기반 대화 관리",
            "실시간 메모리 관리",
            "폴백 및 오류 처리"
        ],
        "unified_graph": True
    }

# ────────────────────────────────────────────────────────────────────────────────
# 채팅 내역 조회 API (기존 유지)
# ────────────────────────────────────────────────────────────────────────────────

@router.get("/sessions")
def get_chat_sessions():
    """모든 채팅 세션 목록 조회"""
    try:
        sessions = get_all_sessions()
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
            "message": f"{len(sessions)}개의 채팅 세션을 찾았습니다.",
            "unified_graph": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/sessions/{session_id}/messages")
def get_session_messages_api(session_id: str):
    """특정 세션의 모든 메시지 조회"""
    try:
        messages = get_session_messages(session_id)
        return {
            "success": True,
            "session_id": session_id,
            "messages": messages,
            "count": len(messages),
            "message": f"{len(messages)}개의 메시지를 찾았습니다.",
            "unified_graph": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/chat-history")
def get_full_chat_history():
    """전체 채팅 내역 (세션 + 메시지) 조회"""
    try:
        sessions = get_all_sessions()
        full_history = []
        
        for session in sessions:
            messages = get_session_messages(session["id"])
            full_history.append({
                "id": session["id"],
                "sessionId": session["id"],  # 프론트엔드 호환
                "title": session["title"],
                "messages": messages,
                "createdAt": session["created_at"],
                "updatedAt": session["updated_at"]
            })
        
        return {
            "success": True,
            "chatHistory": full_history,
            "count": len(full_history),
            "message": f"{len(full_history)}개의 채팅 내역을 불러왔습니다.",
            "unified_graph": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
