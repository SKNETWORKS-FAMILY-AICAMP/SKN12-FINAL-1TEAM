"""
Simple API for client analysis
"""
from fastapi import APIRouter
from typing import Optional
import logging

from .client_agent import ClientAgent, run_full_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/client-analysis", tags=["client-analysis"])

# ClientAgent 인스턴스
client_agent = ClientAgent()

@router.post("/analyze")
async def analyze_client(
    company_name: str,
    start_month: Optional[int] = None,
    end_month: Optional[int] = None
):
    """
    거래처 분석 실행
    
    Parameters:
    - company_name: 거래처명
    - start_month: 시작월 (예: 202401)
    - end_month: 종료월 (예: 202403)
    """
    result = await run_full_pipeline(
        agent=client_agent,
        company_name=company_name,
        start_month=start_month,
        end_month=end_month
    )
    
    return result