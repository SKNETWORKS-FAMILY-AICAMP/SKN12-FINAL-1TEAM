
import os
from fastapi import APIRouter
from pydantic import BaseModel
from ..services.router_agent.state_graph_router import StateGraphRouter
from dotenv import load_dotenv

# OPENAI_API_KEY 확인용 로그
print("router_api.py - OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY")[:10] if os.getenv("OPENAI_API_KEY") else "없음")

# FastAPI 라우터 구성
router = APIRouter()
state_graph_router = StateGraphRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/route/graph")
def route_with_state_graph(req: QueryRequest):
    return state_graph_router.process_query(req.query)
