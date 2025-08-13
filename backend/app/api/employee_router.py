from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path
import jwt
import os

# 경로 설정
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.employee_agent.employee_agent import EnhancedEmployeeAgent
from app.services.employee_agent.db_manager import EmployeeDBManager
from app.services.common.database_api_client import DatabaseAPIClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/employee", tags=["Employee Performance"])

# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# 보안 설정
security = HTTPBearer()

# 전역 인스턴스
employee_agent = None
db_manager = None
db_client = None

def get_employee_agent():
    global employee_agent
    if employee_agent is None:
        employee_agent = EnhancedEmployeeAgent()
    return employee_agent

def get_db_manager():
    global db_manager
    if db_manager is None:
        db_manager = EmployeeDBManager()
    return db_manager

def get_db_client():
    global db_client
    if db_client is None:
        db_client = DatabaseAPIClient()
    return db_client

# 사용자 정보 추출 함수
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user_role = payload.get("role", "user")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # 이메일에서 이름 추출 또는 DB에서 조회
        user_name = user_id.split("@")[0] if "@" in user_id else user_id
        
        # 관리자가 아닌 경우 실제 직원 이름 매핑
        if user_role != "admin":
            # 이메일과 직원명 매핑 (실제로는 DB에서 조회해야 함)
            name_mapping = {
                "suah@example.com": "최수아",
                "younghee@example.com": "김영희",
                "cheolsu@example.com": "박철수",
                "sihyun@example.com": "조시현",
                "minsu@example.com": "이민수"
            }
            user_name = name_mapping.get(user_id, user_name)
        
        return {
            "user_id": user_id,
            "role": user_role,
            "name": user_name
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

# Request/Response Models
class AnalyzeRequest(BaseModel):
    query: Optional[str] = None       # 자연어 쿼리
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None    # YYYY-MM-DD format
    start_period: Optional[str] = None  # YYYYMM format
    end_period: Optional[str] = None    # YYYYMM format
    employee_name: Optional[str] = None  # 관리자용

class PerformanceRequest(BaseModel):
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None    # YYYY-MM-DD format
    start_period: Optional[str] = None  # YYYYMM format
    end_period: Optional[str] = None    # YYYYMM format
    employee_name: Optional[str] = None  # 관리자용

class PerformanceResponse(BaseModel):
    summary: Dict[str, Any]
    monthly_data: List[Dict[str, Any]]
    product_data: List[Dict[str, Any]]
    client_data: List[Dict[str, Any]]

class TargetResponse(BaseModel):
    target_data: List[Dict[str, Any]]
    summary: Dict[str, Any]

# API Endpoints

@router.get("/list")
async def get_employee_list(current_user: dict = Depends(get_current_user)):
    """
    직원 목록을 조회합니다.
    관리자: 모든 직원 목록 (실적 요약 포함)
    일반 직원: 본인 정보만
    """
    try:
        db_manager = get_db_manager()
        
        # PostgreSQL에서 직원 목록 조회
        try:
            db_client = get_db_client()
            # employees 테이블에서 활성 직원 조회
            query = """
                SELECT employee_id, name, 사번, department 
                FROM employees 
                WHERE is_active = true AND is_deleted = false
                ORDER BY name
            """
            result = await db_client.execute_query(query)
            
            if result and len(result) > 0:
                employees = []
                for row in result:
                    employees.append({
                        "employee_id": row.get("employee_id"),
                        "name": row.get("name"),
                        "사번": row.get("사번"),
                        "department": row.get("department", "영업팀")
                    })
                return {"employees": employees}
        except Exception as e:
            logger.warning(f"PostgreSQL 조회 실패, 대체 방법 사용: {e}")
        
        # 대체: sales_performance 테이블에서 직원명 추출
        employees = db_manager.get_available_employees()
        
        # 직원명만 있는 경우 형식 맞추기
        employee_list = []
        for idx, name in enumerate(employees, 1):
            employee_list.append({
                "employee_id": idx,
                "name": name,
                "사번": 1025 + idx,  # 임시 사번
                "department": "영업팀"
            })
        
        # 권한에 따른 필터링
        if current_user["role"] != "admin":
            # 일반 직원은 본인 정보만
            employee_list = [emp for emp in employee_list if emp["name"] == current_user["name"]]
        
        return {"employees": employee_list}
        
    except Exception as e:
        logger.error(f"직원 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/performance", response_model=PerformanceResponse)
async def get_employee_performance(
    request: PerformanceRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    직원의 실적 데이터를 조회합니다.
    관리자: 모든 직원 데이터 조회 가능
    일반 직원: 본인 데이터만 조회 가능
    """
    try:
        db_manager = get_db_manager()
        
        # 직원명 결정
        if current_user["role"] == "admin" and request.employee_name:
            # 관리자는 지정한 직원 조회
            employee_name = request.employee_name
        else:
            # 일반 직원은 본인만 조회
            employee_name = current_user["name"]
        
        # 날짜 형식 처리 (YYYY-MM-DD 또는 YYYYMM)
        if request.start_period and request.end_period:
            # 이미 YYYYMM 형식으로 전달된 경우
            start_period = request.start_period
            end_period = request.end_period
        elif request.start_date and request.end_date:
            # YYYY-MM-DD 형식을 YYYYMM으로 변환
            start_period = request.start_date.replace("-", "")[:6]
            end_period = request.end_date.replace("-", "")[:6]
        else:
            # 기본값: 최근 3개월
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            start_period = start_date.strftime("%Y%m")
            end_period = end_date.strftime("%Y%m")
        
        # 실적 데이터 조회
        performance_summary = db_manager.get_performance_summary(
            employee_name,
            start_period,
            end_period
        )
        
        if not performance_summary:
            raise HTTPException(status_code=404, detail="실적 데이터를 찾을 수 없습니다.")
        
        # 응답 형식으로 변환
        total_performance = performance_summary.get("total_performance", 0)
        monthly_breakdown = performance_summary.get("monthly_breakdown", [])
        product_breakdown = performance_summary.get("product_breakdown", [])
        client_breakdown = performance_summary.get("client_breakdown", [])
        
        # 요약 정보 계산
        summary = {
            "total_amount": total_performance,
            "total_count": len(monthly_breakdown),
            "average_amount": int(total_performance / len(monthly_breakdown)) if monthly_breakdown else 0
        }
        
        # 월별 데이터 형식 변환
        monthly_data = []
        for item in monthly_breakdown:
            monthly_data.append({
                "month": item.get("month"),
                "amount": item.get("amount"),
                "count": item.get("count", 0)
            })
        
        # 제품별 데이터 형식 변환 (비율 추가)
        product_data = []
        for item in product_breakdown:
            percentage = (item["amount"] / total_performance * 100) if total_performance > 0 else 0
            product_data.append({
                "product": item.get("name"),
                "amount": item.get("amount"),
                "percentage": round(percentage, 1)
            })
        
        # 거래처별 데이터 형식 변환 (비율 추가)
        client_data = []
        for item in client_breakdown:
            percentage = (item["amount"] / total_performance * 100) if total_performance > 0 else 0
            client_data.append({
                "client": item.get("name"),
                "amount": item.get("amount"),
                "percentage": round(percentage, 1)
            })
        
        return PerformanceResponse(
            summary=summary,
            monthly_data=monthly_data,
            product_data=product_data,
            client_data=client_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"실적 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/target", response_model=TargetResponse)
async def get_employee_target(
    request: PerformanceRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    직원의 목표 대비 실적을 조회합니다.
    관리자: 모든 직원 데이터 조회 가능안그
    일반 직원: 본인 데이터만 조회 가능
    """
    try:
        db_manager = get_db_manager()
        
        # 직원명 결정
        if current_user["role"] == "admin" and request.employee_name:
            employee_name = request.employee_name
        else:
            employee_name = current_user["name"]
        
        # 날짜 형식 처리
        if request.start_period and request.end_period:
            start_period = request.start_period
            end_period = request.end_period
        elif request.start_date and request.end_date:
            start_period = request.start_date.replace("-", "")[:6]
            end_period = request.end_date.replace("-", "")[:6]
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            start_period = start_date.strftime("%Y%m")
            end_period = end_date.strftime("%Y%m")
        
        # 목표 대비 실적 데이터 조회
        target_comparison = db_manager.get_target_vs_performance(
            employee_name,
            start_period,
            end_period
        )
        
        if not target_comparison:
            raise HTTPException(status_code=404, detail="목표 데이터를 찾을 수 없습니다.")
        
        # 실적 데이터도 함께 조회하여 월별 비교
        performance_summary = db_manager.get_performance_summary(
            employee_name,
            start_period,
            end_period
        )
        
        # 월별 목표 vs 실적 데이터 생성
        target_data = []
        monthly_breakdown = performance_summary.get("monthly_breakdown", [])
        
        # 목표 데이터 조회 (월별)
        target_df = db_manager.get_employee_target_data(
            employee_name,
            start_period,
            end_period
        )
        
        # 월별 데이터 매칭
        for month_data in monthly_breakdown:
            month = month_data["month"]
            actual = month_data["amount"]
            
            # 해당 월의 목표 찾기
            target = 0
            if not target_df.empty:
                month_int = int(month)
                month_target = target_df[target_df['년월'] == month_int]
                if not month_target.empty:
                    target = int(month_target.iloc[0]['목표'])
            
            # 목표가 없으면 실적의 90%를 가상 목표로 설정
            if target == 0:
                target = int(actual * 0.9)
            
            achievement_rate = (actual / target * 100) if target > 0 else 0
            
            target_data.append({
                "month": month,
                "target": target,
                "actual": actual,
                "achievement_rate": round(achievement_rate, 1)
            })
        
        # 전체 요약
        total_target = target_comparison.get("total_target", 0)
        total_actual = target_comparison.get("total_performance", 0)
        overall_achievement = target_comparison.get("achievement_rate", 0)
        
        # 목표 달성한 월 수 계산
        achieved_months = sum(1 for item in target_data if item["achievement_rate"] >= 100)
        
        summary = {
            "total_target": total_target,
            "total_actual": total_actual,
            "overall_achievement": round(overall_achievement, 1),
            "achieved_months": achieved_months,
            "total_months": len(target_data),
            "evaluation": target_comparison.get("evaluation", ""),
            "grade": target_comparison.get("grade", "")
        }
        
        return TargetResponse(
            target_data=target_data,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"목표 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_employee_performance(
    request: AnalyzeRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    선택한 기간의 직원 실적을 분석합니다.
    관리자: 모든 직원 데이터 분석 가능
    일반 직원: 본인 데이터만 분석 가능
    """
    try:
        agent = get_employee_agent()
        
        # 직원명 결정
        if current_user["role"] == "admin" and request.employee_name:
            employee_name = request.employee_name
        else:
            employee_name = current_user["name"]
        
        # 쿼리 처리
        if request.query:
            # 자연어 쿼리가 전달된 경우
            if employee_name and employee_name not in request.query:
                # 관리자가 특정 직원을 선택한 경우 직원명 추가
                query = request.query.replace("실적을 분석해주세요", f"{employee_name}의 실적을 분석해주세요")
            else:
                query = request.query
                
            # 쿼리에 직원명이 없으면 현재 사용자 이름 추가
            if employee_name and employee_name not in query:
                query = f"{employee_name}의 {query}"
        elif request.start_period and request.end_period:
            # YYYYMM 형식으로 지정된 경우
            start_year = request.start_period[:4]
            start_month = request.start_period[4:6]
            end_year = request.end_period[:4]
            end_month = request.end_period[4:6]
            query = f"{employee_name}의 {start_year}년 {start_month}월부터 {end_year}년 {end_month}월까지 실적을 분석해주세요"
        elif request.start_date and request.end_date:
            # YYYY-MM-DD 형식으로 지정된 경우
            start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
            query = f"{employee_name}의 {start_date.strftime('%Y년 %m월')}부터 {end_date.strftime('%Y년 %m월')}까지 실적을 분석해주세요"
        else:
            # 기본값: 최근 3개월
            query = f"{employee_name}의 최근 3개월 실적을 분석해주세요"
        
        # 에이전트 실행
        result = await agent.graph.ainvoke({
            "query": query,
            "query_analysis": None,
            "employee_name": None,
            "start_period": None,
            "end_period": None,
            "analysis_type": None,
            "performance_data": None,
            "target_data": None,
            "analysis_results": None,
            "report": None,
            "error": None
        })
        
        # 오류 확인
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        # 결과 반환
        return {
            "employee_name": result.get("employee_name"),
            "period": f"{result.get('start_period')}~{result.get('end_period')}",
            "performance_data": result.get("performance_data"),
            "target_data": result.get("target_data"),
            "analysis_results": result.get("analysis_results"),
            "report": result.get("report"),
            "summary": {
                "achievement_rate": result.get("target_data", {}).get("achievement_rate", 0),
                "grade": result.get("target_data", {}).get("grade", ""),
                "evaluation": result.get("target_data", {}).get("evaluation", "")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"실적 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 헬스체크
@router.get("/health")
async def health_check():
    """API 헬스체크"""
    return {"status": "healthy", "service": "employee_performance"}