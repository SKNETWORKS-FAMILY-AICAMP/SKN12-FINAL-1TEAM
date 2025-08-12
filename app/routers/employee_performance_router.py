"""
직원 실적 데이터 API Router
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import jwt
import os
from sqlalchemy import text

# 데이터베이스 관련
from app.services.common.database_api_client import DatabaseAPIClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/employee", tags=["Employee Performance Data"])

# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

# 보안 설정
security = HTTPBearer()

# 전역 DB 클라이언트
db_client = None

def get_db_client():
    """싱글톤 DB 클라이언트"""
    global db_client
    if db_client is None:
        db_client = DatabaseAPIClient()
    return db_client

# 사용자 정보 추출
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT 토큰에서 사용자 정보 추출"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")  # 이메일
        user_role = payload.get("role", "user")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # DB에서 직원 정보 조회
        db_client = get_db_client()
        query = """
            SELECT e.employee_id, e.name, e.role, e.email, ei.사번, ei.department
            FROM employees e
            LEFT JOIN employee_info ei ON e.employee_id = ei.employee_id
            WHERE e.email = %s AND e.is_active = true AND e.is_deleted = false
            LIMIT 1
        """
        result = await db_client.execute_query(query, params=(user_id,))
        
        if result and len(result) > 0:
            user_data = result[0]
            return {
                "user_id": user_id,
                "employee_id": user_data.get("employee_id"),
                "role": user_data.get("role", user_role),
                "name": user_data.get("name"),
                "사번": user_data.get("사번"),
                "department": user_data.get("department")
            }
        else:
            # 기본값 반환
            return {
                "user_id": user_id,
                "role": user_role,
                "name": user_id.split("@")[0] if "@" in user_id else user_id
            }
            
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
    """거래처별 실적"""
    customer_id: int
    customer_name: str
    total_amount: float
    sales_count: int
    percentage: Optional[float]

# API Endpoints

@router.get("/employees", response_model=List[EmployeeInfo])
async def get_employees(
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
        db_client = get_db_client()
        
        # 기본 쿼리
        query = """
            SELECT 
                e.employee_id,
                e.name,
                e.email,
                e.role,
                ei.사번,
                ei.department
            FROM employees e
            LEFT JOIN employee_info ei ON e.employee_id = ei.employee_id
            WHERE e.is_deleted = false
        """
        
        params = []
        
        # 활성 상태 필터
        if is_active:
            query += " AND e.is_active = true"
        
        # 부서 필터
        if department:
            query += " AND ei.department = %s"
            params.append(department)
        
        query += " ORDER BY e.name"
        
        result = await db_client.execute_query(query, params=tuple(params) if params else None)
        
        if not result:
            return []
        
        employees = []
        for row in result:
            emp = EmployeeInfo(
                employee_id=row["employee_id"],
                name=row["name"],
                사번=row.get("사번"),
                department=row.get("department"),
                email=row.get("email"),
                role=row.get("role")
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

@router.get("/performance/{employee_id}", response_model=List[PerformanceData])
async def get_employee_performance(
    employee_id: int,
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    current_user: dict = Depends(get_current_user)
):
    """
    특정 직원의 월별 실적 데이터를 조회합니다.
    Materialized View (employee_performance_mv)를 활용합니다.
    """
    try:
        # 권한 확인
        if current_user["role"] != "admin":
            # 일반 직원은 본인 데이터만 조회 가능
            if current_user.get("employee_id") != employee_id:
                raise HTTPException(status_code=403, detail="본인 데이터만 조회 가능합니다.")
        
        db_client = get_db_client()
        
        # 기간 형식 변환 (YYYYMM -> YYYY-MM-01)
        start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
        end_date = f"{end_period[:4]}-{end_period[4:6]}-01"
        
        # Materialized View에서 데이터 조회
        query = """
            SELECT 
                employee_id,
                employee_name,
                TO_CHAR(year_month, 'YYYYMM') as year_month,
                target_amount,
                actual_sales,
                achievement_rate,
                sales_count,
                customer_count
            FROM employee_performance_mv
            WHERE employee_id = %s
                AND year_month >= %s::date
                AND year_month <= %s::date
            ORDER BY year_month
        """
        
        result = await db_client.execute_query(
            query, 
            params=(employee_id, start_date, end_date)
        )
        
        if not result:
            return []
        
        performance_list = []
        for row in result:
            performance = PerformanceData(
                employee_id=row["employee_id"],
                employee_name=row["employee_name"],
                year_month=row["year_month"],
                target_amount=row.get("target_amount"),
                actual_sales=row.get("actual_sales"),
                achievement_rate=row.get("achievement_rate"),
                sales_count=row.get("sales_count"),
                customer_count=row.get("customer_count")
            )
            performance_list.append(performance)
        
        return performance_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"실적 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/{employee_id}/summary")
async def get_performance_summary(
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
        
        db_client = get_db_client()
        
        # 기간 형식 변환
        start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
        end_date = f"{end_period[:4]}-{end_period[4:6]}-01"
        
        # 요약 통계 조회
        query = """
            SELECT 
                COUNT(*) as month_count,
                SUM(target_amount) as total_target,
                SUM(actual_sales) as total_sales,
                AVG(achievement_rate) as avg_achievement_rate,
                SUM(sales_count) as total_sales_count,
                COUNT(DISTINCT customer_count) as unique_customers
            FROM employee_performance_mv
            WHERE employee_id = %s
                AND year_month >= %s::date
                AND year_month <= %s::date
        """
        
        result = await db_client.execute_query(
            query,
            params=(employee_id, start_date, end_date)
        )
        
        if not result or len(result) == 0:
            return {
                "month_count": 0,
                "total_target": 0,
                "total_sales": 0,
                "avg_achievement_rate": 0,
                "total_sales_count": 0,
                "unique_customers": 0
            }
        
        summary = result[0]
        
        return {
            "employee_id": employee_id,
            "period": f"{start_period}~{end_period}",
            "month_count": summary.get("month_count", 0),
            "total_target": summary.get("total_target", 0),
            "total_sales": summary.get("total_sales", 0),
            "avg_achievement_rate": summary.get("avg_achievement_rate", 0),
            "total_sales_count": summary.get("total_sales_count", 0),
            "unique_customers": summary.get("unique_customers", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/{employee_id}/products", response_model=List[ProductPerformance])
async def get_product_performance(
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
        
        db_client = get_db_client()
        
        # 기간 형식 변환
        start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
        end_date = f"{end_period[:4]}-{end_period[4:6]}-31"
        
        # 제품별 실적 조회
        query = """
            SELECT 
                p.product_id,
                p.product_name,
                SUM(sr.sale_amount) as total_amount,
                COUNT(sr.sale_id) as sales_count
            FROM sales_records sr
            INNER JOIN products p ON sr.product_id = p.product_id
            WHERE sr.employee_id = %s
                AND sr.sale_date >= %s::date
                AND sr.sale_date <= %s::date
            GROUP BY p.product_id, p.product_name
            ORDER BY total_amount DESC
            LIMIT %s
        """
        
        result = await db_client.execute_query(
            query,
            params=(employee_id, start_date, end_date, limit)
        )
        
        if not result:
            return []
        
        # 전체 매출 계산 (비율 계산용)
        total_sales = sum(row["total_amount"] for row in result)
        
        products = []
        for row in result:
            product = ProductPerformance(
                product_id=row["product_id"],
                product_name=row["product_name"],
                total_amount=row["total_amount"],
                sales_count=row["sales_count"],
                percentage=round((row["total_amount"] / total_sales * 100), 2) if total_sales > 0 else 0
            )
            products.append(product)
        
        return products
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"제품별 실적 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/{employee_id}/customers", response_model=List[CustomerPerformance])
async def get_customer_performance(
    employee_id: int,
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    limit: int = Query(10, description="상위 N개 거래처"),
    current_user: dict = Depends(get_current_user)
):
    """
    특정 직원의 거래처별 실적을 조회합니다.
    """
    try:
        # 권한 확인
        if current_user["role"] != "admin":
            if current_user.get("employee_id") != employee_id:
                raise HTTPException(status_code=403, detail="본인 데이터만 조회 가능합니다.")
        
        db_client = get_db_client()
        
        # 기간 형식 변환
        start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
        end_date = f"{end_period[:4]}-{end_period[4:6]}-31"
        
        # 거래처별 실적 조회
        query = """
            SELECT 
                c.customer_id,
                c.customer_name,
                SUM(sr.sale_amount) as total_amount,
                COUNT(sr.sale_id) as sales_count
            FROM sales_records sr
            INNER JOIN customers c ON sr.customer_id = c.customer_id
            WHERE sr.employee_id = %s
                AND sr.sale_date >= %s::date
                AND sr.sale_date <= %s::date
            GROUP BY c.customer_id, c.customer_name
            ORDER BY total_amount DESC
            LIMIT %s
        """
        
        result = await db_client.execute_query(
            query,
            params=(employee_id, start_date, end_date, limit)
        )
        
        if not result:
            return []
        
        # 전체 매출 계산
        total_sales = sum(row["total_amount"] for row in result)
        
        customers = []
        for row in result:
            customer = CustomerPerformance(
                customer_id=row["customer_id"],
                customer_name=row["customer_name"],
                total_amount=row["total_amount"],
                sales_count=row["sales_count"],
                percentage=round((row["total_amount"] / total_sales * 100), 2) if total_sales > 0 else 0
            )
            customers.append(customer)
        
        return customers
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"거래처별 실적 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/targets/{employee_id}")
async def get_employee_targets(
    employee_id: int,
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    current_user: dict = Depends(get_current_user)
):
    """
    특정 직원의 목표 데이터를 조회합니다.
    """
    try:
        # 권한 확인
        if current_user["role"] != "admin":
            if current_user.get("employee_id") != employee_id:
                raise HTTPException(status_code=403, detail="본인 데이터만 조회 가능합니다.")
        
        db_client = get_db_client()
        
        # 목표 데이터 조회
        query = """
            SELECT 
                ep.employee_info_id,
                ep.년월,
                ep.목표,
                ep.누적목표,
                ei.name as employee_name
            FROM employee_performance ep
            INNER JOIN employee_info ei ON ep.employee_info_id = ei.employee_info_id
            WHERE ei.employee_id = %s
                AND ep.년월 >= %s
                AND ep.년월 <= %s
            ORDER BY ep.년월
        """
        
        result = await db_client.execute_query(
            query,
            params=(employee_id, int(start_period), int(end_period))
        )
        
        if not result:
            return []
        
        targets = []
        for row in result:
            targets.append({
                "year_month": str(row["년월"]),
                "target": row.get("목표", 0),
                "cumulative_target": row.get("누적목표", 0),
                "employee_name": row.get("employee_name")
            })
        
        return targets
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"목표 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/departments")
async def get_departments(current_user: dict = Depends(get_current_user)):
    """
    부서 목록을 조회합니다.
    """
    try:
        db_client = get_db_client()
        
        query = """
            SELECT DISTINCT department
            FROM employee_info
            WHERE department IS NOT NULL
            ORDER BY department
        """
        
        result = await db_client.execute_query(query)
        
        if not result:
            return []
        
        return [row["department"] for row in result]
        
    except Exception as e:
        logger.error(f"부서 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 에이전트용 데이터 엔드포인트 추가

@router.get("/agent/performance-data")
async def get_agent_performance_data(
    employee_name: str = Query(..., description="직원 이름"),
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    current_user: dict = Depends(get_current_user)
):
    """
    에이전트가 필요로 하는 실적 데이터 구조를 반환합니다.
    /api/employee/analyze의 performance_data 부분
    """
    try:
        db_client = get_db_client()
        
        # 직원 ID 조회
        emp_query = """
            SELECT ei.employee_info_id, ei.employee_id, ei.사번
            FROM employee_info ei
            WHERE ei.name = %s
            LIMIT 1
        """
        emp_result = await db_client.execute_query(emp_query, params=(employee_name,))
        
        if not emp_result:
            raise HTTPException(status_code=404, detail=f"직원 '{employee_name}'을 찾을 수 없습니다.")
        
        employee_info_id = emp_result[0]["employee_info_id"]
        
        # 월별 실적 조회
        monthly_query = """
            SELECT 
                년월,
                SUM(금액) as amount
            FROM sales_records
            WHERE 담당자 = %s
                AND 년월 >= %s
                AND 년월 <= %s
            GROUP BY 년월
            ORDER BY 년월
        """
        monthly_result = await db_client.execute_query(
            monthly_query,
            params=(employee_name, int(start_period), int(end_period))
        )
        
        # 제품별 실적 조회
        product_query = """
            SELECT 
                품목 as name,
                SUM(금액) as amount
            FROM sales_records
            WHERE 담당자 = %s
                AND 년월 >= %s
                AND 년월 <= %s
            GROUP BY 품목
            ORDER BY amount DESC
        """
        product_result = await db_client.execute_query(
            product_query,
            params=(employee_name, int(start_period), int(end_period))
        )
        
        # 거래처별 실적 조회
        client_query = """
            SELECT 
                거래처 as name,
                SUM(금액) as amount
            FROM sales_records
            WHERE 담당자 = %s
                AND 년월 >= %s
                AND 년월 <= %s
            GROUP BY 거래처
            ORDER BY amount DESC
        """
        client_result = await db_client.execute_query(
            client_query,
            params=(employee_name, int(start_period), int(end_period))
        )
        
        # 총 실적 계산
        total_performance = sum(row["amount"] for row in monthly_result) if monthly_result else 0
        
        # 데이터 구조 생성
        performance_data = {
            "total_performance": total_performance,
            "monthly_breakdown": [
                {"month": str(row["년월"]), "amount": row["amount"]}
                for row in monthly_result
            ] if monthly_result else [],
            "product_breakdown": [
                {"name": row["name"], "amount": row["amount"]}
                for row in product_result
            ] if product_result else [],
            "client_breakdown": [
                {"name": row["name"], "amount": row["amount"]}
                for row in client_result
            ] if client_result else []
        }
        
        return performance_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"에이전트 실적 데이터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/target-data")
async def get_agent_target_data(
    employee_name: str = Query(..., description="직원 이름"),
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    current_user: dict = Depends(get_current_user)
):
    """
    에이전트가 필요로 하는 목표 데이터 구조를 반환합니다.
    /api/employee/analyze의 target_data 부분
    """
    try:
        db_client = get_db_client()
        
        # 실적 조회
        performance_query = """
            SELECT 
                SUM(금액) as total_performance
            FROM sales_records
            WHERE 담당자 = %s
                AND 년월 >= %s
                AND 년월 <= %s
        """
        perf_result = await db_client.execute_query(
            performance_query,
            params=(employee_name, int(start_period), int(end_period))
        )
        
        total_performance = perf_result[0]["total_performance"] if perf_result and perf_result[0]["total_performance"] else 0
        
        # 목표 조회
        target_query = """
            SELECT 
                SUM(목표) as total_target
            FROM employee_performance
            WHERE 담당자 = %s
                AND 년월 >= %s
                AND 년월 <= %s
        """
        target_result = await db_client.execute_query(
            target_query,
            params=(employee_name, int(start_period), int(end_period))
        )
        
        total_target = target_result[0]["total_target"] if target_result and target_result[0]["total_target"] else 0
        
        # 달성률 계산
        achievement_rate = (total_performance / total_target * 100) if total_target > 0 else 0
        gap_amount = total_performance - total_target
        
        # 평가 등급 결정
        if achievement_rate >= 110:
            evaluation = "탁월"
            grade = "S"
        elif achievement_rate >= 100:
            evaluation = "우수"
            grade = "A"
        elif achievement_rate >= 90:
            evaluation = "양호"
            grade = "B"
        elif achievement_rate >= 80:
            evaluation = "보통"
            grade = "C"
        else:
            evaluation = "미흡"
            grade = "D"
        
        return {
            "total_performance": total_performance,
            "total_target": total_target,
            "achievement_rate": round(achievement_rate, 1),
            "gap_amount": gap_amount,
            "evaluation": evaluation,
            "grade": grade
        }
        
    except Exception as e:
        logger.error(f"에이전트 목표 데이터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/monthly-breakdown")
async def get_agent_monthly_breakdown(
    employee_name: str = Query(..., description="직원 이름"),
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    current_user: dict = Depends(get_current_user)
):
    """
    에이전트용 월별 실적 및 목표 상세 데이터
    """
    try:
        db_client = get_db_client()
        
        # 월별 실적 및 목표 조회
        query = """
            SELECT 
                COALESCE(sr.년월, ep.년월) as month,
                COALESCE(SUM(sr.금액), 0) as actual,
                COALESCE(MAX(ep.목표), 0) as target
            FROM (
                SELECT DISTINCT 년월 FROM sales_records 
                WHERE 담당자 = %s AND 년월 >= %s AND 년월 <= %s
                UNION
                SELECT DISTINCT 년월 FROM employee_performance 
                WHERE 담당자 = %s AND 년월 >= %s AND 년월 <= %s
            ) months
            LEFT JOIN sales_records sr ON sr.년월 = months.년월 AND sr.담당자 = %s
            LEFT JOIN employee_performance ep ON ep.년월 = months.년월 AND ep.담당자 = %s
            GROUP BY COALESCE(sr.년월, ep.년월)
            ORDER BY month
        """
        
        result = await db_client.execute_query(
            query,
            params=(
                employee_name, int(start_period), int(end_period),
                employee_name, int(start_period), int(end_period),
                employee_name, employee_name
            )
        )
        
        if not result:
            return []
        
        monthly_data = []
        for row in result:
            achievement_rate = (row["actual"] / row["target"] * 100) if row["target"] > 0 else 0
            monthly_data.append({
                "month": str(row["month"]),
                "target": row["target"],
                "actual": row["actual"],
                "achievement_rate": round(achievement_rate, 1)
            })
        
        return monthly_data
        
    except Exception as e:
        logger.error(f"월별 상세 데이터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 헬스체크
@router.get("/health")
async def health_check():
    """API 헬스체크"""
    return {
        "status": "healthy",
        "service": "employee_performance_data",
        "type": "data_api",
        "version": "1.0.0",
        "description": "순수 데이터 API (에이전트 없음)"
    }

# API 문서
@router.get("/")
async def api_info():
    """API 정보 및 사용 가능한 엔드포인트 목록"""
    return {
        "service": "Employee Performance Data API",
        "description": "직원 실적 데이터를 조회하는 순수 데이터 API",
        "endpoints": {
            "standard": {
                "GET /employees": "직원 목록 조회",
                "GET /performance/{employee_id}": "월별 실적 데이터 조회",
                "GET /performance/{employee_id}/summary": "실적 요약 정보",
                "GET /performance/{employee_id}/products": "제품별 실적",
                "GET /performance/{employee_id}/customers": "거래처별 실적",
                "GET /targets/{employee_id}": "목표 데이터 조회",
                "GET /departments": "부서 목록 조회"
            },
            "agent_compatible": {
                "GET /agent/performance-data": "에이전트용 실적 데이터 (performance_data)",
                "GET /agent/target-data": "에이전트용 목표 데이터 (target_data)",
                "GET /agent/monthly-breakdown": "에이전트용 월별 상세 데이터"
            }
        },
        "note": "모든 엔드포인트는 JWT 인증이 필요합니다.",
        "agent_info": "agent_compatible 엔드포인트는 에이전트가 필요로 하는 정확한 데이터 구조를 반환합니다."
    }