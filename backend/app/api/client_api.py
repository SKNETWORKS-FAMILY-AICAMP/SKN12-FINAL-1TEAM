import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from services.client_agent.client_analysis_agent import graph

# .env 로드 (현재 경로와 상위 경로에서 찾기)
current_env = Path(__file__).parent / ".env"
parent_env = Path(__file__).resolve().parents[1] / ".env"

if current_env.exists():
    load_dotenv(dotenv_path=current_env)
    print(f"✅ client_api.py - .env 로드됨: {current_env}")
elif parent_env.exists():
    load_dotenv(dotenv_path=parent_env)
    print(f"✅ client_api.py - .env 로드됨: {parent_env}")
else:
    print("⚠️ client_api.py - .env 파일을 찾을 수 없습니다")

# OPENAI_API_KEY 확인용 로그
print("client_api.py - OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY")[:10] if os.getenv("OPENAI_API_KEY") else "없음")

logger = logging.getLogger(__name__)

router = APIRouter()

class CompanyInput(BaseModel):
    name: str
    sales: int
    visits: int

class ClientAnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str

@router.get("/health")
async def client_health_check():
    """Client Agent 헬스 체크"""
    try:
        return {
            "status": "healthy",
            "agent": "Client Analysis Agent",
            "service": "running"
        }
    except Exception as e:
        logger.error(f"Client Agent 헬스 체크 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Client Agent 오류: {str(e)}")

@router.post("/analyze", response_model=ClientAnalysisResponse)
async def analyze_client(company: CompanyInput):
    """클라이언트 분석 API"""
    try:
        logger.info(f"클라이언트 분석 요청: {company}")
        
        first_state = {
            "target_company": {
                "name": company.name,
                "sales": company.sales,
                "visits": company.visits
            }
        }

        final_state = await graph.ainvoke(first_state)

        analysis_data = {
            "등급": final_state.get("rating"),
            "등급 이유": final_state.get("grade_reason_report"),
            "영업 전략 보고서": final_state.get("sales_strategy_report"),
            "성장 요약 보고서": final_state.get("growth_summary_report"),
            "통합 보고서": final_state.get("merged_report")
        }

        return ClientAnalysisResponse(
            success=True,
            data=analysis_data,
            message="클라이언트 분석이 완료되었습니다."
        )

    except Exception as e:
        logger.error(f"클라이언트 분석 오류: {str(e)}")
        return ClientAnalysisResponse(
            success=False,
            error=str(e),
            message="클라이언트 분석 중 오류가 발생했습니다."
        )

@router.post("/run-report")
async def run_report(company: CompanyInput):
    """기존 호환성을 위한 레거시 엔드포인트"""
    try:
        result = await analyze_client(company)
        if result.success:
            return result.data
        else:
            raise HTTPException(status_code=500, detail=result.error)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))