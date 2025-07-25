from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
# 기존 에이전트 대신 새로운 에이전트 사용
from ..services.employee_agent.employee_agent import analyze_employee_query

router = APIRouter()

class QueryOnlyRequest(BaseModel):
    session_id: str
    query: str

class AnalyzeRequest(BaseModel):
    """직원 실적 분석 요청"""
    session_id: str
    query: str
    employee_name: Optional[str] = None
    period: Optional[str] = None
    analysis_type: Optional[str] = None

@router.post("/analyze")
async def analyze_employee_query_api(request: QueryOnlyRequest):
    """
    사용자 질문을 분석하여 직원 실적 분석을 수행합니다.
    
    새로운 기능:
    - 자동 쿼리 분석 (직원명, 기간, 분석 유형 추출)
    - SQLite 기반 데이터 로드
    - 고급 계산 도구 (트렌드, 파레토, 예측 분석 등)
    - LLM 기반 지능형 보고서 생성
    - 종합 평가 및 점수 시스템
    """
    try:
        # 새로운 에이전트를 사용하여 분석 수행
        result = await analyze_employee_query(request.query)
        
        # API 응답 형식에 맞게 변환
        if result.get("success"):
            return {
                "success": True,
                "employee_name": result.get("employee_name"),
                "period": result.get("period"),
                "total_performance": result.get("total_performance", 0),
                "achievement_rate": result.get("achievement_rate", 0),
                "evaluation": result.get("evaluation"),
                "report": result.get("report"),
                "analysis_details": result.get("analysis_details", {}),
                "message": result.get("message")
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "message": result.get("message", "분석 처리 중 오류가 발생했습니다.")
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "API 처리 중 오류가 발생했습니다."
        }

@router.get("/health")
async def health_check():
    """직원 실적 분석 에이전트 헬스 체크"""
    try:
        # 기본적인 시스템 상태 확인
        from app.services.employee_agent.db_manager import EmployeeDBManager
        
        db_manager = EmployeeDBManager()
        employees = db_manager.get_available_employees()
        
        return {
            "status": "healthy",
            "agent": "Enhanced Employee Performance Agent",
            "database_status": "connected",
            "available_employees": employees,
            "total_employees": len(employees),
            "features": [
                "자동 쿼리 분석",
                "SQLite 기반 데이터 처리",
                "고급 통계 분석",
                "LLM 기반 보고서",
                "종합 평가 시스템"
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "agent": "Enhanced Employee Performance Agent",
            "error": str(e)
        }

@router.get("/employees")
async def get_available_employees():
    """사용 가능한 직원 목록 조회"""
    try:
        from app.services.employee_agent.db_manager import EmployeeDBManager
        
        db_manager = EmployeeDBManager()
        employees = db_manager.get_available_employees()
        
        return {
            "success": True,
            "employees": employees,
            "count": len(employees),
            "message": f"{len(employees)}명의 직원 데이터가 있습니다."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "직원 목록 조회 중 오류가 발생했습니다."
        }

@router.post("/analyze-detailed")
async def analyze_detailed(request: AnalyzeRequest):
    """
    상세 분석 요청 (추가 파라미터 지원)
    """
    try:
        # 기본 쿼리에 추가 정보 포함
        enhanced_query = request.query
        
        if request.employee_name:
            enhanced_query += f" (직원: {request.employee_name})"
        if request.period:
            enhanced_query += f" (기간: {request.period})"
        if request.analysis_type:
            enhanced_query += f" (분석유형: {request.analysis_type})"
        
        result = await analyze_employee_query(enhanced_query)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "상세 분석 처리 중 오류가 발생했습니다."
        }