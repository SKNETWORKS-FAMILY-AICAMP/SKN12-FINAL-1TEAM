"""
Employee Agent API Router
직원 실적 분석을 위한 Agent 호출 API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os

# Employee Agent import
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from app.services.employee_agent.employee_agent import EnhancedEmployeeAgent
from app.services.employee_agent.db_manager import EmployeeDBManager

# PostgreSQL 연결용 추가 import (삭제 - EmployeeDBManager 사용)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Employee Performance"])

# Request/Response Models
class AnalyzeRequest(BaseModel):
    """실적 분석 요청"""
    query: str

class PerformanceRequest(BaseModel):
    """실적 데이터 조회 요청"""
    employee_name: str
    start_period: str  # YYYYMM
    end_period: str    # YYYYMM

class TargetRequest(BaseModel):
    """목표 달성률 조회 요청"""
    employee_name: str
    start_period: str  # YYYYMM
    end_period: str    # YYYYMM

# JWT 인증
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = "HS256"

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT 토큰에서 사용자 정보 추출"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        user_email = payload.get("sub")
        user_role = payload.get("role", "user")
        
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # 데이터베이스에서 직원 이름 조회
        with next(get_db()) as db:
            query = text("""
                SELECT name FROM employees 
                WHERE email = :email AND is_deleted = false
            """)
            result = db.execute(query, {"email": user_email}).fetchone()
            
            if result:
                employee_name = result.name
            else:
                employee_name = user_email
        
        return {
            "email": user_email,
            "role": user_role,
            "employee_name": employee_name
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@router.post("/analyze")
async def analyze_employee_performance(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    직원 실적 분석 + 보고서 생성 (메인 기능)
    자연어 쿼리를 받아 직원 실적을 분석하고 종합 보고서를 생성합니다.
    
    권한: 모든 사용자 (본인 데이터만 조회 가능)
    """
    try:
        
        # Agent 실행 (session_id 추가)
        import uuid
        session_id = str(uuid.uuid4())
        agent = EnhancedEmployeeAgent()
        result = await agent.run(request.query, session_id, messages=[])
        
        if result.get("error"):
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
        
        # 권한 체크: 일반 사용자는 본인 데이터만
        if current_user["role"] != "admin":
            employee_name = result.get("employee_name")
            if employee_name and employee_name != current_user["employee_name"]:
                raise HTTPException(
                    status_code=403,
                    detail="본인의 실적만 조회할 수 있습니다."
                )
        
        # API 명세에 맞는 응답 형식으로 변환
        response = {
            "employee_name": result.get("employee_name"),
            "period": f"{result.get('start_period')}~{result.get('end_period')}",
            "performance_data": result.get("performance_data"),
            "target_data": result.get("target_data"),
            "analysis_results": result.get("analysis_results"),
            "report": result.get("report"),
            "summary": {
                "achievement_rate": result.get("target_data", {}).get("achievement_rate"),
                "grade": result.get("target_data", {}).get("grade"),
                "evaluation": result.get("target_data", {}).get("evaluation")
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/list")
async def get_employee_list(
    current_user: dict = Depends(get_current_user)
):
    """
    직원 목록 조회 (관리자 전용)
    전체 직원의 기본 정보를 조회합니다.
    
    권한: 관리자만
    """
    try:
        
        # 권한 체크
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=403,
                detail="관리자만 직원 목록을 조회할 수 있습니다."
            )
        
        # EmployeeDBManager를 사용하여 직원 목록 조회
        db_manager = EmployeeDBManager()
        employees = db_manager.get_all_employees()
        
        # 응답 형식에 맞게 변환
        employee_list = []
        for emp in employees:
            employee_list.append({
                "employee_id": emp["employee_id"],
                "name": emp["name"],
                "사번": emp["employee_number"],
                "department": emp["department"]
            })
        
        return {"employees": employee_list}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get employee list: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"직원 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/performance")
async def get_performance_detail(
    request: PerformanceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    실적 상세 데이터 조회
    특정 직원의 기간별 실적 상세 데이터를 조회합니다.
    
    권한: 모든 사용자 (본인 데이터만 조회 가능)
    """
    try:
        
        # 권한 체크: 일반 사용자는 본인 데이터만
        if current_user["role"] != "admin":
            if request.employee_name != current_user["employee_name"]:
                raise HTTPException(
                    status_code=403,
                    detail="본인의 실적만 조회할 수 있습니다."
                )
        
        # DB Manager로 실적 데이터 조회
        db_manager = EmployeeDBManager()
        
        # 실적 데이터 조회
        performance_data = db_manager.get_employee_performance(
            employee_name=request.employee_name,
            start_period=request.start_period,
            end_period=request.end_period
        )
        
        if not performance_data:
            raise HTTPException(
                status_code=404,
                detail=f"직원 '{request.employee_name}'의 실적 데이터를 찾을 수 없습니다."
            )
        
        # 월별 데이터 구성
        monthly_data = []
        total_amount = 0
        
        for month_data in performance_data.get("monthly_breakdown", []):
            amount = month_data.get("amount", 0)
            total_amount += amount
            monthly_data.append({
                "month": month_data.get("month"),
                "amount": amount,
                "count": 1
            })
        
        # 제품별 데이터
        product_data = []
        for product in performance_data.get("product_breakdown", []):
            percentage = (product["amount"] / total_amount * 100) if total_amount > 0 else 0
            product_data.append({
                "product": product["name"],
                "amount": product["amount"],
                "percentage": round(percentage, 1)
            })
        
        # 거래처별 데이터
        client_data = []
        for client in performance_data.get("client_breakdown", []):
            percentage = (client["amount"] / total_amount * 100) if total_amount > 0 else 0
            client_data.append({
                "client": client["name"],
                "amount": client["amount"],
                "percentage": round(percentage, 1)
            })
        
        return {
            "summary": {
                "total_amount": total_amount,
                "total_count": len(monthly_data),
                "average_amount": total_amount // len(monthly_data) if monthly_data else 0
            },
            "monthly_data": monthly_data,
            "product_data": product_data,
            "client_data": client_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"실적 데이터 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/target")
async def get_target_achievement(
    request: TargetRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    목표 달성률 데이터 조회 (관리자 전용)
    특정 직원의 기간별 목표 달성률을 조회합니다.
    
    권한: 관리자만
    """
    try:
        
        # 권한 체크
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=403,
                detail="관리자만 목표 달성률을 조회할 수 있습니다."
            )
        
        # DB Manager로 목표 데이터 조회
        db_manager = EmployeeDBManager()
        
        # 목표 데이터 조회
        target_data = db_manager.get_employee_targets(
            employee_name=request.employee_name,
            start_period=request.start_period,
            end_period=request.end_period
        )
        
        if not target_data:
            raise HTTPException(
                status_code=404,
                detail=f"직원 '{request.employee_name}'의 목표 데이터를 찾을 수 없습니다."
            )
        
        # 월별 목표 달성률 데이터 구성
        monthly_target_data = []
        total_target = 0
        total_actual = 0
        achieved_months = 0
        
        for month_data in target_data.get("monthly_targets", []):
            month = month_data["month"]
            target = month_data["target"]
            actual = month_data["actual"]
            achievement_rate = (actual / target * 100) if target > 0 else 0
            
            monthly_target_data.append({
                "month": month,
                "target": target,
                "actual": actual,
                "achievement_rate": round(achievement_rate, 1)
            })
            
            total_target += target
            total_actual += actual
            if achievement_rate >= 100:
                achieved_months += 1
        
        # 전체 요약
        overall_achievement = (total_actual / total_target * 100) if total_target > 0 else 0
        
        # 평가 등급 결정
        if overall_achievement >= 120:
            evaluation = "매우 우수"
            grade = "S"
        elif overall_achievement >= 100:
            evaluation = "우수"
            grade = "A"
        elif overall_achievement >= 80:
            evaluation = "양호"
            grade = "B"
        elif overall_achievement >= 60:
            evaluation = "보통"
            grade = "C"
        else:
            evaluation = "개선 필요"
            grade = "D"
        
        return {
            "target_data": monthly_target_data,
            "summary": {
                "total_target": total_target,
                "total_actual": total_actual,
                "overall_achievement": round(overall_achievement, 1),
                "achieved_months": achieved_months,
                "total_months": len(monthly_target_data),
                "evaluation": evaluation,
                "grade": grade
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get target data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"목표 데이터 조회 중 오류가 발생했습니다: {str(e)}"
        )