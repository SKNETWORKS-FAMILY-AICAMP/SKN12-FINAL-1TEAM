from fastapi import APIRouter
from pydantic import BaseModel
from app.services.employee_agent.employee_agent import analyze_employee_query

router = APIRouter()

class QueryOnlyRequest(BaseModel):
    session_id: str
    query: str

@router.post("/analyze")
async def analyze_employee_query_api(request: QueryOnlyRequest):
    """
    사용자 질문 원문을 그대로 전달하여 직원 실적 분석을 요청합니다.
    """
    query = request.query
    result = await analyze_employee_query(query)
    return result
# 
# 