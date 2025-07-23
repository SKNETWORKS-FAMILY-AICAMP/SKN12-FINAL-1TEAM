
import os
from fastapi import APIRouter
from pydantic import BaseModel
from ..services.router_agent.state_graph_router import StateGraphRouter
from dotenv import load_dotenv

# OPENAI_API_KEY 확인
api_key = os.getenv("OPENAI_API_KEY")
print("router_api.py - OPENAI_API_KEY:", api_key[:10] + "..." if api_key else "없음")

# FastAPI 라우터 구성
router = APIRouter()
state_graph_router = StateGraphRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/router")
def route_with_state_graph(req: QueryRequest):
    """쿼리를 분석하고 적절한 에이전트로 라우팅"""
    try:
        result = state_graph_router.process_query(req.query)
        
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
