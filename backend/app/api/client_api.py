from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.client_agent.client_analysis_agent import analyze_client_query

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/analyze")
async def analyze_client_query_api(request: QueryRequest):
    """
    사용자 질문을 기반으로 거래처 분석 결과를 반환합니다.
    LLM 호출 및 파라미터 추출은 내부 에이전트가 처리합니다.
    """
    try:
        result = await analyze_client_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
