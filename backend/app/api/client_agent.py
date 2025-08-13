"""
Client Agent API - 거래처 분석 및 보고서 생성 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Client Agent 임포트
from app.services.client_agent.client_agent_v1 import ClientAgent, run_full_pipeline

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 라우터 생성
router = APIRouter(prefix="/client", tags=["client-agent"])

# 전역 Client Agent 인스턴스
client_agent = ClientAgent()


# Request/Response 모델
class ClientAnalysisRequest(BaseModel):
    """거래처 분석 요청 모델"""
    query: str
    generate_docs: bool = True
    output_dir: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "서울대병원 202401부터 202412까지 분석해줘",
                "generate_docs": True,
                "output_dir": "./output"
            }
        }


class ClientAnalysisResponse(BaseModel):
    """거래처 분석 응답 모델"""
    success: bool
    company_name: Optional[str] = None
    start_month: Optional[int] = None
    end_month: Optional[int] = None
    final_report: Optional[str] = None
    documents: Optional[Dict[str, str]] = None
    grade_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/analyze", response_model=ClientAnalysisResponse)
async def analyze_client(request: ClientAnalysisRequest) -> ClientAnalysisResponse:
    """
    거래처를 분석하고 종합 보고서를 생성합니다.
    
    Args:
        request: 거래처 분석 요청
        
    Returns:
        ClientAnalysisResponse: 분석 결과 및 보고서
    """
    try:
        logger.info(f"[CLIENT-ANALYSIS] 요청 수신: {request.query}")
        
        # 파이프라인 실행
        result = await run_full_pipeline(
            client_agent,
            user_input=request.query,
            generate_docs=request.generate_docs,
            output_dir=request.output_dir
        )
        
        report_state = result.get("report_state", {})
        documents = result.get("documents", {})
        
        # 응답 구성
        response = ClientAnalysisResponse(
            success=True,
            company_name=report_state.get("company_name"),
            start_month=report_state.get("start_month"),
            end_month=report_state.get("end_month"),
            final_report=report_state.get("final_report"),
            documents=documents,
            grade_result=report_state.get("grade_result"),
            metadata={
                "analysis_timestamp": datetime.now().isoformat(),
                "generated_docs": request.generate_docs,
                "output_dir": documents.get("output_dir") if documents else request.output_dir
            }
        )
        
        logger.info(f"[CLIENT-ANALYSIS] 분석 완료: {response.company_name}")
        return response
        
    except Exception as e:
        logger.error(f"[CLIENT-ANALYSIS] 오류 발생: {str(e)}")
        return ClientAnalysisResponse(
            success=False,
            error=f"거래처 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Client Agent 서비스의 헬스 체크
    
    Returns:
        Dict: 서비스 상태
    """
    try:
        # 데이터 로드 상태 확인
        data_loaded = not client_agent.df.empty
        data_count = len(client_agent.df) if data_loaded else 0
        
        return {
            "status": "healthy",
            "service": "client-agent",
            "version": "1.0.0",
            "data_loaded": data_loaded,
            "data_count": data_count,
            "api_configured": client_agent._is_api_configured(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "client-agent",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }