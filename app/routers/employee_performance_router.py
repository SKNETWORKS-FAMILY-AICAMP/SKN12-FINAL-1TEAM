"""
직원 실적 데이터 API Router
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import jwt
import os

# 서비스 관련
from app.services.core.employee_performance_service import employee_performance_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Employee Performance Data"])

# Request/Response Models for Agent
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
    employee_id: Optional[int] = None   # 직원 ID

class PerformanceResponse(BaseModel):
    summary: Dict[str, Any]
    monthly_data: List[Dict[str, Any]]
    product_data: List[Dict[str, Any]]
    client_data: List[Dict[str, Any]]

class TargetResponse(BaseModel):
    target_data: List[Dict[str, Any]]
    summary: Dict[str, Any]

# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# 보안 설정
security = HTTPBearer()

# 사용자 정보 추출
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT 토큰에서 사용자 정보 추출"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id = payload.get("sub")  # 이메일
        user_role = payload.get("role", "user")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # 데이터베이스에서 실제 employee_id 조회
        from app.services.utils.db import get_db
        from app.models.employees import Employee
        from sqlalchemy.orm import Session
        
        db: Session = next(get_db())
        try:
            employee = db.query(Employee).filter(
                Employee.email == user_id,
                Employee.is_deleted == False
            ).first()
            
            if employee:
                # employee_info_id를 사용해야 함 (sales_records가 참조)
                from app.models.employee_info import EmployeeInfo
                emp_info = db.query(EmployeeInfo).filter(
                    EmployeeInfo.name == employee.name
                ).first()
                
                employee_id = emp_info.employee_info_id if emp_info else employee.employee_id
                employee_name = employee.name
            else:
                employee_id = None
                employee_name = user_id
        finally:
            db.close()
        
        # 사용자 정보 반환
        user_info = {
            "user_id": user_id,
            "role": user_role,
            "employee_id": employee_id,
            "name": employee_name
        }
        
        return user_info
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Response Models
class EmployeeInfo(BaseModel):
    """직원 정보"""
    employee_id: int
    name: str
    사번: Optional[str]
    department: Optional[str]
    email: Optional[str]
    role: Optional[str]

class PerformanceData(BaseModel):
    """실적 데이터"""
    employee_id: int
    employee_name: str
    year_month: str
    target_amount: Optional[float]
    actual_sales: Optional[float]
    achievement_rate: Optional[float]
    sales_count: Optional[int]
    customer_count: Optional[int]

class ProductPerformance(BaseModel):
    """제품별 실적"""
    product_id: int
    product_name: str
    total_amount: float
    sales_count: int
    percentage: Optional[float]

class CustomerPerformance(BaseModel):
    """고객별 실적"""
    customer_id: int
    customer_name: str
    customer_grade: Optional[str]
    total_amount: float
    sales_count: int
    percentage: Optional[float]

# API Endpoints

@router.get("/employees", response_model=List[EmployeeInfo])
def get_employees(
    department: Optional[str] = Query(None, description="부서명으로 필터링"),
    is_active: bool = Query(True, description="활성 직원만 조회"),
    current_user: dict = Depends(get_current_user)
):
    """
    직원 목록을 조회합니다.
    - 관리자: 전체 직원 조회 가능
    - 일반 직원: 본인 정보만 조회
    """
    try:
        # 서비스를 통한 직원 목록 조회
        employees_data = employee_performance_service.get_employees(
            department=department,
            is_active=is_active
        )
        
        employees = []
        for emp_data in employees_data:
            emp = EmployeeInfo(
                employee_id=emp_data["employee_id"],
                name=emp_data["name"],
                사번=emp_data.get("사번"),
                department=emp_data.get("department"),
                email=emp_data.get("email"),
                role=emp_data.get("role")
            )
            employees.append(emp)
        
        # 권한에 따른 필터링
        if current_user["role"] != "admin":
            # 일반 직원은 본인만
            employees = [emp for emp in employees if emp.name == current_user["name"]]
        
        return employees
        
    except Exception as e:
        logger.error(f"직원 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{employee_id}", response_model=List[PerformanceData])
def get_employee_performance(
    employee_id: int,
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    current_user: dict = Depends(get_current_user)
):
    """
    특정 직원의 월별 실적 데이터를 조회합니다.
    """
    try:
        # 권한 확인
        if current_user["role"] != "admin":
            if current_user.get("employee_id") != employee_id:
                raise HTTPException(status_code=403, detail="본인 데이터만 조회 가능합니다.")
        
        # 서비스를 통한 실적 데이터 조회
        performance_data = employee_performance_service.get_performance_data(
            employee_id=employee_id,
            start_period=start_period,
            end_period=end_period
        )
        
        performance_list = []
        for data in performance_data:
            performance = PerformanceData(
                employee_id=data["employee_id"],
                employee_name=data["employee_name"],
                year_month=data["year_month"],
                target_amount=data["target_amount"],
                actual_sales=data["actual_sales"],
                achievement_rate=data["achievement_rate"],
                sales_count=data["sales_count"],
                customer_count=data["customer_count"]
            )
            performance_list.append(performance)
        
        return performance_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"실적 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{employee_id}/summary")
def get_performance_summary(
    employee_id: int,
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    current_user: dict = Depends(get_current_user)
):
    """
    특정 직원의 실적 요약 정보를 반환합니다.
    """
    try:
        # 권한 확인
        if current_user["role"] != "admin":
            if current_user.get("employee_id") != employee_id:
                raise HTTPException(status_code=403, detail="본인 데이터만 조회 가능합니다.")
        
        # 서비스를 통한 요약 데이터 조회
        summary = employee_performance_service.get_performance_summary(
            employee_id=employee_id,
            start_period=start_period,
            end_period=end_period
        )
        
        return {
            "employee_id": employee_id,
            "period": f"{start_period}~{end_period}",
            "month_count": summary["month_count"],
            "total_target": summary["total_target"],
            "total_sales": summary["total_sales"],
            "avg_achievement_rate": summary["avg_achievement_rate"],
            "total_sales_count": summary["total_sales_count"],
            "unique_customers": summary["unique_customers"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{employee_id}/products", response_model=List[ProductPerformance])
def get_product_performance(
    employee_id: int,
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    limit: int = Query(10, description="상위 N개 제품"),
    current_user: dict = Depends(get_current_user)
):
    """
    특정 직원의 제품별 실적을 조회합니다.
    """
    try:
        # 권한 확인
        if current_user["role"] != "admin":
            if current_user.get("employee_id") != employee_id:
                raise HTTPException(status_code=403, detail="본인 데이터만 조회 가능합니다.")
        
        # 서비스를 통한 제품별 실적 조회
        products_data = employee_performance_service.get_product_performance(
            employee_id=employee_id,
            start_period=start_period,
            end_period=end_period,
            limit=limit
        )
        
        products = []
        for data in products_data:
            product = ProductPerformance(
                product_id=data["product_id"],
                product_name=data["product_name"],
                total_amount=data["total_amount"],
                sales_count=data["sales_count"],
                percentage=data.get("percentage", 0)
            )
            products.append(product)
        
        return products
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"제품별 실적 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{employee_id}/customers", response_model=List[CustomerPerformance])
def get_customer_performance(
    employee_id: int,
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    limit: int = Query(10, description="상위 N개 고객"),
    current_user: dict = Depends(get_current_user)
):
    """
    특정 직원의 고객별 실적을 조회합니다.
    """
    try:
        # 권한 확인
        if current_user["role"] != "admin":
            if current_user.get("employee_id") != employee_id:
                raise HTTPException(status_code=403, detail="본인 데이터만 조회 가능합니다.")
        
        # 서비스를 통한 고객별 실적 조회
        customers_data = employee_performance_service.get_customer_performance(
            employee_id=employee_id,
            start_period=start_period,
            end_period=end_period,
            limit=limit
        )
        
        customers = []
        for data in customers_data:
            customer = CustomerPerformance(
                customer_id=data["customer_id"],
                customer_name=data["customer_name"],
                customer_grade=data.get("customer_grade"),
                total_amount=data["total_amount"],
                sales_count=data["sales_count"],
                percentage=data.get("percentage", 0)
            )
            customers.append(customer)
        
        return customers
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"고객별 실적 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/departments")
def get_departments(current_user: dict = Depends(get_current_user)):
    """
    부서 목록을 조회합니다.
    """
    try:
        departments = employee_performance_service.get_departments()
        return departments
        
    except Exception as e:
        logger.error(f"부서 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 에이전트용 데이터 엔드포인트

@router.get("/agent/performance-data")
def get_agent_performance_data(
    employee_name: str = Query(..., description="직원 이름"),
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    current_user: dict = Depends(get_current_user)
):
    """
    에이전트가 필요로 하는 실적 데이터 구조를 반환합니다.
    """
    try:
        # 직원 정보 조회
        employee_info = employee_performance_service.get_employee_info_by_name(employee_name)
        
        if not employee_info:
            raise HTTPException(status_code=404, detail=f"직원 '{employee_name}'을 찾을 수 없습니다.")
        
        employee_id = employee_info["employee_id"]
        
        # 권한 확인
        if current_user["role"] != "admin":
            if current_user.get("employee_id") != employee_id:
                raise HTTPException(status_code=403, detail="본인 데이터만 조회 가능합니다.")
        
        # 실적 데이터 조회
        performance_data = employee_performance_service.get_performance_data(
            employee_id=employee_id,
            start_period=start_period,
            end_period=end_period
        )
        
        # 에이전트용 데이터 구조로 변환
        return {
            "employee_info": {
                "employee_id": employee_id,
                "name": employee_info["name"],
                "사번": employee_info.get("사번"),
                "department": employee_info.get("department")
            },
            "performance_data": performance_data,
            "period": {
                "start": start_period,
                "end": end_period
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"에이전트 데이터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))