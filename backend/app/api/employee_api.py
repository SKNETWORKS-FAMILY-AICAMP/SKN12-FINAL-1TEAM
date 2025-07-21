
import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional, Dict, Any

# .env 로드 (현재 경로와 상위 경로에서 찾기)
current_env = Path(__file__).parent / ".env"
parent_env = Path(__file__).resolve().parents[1] / ".env"

if current_env.exists():
    load_dotenv(dotenv_path=current_env)
    print(f"✅ employee_api.py - .env 로드됨: {current_env}")
elif parent_env.exists():
    load_dotenv(dotenv_path=parent_env)
    print(f"✅ employee_api.py - .env 로드됨: {parent_env}")
else:
    print("⚠️ employee_api.py - .env 파일을 찾을 수 없습니다")

# OPENAI_API_KEY 확인용 로그
print("employee_api.py - OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY")[:10] if os.getenv("OPENAI_API_KEY") else "없음")

# Employee Agent import
from services.employee_agent.employee_agent import EmployeePerformanceAgent

logger = logging.getLogger(__name__)

# Employee 전용 라우터 생성
router = APIRouter()

# Employee Agent 인스턴스 생성 (lazy loading)
employee_agent = None

def get_employee_agent():
    global employee_agent
    if employee_agent is None:
        try:
            logger.info("Employee Agent 인스턴스 생성 시작...")
            employee_agent = EmployeePerformanceAgent()
            logger.info("Employee Agent 인스턴스 생성 성공")
        except Exception as e:
            logger.error(f"Employee Agent 인스턴스 생성 실패: {e}")
            import traceback
            logger.error(f"오류 상세: {traceback.format_exc()}")
            raise e
    return employee_agent

# Pydantic 모델 정의
class EmployeeAnalysisRequest(BaseModel):
    employee_name: Optional[str] = None
    period: Optional[str] = None
    save_report: bool = False
    filename: Optional[str] = None

class EmployeeAnalysisResponse(BaseModel):
    success: bool
    analysis_result: Optional[Dict[str, Any]] = None
    report: Optional[str] = None
    error: Optional[str] = None
    message: str

@router.get("/health")
async def employee_health_check():
    """Employee Agent 헬스 체크"""
    try:
        # Employee Agent 인스턴스 가져오기
        agent = get_employee_agent()
        
        # 기본 데이터 로드 테스트
        performance_data = agent.load_performance_data()
        target_data = agent.load_target_data()
        
        return {
            "status": "healthy",
            "agent": "Employee Performance Agent",
            "data_status": {
                "performance_data": "loaded" if not performance_data.empty else "empty",
                "target_data": "loaded" if not target_data.empty else "empty"
            }
        }
    except Exception as e:
        logger.error(f"Employee Agent 헬스 체크 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Employee Agent 오류: {str(e)}")

@router.get("/performance/summary")
async def get_employee_performance_summary():
    """직원 실적 요약 정보 조회"""
    try:
        logger.info("실적 요약 조회 시작")
        
        # Employee Agent 인스턴스 가져오기
        logger.info("Employee Agent 인스턴스 가져오는 중...")
        agent = get_employee_agent()
        logger.info("Employee Agent 인스턴스 가져오기 성공")
        
        # 기본 실적 정보 조회
        logger.info("총 실적 계산 중...")
        total_performance = agent._get_total_performance()
        logger.info(f"총 실적: {total_performance}")
        
        logger.info("총 목표 계산 중...")
        total_target = agent._get_total_target()
        logger.info(f"총 목표: {total_target}")
        
        logger.info("달성률 계산 중...")
        achievement_rate = agent._get_achievement_rate()
        logger.info(f"달성률: {achievement_rate}")
        
        result = {
            "success": True,
            "summary": {
                "employee_name": "최수아",
                "period": "2023년 12월 ~ 2024년 3월",
                "total_performance": float(total_performance),
                "total_target": float(total_target),
                "achievement_rate": float(achievement_rate),
                "status": "급증" if achievement_rate > 120 else "안정" if achievement_rate >= 80 else "미달성"
            }
        }
        
        logger.info("실적 요약 조회 완료")
        return result
        
    except Exception as e:
        logger.error(f"실적 요약 조회 오류: {str(e)}")
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"오류 상세: {error_detail}")
        return {
            "success": False,
            "error": str(e),
            "detail": error_detail,
            "message": "실적 요약 조회 중 오류가 발생했습니다."
        }

@router.post("/analyze", response_model=EmployeeAnalysisResponse)
async def analyze_employee_performance(request: EmployeeAnalysisRequest):
    """직원 실적 분석 API"""
    try:
        logger.info(f"직원 실적 분석 요청: {request}")
        
        # Employee Agent 인스턴스 가져오기
        agent = get_employee_agent()
        
        # 실적 분석 실행
        result = agent.run_analysis()
        
        if result.get("error"):
            return EmployeeAnalysisResponse(
                success=False,
                error=result["error"],
                message="분석 중 오류가 발생했습니다."
            )
        
        analysis_result = result.get("analysis_result", {})
        report = result.get("report", "")
        
        # numpy 타입을 Python 기본 타입으로 변환
        def convert_numpy_types(obj):
            import numpy as np
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        # analysis_result의 numpy 타입 변환
        analysis_result = convert_numpy_types(analysis_result)
        
        # 보고서 저장 요청이 있는 경우
        if request.save_report and report:
            filename = request.filename or "실적분석보고서.docx"
            save_result = agent.save_report_to_docx(report, filename)
            message = f"분석 완료. {save_result}"
        else:
            message = "직원 실적 분석이 완료되었습니다."
        
        return EmployeeAnalysisResponse(
            success=True,
            analysis_result=analysis_result,
            report=report,
            message=message
        )
        
    except Exception as e:
        logger.error(f"직원 실적 분석 오류: {str(e)}")
        return EmployeeAnalysisResponse(
            success=False,
            error=str(e),
            message="서버 오류가 발생했습니다."
        )

@router.post("/report/generate")
async def generate_employee_report(request: EmployeeAnalysisRequest):
    """직원 실적 보고서 생성 및 다운로드"""
    try:
        # Employee Agent 인스턴스 가져오기
        agent = get_employee_agent()
        
        # 분석 실행
        result = agent.run_analysis()
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        report = result.get("report", "")
        if not report:
            raise HTTPException(status_code=400, detail="보고서 생성에 실패했습니다.")
        
        # Word 문서로 저장
        filename = request.filename or "최수아_실적분석보고서.docx"
        save_result = agent.save_report_to_docx(report, filename)
        
        return {
            "success": True,
            "message": save_result,
            "filename": filename,
            "report_preview": report[:500] + "..." if len(report) > 500 else report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}") 