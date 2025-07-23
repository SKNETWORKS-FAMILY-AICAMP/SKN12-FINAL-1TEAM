import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from ..services.client_agent.client_analysis_agent import graph

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
    """클라이언트 분석 API (더미 데이터)"""
    try:
        logger.info(f"클라이언트 분석 요청: {company}")
        
        # 더미 데이터로 분석 결과 생성
        analysis_data = {
            "등급": "A급 (우수)",
            "등급 이유": f"{company.name}은(는) 연간 매출 {company.sales:,}원, 월 평균 방문 {company.visits}회로 우수한 거래 파트너입니다. 안정적인 매출과 지속적인 방문으로 A급으로 분류됩니다.",
            "영업 전략 보고서": f"""📊 {company.name} 영업 전략 보고서

🏢 회사 정보:
• 회사명: {company.name}
• 연간 매출: {company.sales:,}원
• 월 평균 방문: {company.visits}회

📈 영업 전략:
1. 정기 방문 일정 확립 (월 {company.visits}회)
2. 맞춤형 제품 제안 및 기술 지원
3. 연간 계약 갱신 및 장기 파트너십 구축
4. 신제품 우선 공급 및 특별 할인 혜택

🎯 목표:
• 매출 20% 증대 (현재 {company.sales:,}원 → 목표 {int(company.sales * 1.2):,}원)
• 방문 횟수 증가 (현재 {company.visits}회 → 목표 {company.visits + 2}회)
• 신제품 도입 3종 이상

📋 실행 계획:
• 분기별 영업 계획 수립
• 월간 실적 리뷰 및 전략 조정
• 고객 만족도 조사 실시""",
            "성장 요약 보고서": f"""📈 {company.name} 성장 요약 보고서

📊 현재 상황:
• 매출 규모: {company.sales:,}원 (중견 규모)
• 방문 빈도: {company.visits}회/월 (적정 수준)
• 거래 안정성: 우수

🚀 성장 잠재력:
• 시장 확장 가능성: 높음
• 제품 다양화 수용도: 높음
• 기술 도입 의지: 적극적

📋 성장 전략:
1. 신제품 라인업 확대
2. 기술 지원 강화
3. 교육 프로그램 제공
4. 공동 마케팅 활동

🎯 예상 성장률: 연 15-20%""",
            "통합 보고서": f"""📋 {company.name} 통합 분석 보고서

🏢 기본 정보:
• 회사명: {company.name}
• 연간 매출: {company.sales:,}원
• 월 평균 방문: {company.visits}회
• 등급: A급 (우수)

📊 분석 결과:
{company.name}은(는) 안정적인 매출과 지속적인 거래 관계를 보이는 우수한 파트너입니다.

💡 핵심 강점:
• 안정적인 매출 기반
• 정기적인 방문으로 인한 신뢰 관계
• 신제품 도입에 적극적
• 장기 파트너십 가능성 높음

📈 권장사항:
1. 정기 방문 일정 유지 및 강화
2. 맞춤형 제품 제안 확대
3. 기술 지원 및 교육 프로그램 제공
4. 연간 계약 갱신 시 우선권 부여

📄 보고서 다운로드:
• 📎 상세 분석 보고서 (PDF)
• 📊 매출 추이 차트 (Excel)
• 📋 영업 전략 가이드 (Word)

✅ 분석 완료: {company.name}은(는) A급 우수 거래 파트너입니다."""
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