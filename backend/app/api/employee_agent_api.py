
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
    employee_name: Optional[str] = None  # 직원명 추가
    employee_info_id: Optional[int] = None  # 직원 ID 직접 지정

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
# 데이터베이스 서버와 동일한 JWT_SECRET_KEY 사용
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "n!CnQ1>(DOcrbITm4]2bUxt[yTF+9,Gu^5s8Duo&27ZK8yCah5Qc-vNd=#.?w(*Ks")
JWT_ALGORITHM = "HS256"

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT 토큰에서 사용자 정보 추출"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        user_email = payload.get("sub")
        user_role = payload.get("role", "user")
        user_name = payload.get("name", user_email)  # name이 payload에 있으면 사용
        
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # employees 테이블에서 실제 이름 조회
        employee_name = user_name  # 기본값
        employee_number = None
        employee_info_id = None
        
        try:
            from sqlalchemy import create_engine, text
            POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
            POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword")
            POSTGRES_DB = os.getenv("POSTGRES_DB", "mydatabase")
            POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
            POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
            
            DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
            engine = create_engine(DATABASE_URL)
            
            with engine.connect() as conn:
                # employees 테이블에서 이름 조회 (원래대로)
                result = conn.execute(
                    text("SELECT name FROM employees WHERE email = :email"),
                    {"email": user_email}
                )
                row = result.fetchone()
                if row:
                    employee_name = row[0]
                    logger.info(f"Found employee name from DB: {employee_name}")
                    
                    # 이름이 같은 직원이 여러 명일 때, sales_records에 데이터가 있는 직원 선택
                    emp_info_result = conn.execute(
                        text("""
                            SELECT DISTINCT ei.employee_info_id, ei.name, ei.employee_number,
                                   COUNT(sr.record_id) as sale_count
                            FROM employee_info ei
                            LEFT JOIN sales_records sr ON sr.employee_id = ei.employee_info_id
                            WHERE ei.name = :name
                            GROUP BY ei.employee_info_id, ei.name, ei.employee_number
                            ORDER BY sale_count DESC
                            LIMIT 1
                        """),
                        {"name": employee_name}
                    )
                    emp_info_row = emp_info_result.fetchone()
                    if emp_info_row:
                        employee_info_id = emp_info_row[0]
                        employee_number = emp_info_row[2]
                        logger.info(f"Selected employee_info: id={employee_info_id}, name={employee_name}, employee_number={employee_number}, sale_count={emp_info_row[3]}")
        except Exception as e:
            logger.warning(f"Failed to get employee info from DB: {e}")
        
        logger.info(f"Token decoded - email: {user_email}, role: {user_role}, employee_name: {employee_name}, employee_number: {employee_number}, employee_info_id: {employee_info_id}")
        
        return {
            "email": user_email,
            "role": user_role,
            "employee_name": employee_name,
            "employee_number": employee_number,
            "employee_info_id": employee_info_id
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
        # 디버깅 로그
        logger.info(f"Current user: {current_user}")
        logger.info(f"Request query: {request.query}")
        logger.info(f"Request employee_name: {request.employee_name}")
        
        # employee_info_id가 제공된 경우 (중복 직원 선택 후)
        if request.employee_info_id:
            # DB에서 해당 직원 정보 조회
            from sqlalchemy import text
            db_manager = EmployeeDBManager()
            with db_manager.get_connection() as db:
                result = db.execute(
                    text("SELECT name, employee_number FROM employee_info WHERE employee_info_id = :id"),
                    {"id": request.employee_info_id}
                ).fetchone()
                
                if result:
                    employee_name = result[0]
                    # 쿼리에 직원명 추가
                    if employee_name not in request.query:
                        query = f"{employee_name}의 {request.query}"
                    else:
                        query = request.query
                    logger.info(f"Using selected employee: {employee_name} (ID: {request.employee_info_id})")
        else:
            # 일반 사용자인 경우 쿼리에 본인 이름 자동 추가
            query = request.query
            if current_user["role"] != "admin":
                current_employee = current_user.get("employee_name", "")
                
                # 쿼리에 다른 직원명이 포함되어 있는지 검사
                import re
                # 한글 이름 패턴 (예: 김철수, 이영희 등)
                name_pattern = r'[\uac00-\ud7af]{2,4}(?:의|\s)'
                found_names = re.findall(name_pattern, query)
                
                # 찾은 이름 중 현재 사용자가 아닌 이름이 있는지 확인
                for name in found_names:
                    cleaned_name = name.replace('의', '').strip()
                    if cleaned_name and cleaned_name != current_employee:
                        logger.warning(f"타인 데이터 조회 시도 차단: {cleaned_name} != {current_employee}")
                        raise HTTPException(
                            status_code=403,
                            detail="본인의 실적만 조회할 수 있습니다. 다른 직원의 이름을 언급하지 마세요."
                        )
                
                # 쿼리에 직원명이 없으면 현재 사용자의 이름을 추가
                if current_employee and current_employee not in query:
                    # "실적 분석" 같은 쿼리를 "조시현의 실적 분석"으로 변경
                    query = f"{current_employee}의 {query}"
                    logger.info(f"Query modified for user: {query}")
        
        # Agent 실행 (session_id 추가)
        import uuid
        session_id = str(uuid.uuid4())
        agent = EnhancedEmployeeAgent()
        
        # employee_info_id가 있으면 agent에 전달
        if request.employee_info_id:
            agent.employee_info_id = request.employee_info_id
            
        result = await agent.run(query, session_id, messages=[])
        
        if result.get("error"):
            error_msg = result["error"]
            
            # employee_info_id가 제공된 경우는 이미 선택한 것이므로 중복 확인 불필요
            if not request.employee_info_id:
                # 중복 직원 감지 로직 (employee_info_id가 없을 때만)
                if "직원의" in error_msg and "실적 데이터가 없습니다" in error_msg:
                    # 직원명 추출
                    import re
                    match = re.search(r"'([^']+)' 직원의", error_msg)
                    if match:
                        employee_name = match.group(1)
                        # 중복 직원 확인
                        db_manager = EmployeeDBManager()
                        candidates = db_manager.find_employees_by_name(employee_name)
                        
                        if len(candidates) > 1:
                            # 중복 직원 발견 - 선택 필요
                            return {
                                "status": "requires_selection",
                                "message": f"'{employee_name}' 이름의 직원이 {len(candidates)}명 있습니다. 선택해주세요.",
                                "candidates": candidates
                            }
            
            # 실적 데이터 없음 메시지를 더 명확하게 표시
            if "실적 데이터가 없습니다" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=error_msg
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=error_msg
                )
        
        # 권한 체크: 일반 사용자는 본인 데이터만
        if current_user["role"] != "admin":
            employee_name = result.get("employee_name", "")
            current_employee_name = current_user.get("employee_name", "")
            
            logger.info(f"권한 체크 - 요청된 직원: '{employee_name}', 현재 사용자: '{current_employee_name}', role: {current_user['role']}")
            
            # 두 이름이 모두 있고 다른 경우에만 차단
            if employee_name and current_employee_name:
                # 이름 정규화 (공백 제거, 소문자 변환)
                normalized_employee = employee_name.strip().lower()
                normalized_current = current_employee_name.strip().lower()
                
                if normalized_employee == normalized_current:
                    logger.info(f"본인 데이터 조회 허용: {employee_name}")
                else:
                    logger.warning(f"타인 데이터 조회 시도 차단: {employee_name} != {current_employee_name}")
                    raise HTTPException(
                        status_code=403,
                        detail=f"본인의 실적만 조회할 수 있습니다."
                    )
            else:
                logger.info(f"권한 체크 스킵 (정보 부족): employee_name={employee_name}, current={current_employee_name}")
        
        # API 명세에 맞는 응답 형식으로 변환
        # analysis_details에서 실제 데이터 추출
        analysis_details = result.get("analysis_details", {})
        achievement_analysis = analysis_details.get("achievement_analysis", {})
        
        # performance_data 확인 및 전달
        performance_data = None
        if "performance_data" in analysis_details:
            performance_data = analysis_details["performance_data"]
        elif result.get("response") and "performance_data" in result:
            performance_data = result["performance_data"]
        
        response = {
            "employee_name": result.get("employee_name"),
            "period": result.get("period", f"{result.get('start_period')}~{result.get('end_period')}"),
            "performance_data": performance_data,
            "target_data": {
                "achievement_rate": result.get("achievement_rate", achievement_analysis.get("achievement_rate", 0)),
                "total_target": achievement_analysis.get("total_target", 0),
                "total_performance": achievement_analysis.get("total_performance", result.get("total_performance", 0)),
                "grade": achievement_analysis.get("grade", result.get("evaluation", "N/A")),
                "evaluation": achievement_analysis.get("evaluation", result.get("evaluation", "평가 불가"))
            },
            "analysis_results": analysis_details,
            "report": result.get("report"),
            "summary": {
                "achievement_rate": result.get("achievement_rate", achievement_analysis.get("achievement_rate", 0)),
                "grade": achievement_analysis.get("grade", "N/A"),
                "evaluation": achievement_analysis.get("evaluation", result.get("evaluation", "평가 불가"))
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
        
        # 현재 사용자의 employee_info_id 사용 (일반 사용자인 경우)
        employee_info_id = None
        if current_user["role"] != "admin" and current_user.get("employee_info_id"):
            employee_info_id = current_user["employee_info_id"]
        
        # 실적 데이터 조회
        performance_data = db_manager.get_employee_performance(
            employee_name=request.employee_name,
            start_period=request.start_period,
            end_period=request.end_period,
            employee_info_id=employee_info_id
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
    목표 달성률 데이터 조회
    특정 직원의 기간별 목표 달성률을 조회합니다.
    
    권한: 모든 사용자 (본인 데이터만 조회 가능)
    """
    try:
        
        # 권한 체크: 일반 사용자는 본인 데이터만
        if current_user["role"] != "admin":
            if request.employee_name != current_user["employee_name"]:
                raise HTTPException(
                    status_code=403,
                    detail="본인의 목표 달성률만 조회할 수 있습니다."
                )
        
        # DB Manager로 목표 데이터 조회
        db_manager = EmployeeDBManager()
        
        # 현재 사용자의 employee_info_id 사용 (일반 사용자인 경우)
        employee_info_id = None
        if current_user["role"] != "admin" and current_user.get("employee_info_id"):
            employee_info_id = current_user["employee_info_id"]
        
        # 목표 데이터 조회
        target_data = db_manager.get_employee_targets(
            employee_name=request.employee_name,
            start_period=request.start_period,
            end_period=request.end_period,
            employee_info_id=employee_info_id
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

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    대시보드 통계 데이터 조회
    직원의 주요 성과 지표를 조회합니다.
    
    권한: 모든 사용자 (본인 데이터만 조회)
    """
    try:
        db_manager = EmployeeDBManager()
        
        # 현재 월과 이전 월 계산 (데이터가 2024년 11월까지 있으므로 임시로 2024년 11월 사용)
        from datetime import datetime, timedelta
        # now = datetime.now()
        # 임시로 2024년 11월로 설정
        now = datetime(2024, 11, 15)
        current_month = now.strftime("%Y%m")  # 202411
        
        # 이전 월 계산
        first_day_current = now.replace(day=1)
        last_month_date = first_day_current - timedelta(days=1)
        last_month = last_month_date.strftime("%Y%m")  # 202410
        
        # 현재 분기 계산 (최근 3개월)
        quarter_start_date = now - timedelta(days=90)
        quarter_start = quarter_start_date.strftime("%Y%m")  # 202408
        
        employee_name = current_user["employee_name"]
        employee_info_id = current_user.get("employee_info_id")
        
        # 1. 목표 달성률 (현재 월)
        target_data = db_manager.get_employee_targets(
            employee_name=employee_name,
            start_period=current_month,
            end_period=current_month,
            employee_info_id=employee_info_id
        )
        
        achievement_rate = 0
        achievement_change = 0
        
        if target_data and target_data.get("monthly_targets"):
            current_target = target_data["monthly_targets"][0]
            achievement_rate = round((current_target["actual"] / current_target["target"] * 100) if current_target["target"] > 0 else 0, 1)
        
        # 이전 월 달성률과 비교
        last_target_data = db_manager.get_employee_targets(
            employee_name=employee_name,
            start_period=last_month,
            end_period=last_month,
            employee_info_id=employee_info_id
        )
        
        if last_target_data and last_target_data.get("monthly_targets"):
            last_target = last_target_data["monthly_targets"][0]
            last_achievement = (last_target["actual"] / last_target["target"] * 100) if last_target["target"] > 0 else 0
            achievement_change = round(achievement_rate - last_achievement, 1)
        
        # 2. 매출 증감률 (전월 대비)
        current_performance = db_manager.get_employee_performance(
            employee_name=employee_name,
            start_period=current_month,
            end_period=current_month,
            employee_info_id=employee_info_id
        )
        
        last_performance = db_manager.get_employee_performance(
            employee_name=employee_name,
            start_period=last_month,
            end_period=last_month,
            employee_info_id=employee_info_id
        )
        
        current_sales = current_performance.get("total_performance", 0) if current_performance else 0
        last_sales = last_performance.get("total_performance", 0) if last_performance else 0
        
        sales_growth = 0
        if last_sales > 0:
            sales_growth = round((current_sales - last_sales) / last_sales * 100, 1)
        
        # 3. 분기 총 실적
        quarter_performance = db_manager.get_employee_performance(
            employee_name=employee_name,
            start_period=quarter_start,
            end_period=current_month,
            employee_info_id=employee_info_id
        )
        
        quarter_total = quarter_performance.get("total_performance", 0) if quarter_performance else 0
        
        # 4. 거래처 수 (활성 거래처)
        client_count = 0
        if quarter_performance and quarter_performance.get("client_breakdown"):
            client_count = len(quarter_performance["client_breakdown"])
        
        return {
            "stats": [
                {
                    "title": "목표 달성률",
                    "value": f"{achievement_rate}%",
                    "change": f"{'+' if achievement_change >= 0 else ''}{achievement_change}%",
                    "trend": "up" if achievement_change > 0 else "down" if achievement_change < 0 else "neutral",
                    "period": "이번 달"
                },
                {
                    "title": "매출 증감률",
                    "value": f"{'+' if sales_growth >= 0 else ''}{sales_growth}%",
                    "change": f"₩{current_sales:,.0f}",
                    "trend": "up" if sales_growth > 0 else "down" if sales_growth < 0 else "neutral",
                    "period": "전월 대비"
                },
                {
                    "title": "분기 총 실적",
                    "value": f"₩{quarter_total:,.0f}",
                    "change": f"{client_count}개 거래처",
                    "trend": "neutral",
                    "period": "최근 3개월"
                }
            ],
            "period": {
                "current": current_month,
                "last": last_month,
                "quarter_start": quarter_start
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        # 오류 시 기본값 반환
        return {
            "stats": [
                {
                    "title": "목표 달성률",
                    "value": "0%",
                    "change": "0%",
                    "trend": "neutral",
                    "period": "이번 달"
                },
                {
                    "title": "매출 증감률",
                    "value": "0%",
                    "change": "₩0",
                    "trend": "neutral",
                    "period": "전월 대비"
                },
                {
                    "title": "분기 총 실적",
                    "value": "₩0",
                    "change": "0개 거래처",
                    "trend": "neutral",
                    "period": "최근 3개월"
                }
            ]
        }