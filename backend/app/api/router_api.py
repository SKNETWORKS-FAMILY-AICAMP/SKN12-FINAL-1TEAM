
import os
from fastapi import APIRouter
from pydantic import BaseModel
from ..services.router_agent.state_graph_router import StateGraphRouter
from ..services.router_agent.router_agent import RouterAgent
from dotenv import load_dotenv

# OPENAI_API_KEY 확인
api_key = os.getenv("OPENAI_API_KEY")
print("router_api.py - OPENAI_API_KEY:", api_key[:10] + "..." if api_key else "없음")

# FastAPI 라우터 구성
router = APIRouter()
state_graph_router = StateGraphRouter()
router_agent = RouterAgent()

class QueryRequest(BaseModel):
    query: str

class AgentSelectionRequest(BaseModel):
    query: str
    selected_agent: str

@router.post("/router")
def route_with_state_graph(req: QueryRequest):
    """쿼리를 분석하고 적절한 에이전트로 라우팅"""
    try:
        result = state_graph_router.process_query(req.query)
        
        # 사용자 선택이 필요한 경우
        if result.get("selected_agent") == "NEED_USER_SELECTION":
            return {
                "success": True,
                "needs_user_selection": True,
                "message": "질문의 의도가 불분명합니다. 4개중에 1개를 선택해주세요",
                "query": result.get("query", ""),
                "routing_attempts": result.get("routing_attempts", 0),
                "classification_result": result.get("classification_result", ""),
                "available_agents": router_agent.available_agents,
                "agent_descriptions": router_agent.agent_descriptions,
                "agent_display_names": router_agent.get_agent_display_names()
            }
        
        return {
            "success": True,
            "agent": result.get("selected_agent", "unknown"),
            "response": result.get("final_response", ""),
            "message": f"{result.get('selected_agent', 'unknown')} 에이전트로 라우팅되었습니다.",
            "query": result.get("query", ""),
            "routing_attempts": result.get("routing_attempts", 0),
            "classification_result": result.get("classification_result", "")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "라우팅 처리 중 오류가 발생했습니다."
        }

@router.get("/agents")
def get_available_agents():
    """사용 가능한 에이전트 목록 반환"""
    try:
        return {
            "success": True,
            "available_agents": router_agent.available_agents,
            "agent_descriptions": router_agent.agent_descriptions,
            "agent_display_names": router_agent.get_agent_display_names()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "에이전트 목록 조회 중 오류가 발생했습니다."
        }

@router.post("/select-agent")
def process_agent_selection(req: AgentSelectionRequest):
    """사용자가 선택한 에이전트로 쿼리 처리"""
    try:
        # 선택된 에이전트로 다시 처리
        result = state_graph_router.process_query_with_agent(req.query, req.selected_agent)
        
        return {
            "success": True,
            "agent": result.get("selected_agent", req.selected_agent),
            "response": result.get("final_response", ""),
            "message": f"사용자 선택: {req.selected_agent} 에이전트로 처리되었습니다.",
            "query": result.get("query", ""),
            "routing_attempts": result.get("routing_attempts", 0),
            "classification_result": "USER_SELECTED"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "에이전트 선택 처리 중 오류가 발생했습니다."
        }
