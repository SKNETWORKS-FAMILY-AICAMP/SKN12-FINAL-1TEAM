import os
from typing import Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import asyncio
import json

# ────────────────────────────────────────────────────────────────────────────────
# 내부 모듈 import
# ────────────────────────────────────────────────────────────────────────────────
# · StateGraphRouter  : LangGraph 분류기
# · RouterAgent       : 에이전트 메타정보
# · add_session       : 세션 row 생성 (중복 무시)
# · add_message       : 메시지 저장 (role/user/assistant, metadata 포함)
# ------------------------------------------------------------------------------
from ..services.router_agent.state_graph_router import StateGraphRouter
from ..services.router_agent.router_agent import RouterAgent
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
# 환경 변수 및 라우터 초기화
# ────────────────────────────────────────────────────────────────────────────────
api_key = os.getenv("OPENAI_API_KEY")
print("router_api.py - OPENAI_API_KEY:", api_key[:10] + "…" if api_key else "없음")

router: APIRouter = APIRouter()
state_graph_router = StateGraphRouter()
router_agent = RouterAgent()

# 내부‑API 베이스 URL (FastAPI 동일 앱이라면 localhost 그대로 OK)
BASE_URL = "http://localhost:8000"

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

# ────────────────────────────────────────────────────────────────────────────────
# 공통 함수: 선택된 에이전트 API 호출
# ────────────────────────────────────────────────────────────────────────────────
async def call_agent_api(agent_name: str, query: str, session_id: str = None) -> Dict[str, Any]:
    """선택된 에이전트 이름과 쿼리를 받아 실제 API 호출"""
    try:
        async with httpx.AsyncClient() as client:
            # ─────────── 직원 분석 ───────────
            if agent_name == "employee_agent":
                response = await client.post(
                    f"{BASE_URL}/api/employee/analyze",
                    json={"session_id": session_id, "query": query},
                    timeout=30.0,
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", True):
                        employee_name = result.get("employee_name", "N/A")
                        period = result.get("period", "N/A")
                        analysis_result = result.get("result", "분석 결과가 없습니다.")

                        formatted_response = (
                            f"📊 **직원 실적 분석 완료!**\n\n"
                            f"👤 분석 대상: {employee_name}\n"
                            f"📅 분석 기간: {period}\n\n"
                            f"📈 분석 결과:\n{analysis_result}\n\n"
                            f"✅ 직원 성과 분석이 완료되었습니다!"
                        )
                        return {
                            "success": True,
                            "agent": agent_name,
                            "response": formatted_response,
                            "api_result": result,
                        }
                    return {
                        "success": False,
                        "error": result.get("result", "직원 분석 실패"),
                    }

            # ─────────── 거래처 분석 ───────────
            elif agent_name == "client_agent":
                response = await client.post(
                    f"{BASE_URL}/api/client/analyze",
                    json={"session_id": session_id, "query": query},
                    timeout=30.0,
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", True):
                        client_name = result.get("client_name", "N/A")
                        analysis_type = result.get("analysis_type", "N/A")
                        analysis_result = result.get("result", "분석 결과가 없습니다.")

                        formatted_response = (
                            f"🏥 **고객 분석 완료!**\n\n"
                            f"🏢 분석 대상: {client_name}\n"
                            f"📊 분석 유형: {analysis_type}\n\n"
                            f"📈 분석 결과:\n{analysis_result}\n\n"
                            f"✅ 고객 분석이 완료되었습니다!"
                        )
                        return {
                            "success": True,
                            "agent": agent_name,
                            "response": formatted_response,
                            "api_result": result,
                        }
                    return {
                        "success": False,
                        "error": result.get("result", "고객 분석 실패"),
                    }

            # ─────────── 문서 분류/작성 ───────────                        
            elif agent_name == "docs_agent":
                # 먼저 세션 상태 확인
                session_status = None
                try:
                    if session_id:
                        status_response = await client.get(
                            f"{BASE_URL}/api/docs/status/{session_id}",
                            timeout=10.0,
                        )
                        if status_response.status_code == 200:
                            session_status = status_response.json()
                except:
                    pass  # 세션 상태 확인 실패 시 초기 요청으로 처리
                
                # 세션 상태에 따라 초기 요청인지 후속 입력인지 판단
                is_initial = True
                if session_status and session_status.get("stage") in ["classified", "waiting_input"]:
                    is_initial = False
                
                # 문서 상호작용 API 호출
                response = await client.post(
                    f"{BASE_URL}/api/docs/interactive",
                    json={
                        "session_id": session_id or "temp_session",
                        "user_input": query,
                        "is_initial": is_initial
                    },
                    timeout=30.0,
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", True):
                        # 상호작용 단계별 처리
                        stage = result.get("stage", "")
                        doc_type = result.get("doc_type", "문서")
                        message = result.get("message", "")
                        
                        if stage == "waiting_input":
                            # 사용자 입력 대기 단계 - 템플릿 제공
                            template = result.get("template", "")
                            formatted_response = (
                                f"📄 **문서 분류 완료!**\n\n"
                                f"📋 분류 결과: {doc_type}\n\n"
                                f"{message}\n\n"
                                f"📝 **입력 템플릿:**\n"
                                f"```\n{template}\n```\n\n"
                                f"💡 **다음 단계:** 위 템플릿에 맞춰 정보를 입력해주시면 문서를 작성해드립니다!"
                            )
                        elif stage == "completed":
                            # 문서 작성 완료
                            document = result.get("document", {})
                            formatted_response = (
                                f"📄 **{doc_type} 작성 완료!**\n\n"
                                f"{message}\n\n"
                                f"📋 **작성된 문서:**\n"
                                f"```json\n{json.dumps(document, indent=2, ensure_ascii=False)}\n```"
                            )
                        else:
                            # 기타 상태 (processing, error 등)
                            formatted_response = (
                                f"📄 **문서 처리 상태**\n\n"
                                f"단계: {stage}\n"
                                f"{message}"
                            )
                        
                        return {
                            "success": True,
                            "agent": agent_name,
                            "response": formatted_response,
                            "api_result": result,
                            "stage": stage,
                            "requires_followup": stage == "waiting_input"  # 후속 입력 필요 여부
                        }
                    return {
                        "success": False,
                        "error": result.get("error", "문서 처리 실패"),
                    }

            # ─────────── 검색 (더미) ───────────
            elif agent_name == "search_agent":
                formatted_response = (
                    f"🔍 **내부 데이터 검색 완료!**\n\n"
                    f"🔎 검색 쿼리: \"{query}\"\n\n"
                    f"📋 검색 결과:\n"
                    f"• 관련 문서 5건 발견 등...\n\n"
                    f"✅ 내부 데이터 검색이 완료되었습니다!"
                )
                return {
                    "success": True,
                    "agent": agent_name,
                    "response": formatted_response,
                }

            # ─────────── 알 수 없는 에이전트 ───────────
            return {
                "success": False,
                "error": f"Unknown agent: {agent_name}",
            }

    except httpx.TimeoutException:
        return {"success": False, "error": "API 호출 시간 초과"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ────────────────────────────────────────────────────────────────────────────────
# 메인 라우터: LangGraph 라우팅
# ────────────────────────────────────────────────────────────────────────────────
@router.post("/router")
async def route_with_state_graph(req: QueryRequest):
    """사용자 쿼리를 분석하고 적절한 에이전트로 라우팅 (세션별 에이전트 고정)"""
    try:
        # 1) 세션 보장 & 사용자 질문 저장
        add_session(req.session_id)
        add_message(req.session_id, "user", req.query)

        # 2) 세션에 이미 선택된 에이전트가 있는지 확인
        selected_agent = get_session_selected_agent(req.session_id)
        
        if selected_agent and selected_agent in router_agent.available_agents:
            # ── 이미 선택된 에이전트가 있는 경우: 바로 API 호출 ────────────────
            print(f"🎯 세션 {req.session_id}에서 기존 에이전트 사용: {selected_agent}")
            
            api_result = await call_agent_api(selected_agent, req.query, req.session_id)

            # assistant 응답 저장
            add_message(
                req.session_id,
                "assistant",
                api_result.get("response", ""),
                metadata={"agent": selected_agent, "error": api_result.get("error"), "session_agent": True},
            )

            return {
                "success": api_result.get("success", True),
                "agent": selected_agent,
                "response": api_result.get("response", ""),
                "api_result": api_result.get("api_result"),
                "error": api_result.get("error"),
                "session_agent": True,  # 세션 고정 에이전트임을 표시
            }

        # 3) 선택된 에이전트가 없는 경우: LangGraph 분류 진행
        print(f"🔍 세션 {req.session_id}에서 새로운 에이전트 분류 시작")
        result = state_graph_router.process_query(req.query)

        # ── (A) 사용자 직접 선택이 필요한 경우 ────────────────────────────────
        if result.get("selected_agent") == "NEED_USER_SELECTION":
            assistant_msg = "질문의 의도가 불분명합니다. 4개 중 하나를 선택해주세요.\n\n💡 선택하신 에이전트가 이 채팅에서 고정됩니다."
            add_message(
                req.session_id,
                "assistant",
                assistant_msg,
                metadata={"needs_user_selection": True},
            )
            return {
                "success": True,
                "needs_user_selection": True,
                "message": assistant_msg,
                "available_agents": router_agent.available_agents,
                "agent_descriptions": router_agent.agent_descriptions,
                "agent_display_names": router_agent.get_agent_display_names(),
                "query": req.query,
            }

        # ── (B) 에이전트가 결정된 경우 ────────────────────────────────────────
        classified_agent = result.get("selected_agent")
        if classified_agent in router_agent.available_agents:
            # 🔹 세션에 에이전트 저장 (고정)
            set_session_selected_agent(req.session_id, classified_agent)
            
            api_result = await call_agent_api(classified_agent, req.query, req.session_id)

            # assistant 응답 저장
            add_message(
                req.session_id,
                "assistant",
                api_result.get("response", ""),
                metadata={"agent": classified_agent, "error": api_result.get("error"), "agent_selected": True},
            )

            return {
                "success": api_result.get("success", True),
                "agent": classified_agent,
                "response": api_result.get("response", ""),
                "api_result": api_result.get("api_result"),
                "error": api_result.get("error"),
                "agent_selected": True,  # 새로 선택된 에이전트임을 표시
                "message": f"🎯 '{router_agent.get_agent_display_names().get(classified_agent, classified_agent)}'가 이 채팅의 전담 에이전트가 되었습니다."
            }

        # ── (C) 분류 결과는 나왔지만 매칭되는 에이전트가 없을 때 ─────────────
        fallback_msg = "적절한 에이전트를 찾지 못했습니다."
        add_message(
            req.session_id,
            "assistant",
            fallback_msg,
            metadata={"agent": "unknown"},
        )
        return {
            "success": False,
            "message": fallback_msg,
            "query": req.query,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "message": "라우팅 처리 중 오류"}

# ────────────────────────────────────────────────────────────────────────────────
# 사용자 선택 에이전트 처리
# ────────────────────────────────────────────────────────────────────────────────
@router.post("/select-agent")
async def process_agent_selection(req: AgentSelectionRequest):
    """프론트에서 사용자가 에이전트를 직접 골랐을 때 (세션에 고정)"""
    try:
        add_session(req.session_id)
        # 사용자 선택 정보도 user role 로 남김(옵션)
        add_message(
            req.session_id,
            "user",
            f"[사용자 선택] {req.selected_agent}",
            metadata={"manual_select": True},
        )

        # 🔹 세션에 선택된 에이전트 저장 (고정)
        set_session_selected_agent(req.session_id, req.selected_agent)

        api_result = await call_agent_api(req.selected_agent, req.query, req.session_id)

        # 에이전트 고정 안내 메시지 추가
        agent_display_name = router_agent.get_agent_display_names().get(req.selected_agent, req.selected_agent)
        enhanced_response = f"🎯 '{agent_display_name}'가 이 채팅의 전담 에이전트가 되었습니다.\n\n{api_result.get('response', '')}"

        add_message(
            req.session_id,
            "assistant",
            enhanced_response,
            metadata={"agent": req.selected_agent, "error": api_result.get("error"), "manual_select": True},
        )

        return {
            "success": api_result.get("success", True),
            "agent": req.selected_agent,
            "response": enhanced_response,
            "error": api_result.get("error"),
            "agent_fixed": True,  # 에이전트 고정됨을 표시
        }
    except Exception as e:
        return {"success": False, "error": str(e), "message": "선택 처리 중 오류"}

# ────────────────────────────────────────────────────────────────────────────────
# 세션별 에이전트 관리 API
# ────────────────────────────────────────────────────────────────────────────────

class NewChatRequest(BaseModel):
    session_id: str

class ResetAgentRequest(BaseModel):
    session_id: str

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
            metadata={"new_chat": True}
        )
        
        return {
            "success": True,
            "message": "새로운 채팅이 시작되었습니다. 질문해주시면 적절한 에이전트를 선택해드립니다.",
            "session_id": req.session_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/current-agent/{session_id}")
def get_current_agent(session_id: str):
    """현재 세션의 선택된 에이전트 확인"""
    try:
        selected_agent = get_session_selected_agent(session_id)
        
        if selected_agent:
            agent_info = {
                "agent_key": selected_agent,
                "agent_name": router_agent.get_agent_display_names().get(selected_agent, selected_agent),
                "agent_description": router_agent.agent_descriptions.get(selected_agent, ""),
            }
            return {
                "success": True,
                "has_selected_agent": True,
                "agent_info": agent_info,
                "message": f"현재 '{agent_info['agent_name']}'가 이 채팅의 전담 에이전트입니다."
            }
        else:
            return {
                "success": True,
                "has_selected_agent": False,
                "message": "아직 선택된 에이전트가 없습니다. 질문해주시면 적절한 에이전트를 선택해드립니다."
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
        
        # 초기화 메시지 추가
        reset_message = (
            f"🔄 에이전트가 초기화되었습니다.\n"
            f"{'기존: ' + router_agent.get_agent_display_names().get(current_agent, current_agent) if current_agent else ''}\n\n"
            f"이제 새로운 질문에 맞는 에이전트를 다시 선택해드립니다."
        )
        
        add_message(
            req.session_id,
            "system",
            reset_message,
            metadata={"agent_reset": True, "previous_agent": current_agent}
        )
        
        return {
            "success": True,
            "message": reset_message,
            "previous_agent": current_agent
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ────────────────────────────────────────────────────────────────────────────────
# 헬프용 엔드포인트: 사용 가능한 에이전트 목록
# ────────────────────────────────────────────────────────────────────────────────
@router.get("/agents")
def get_available_agents():
    try:
        return {
            "success": True,
            "available_agents": router_agent.available_agents,
            "agent_descriptions": router_agent.agent_descriptions,
            "agent_display_names": router_agent.get_agent_display_names(),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ────────────────────────────────────────────────────────────────────────────────
# 채팅 내역 조회 API
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
            "message": f"{len(sessions)}개의 채팅 세션을 찾았습니다."
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
            "message": f"{len(messages)}개의 메시지를 찾았습니다."
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
            "message": f"{len(full_history)}개의 채팅 내역을 불러왔습니다."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
