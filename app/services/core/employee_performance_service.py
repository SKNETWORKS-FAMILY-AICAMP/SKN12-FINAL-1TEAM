"""
직원 실적 관리 서비스
직원별 실적 데이터 조회 및 분석 기능 제공
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

class EmployeePerformanceService:
    """직원 실적 관리 서비스 클래스"""
    
    def __init__(self):
        """서비스 초기화 - DB 연결 설정"""
        self.engine = create_engine(settings.get_database_url())
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_employees(self, department: Optional[str] = None, is_active: bool = True) -> List[Dict[str, Any]]:
        """
        직원 목록 조회
        
        Args:
            department: 부서명 필터
            is_active: 활성 직원만 조회 여부
            
        Returns:
            List[Dict]: 직원 정보 리스트
        """
        with self.SessionLocal() as db:
            try:
                base_query = """
                    SELECT 
                        e.employee_id,
                        e.name,
                        e.email,
                        e.role,
                        ei.employee_number as 사번,
                        b.branch_name as department
                    FROM employees e
                    LEFT JOIN employee_info ei ON e.employee_id = ei.employee_id
                    LEFT JOIN branches b ON ei.branch_id = b.branch_id
                    WHERE e.is_deleted = false
                """
                
                params = {}
                conditions = []
                
                if is_active:
                    conditions.append("e.is_active = true")
                
                if department:
                    conditions.append("b.branch_name = :department")
                    params['department'] = department
                
                if conditions:
                    base_query += " AND " + " AND ".join(conditions)
                
                base_query += " ORDER BY e.name"
                
                result = db.execute(text(base_query), params)
                
                employees = []
                for row in result:
                    employees.append({
                        "employee_id": row.employee_id,
                        "name": row.name,
                        "사번": row.사번,
                        "department": row.department,
                        "email": row.email,
                        "role": row.role
                    })
                
                return employees
                
            except Exception as e:
                logger.error(f"직원 목록 조회 오류: {e}")
                raise
    
    def get_performance_data(
        self, 
        employee_id: int, 
        start_period: str, 
        end_period: str
    ) -> List[Dict[str, Any]]:
        """
        직원 실적 데이터 조회
        
        Args:
            employee_id: 직원 ID
            start_period: 시작 기간 (YYYYMM)
            end_period: 종료 기간 (YYYYMM)
            
        Returns:
            List[Dict]: 실적 데이터 리스트
        """
        with self.SessionLocal() as db:
            try:
                start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
                end_date = f"{end_period[:4]}-{end_period[4:6]}-01"
                
                query = text("""
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
                    WHERE employee_id = :employee_id
                        AND year_month >= CAST(:start_date AS date)
                        AND year_month <= CAST(:end_date AS date)
                    ORDER BY year_month
                """)
                
                result = db.execute(query, {
                    'employee_id': employee_id,
                    'start_date': start_date,
                    'end_date': end_date
                })
                
                performance_data = []
                for row in result:
                    performance_data.append({
                        "employee_id": row.employee_id,
                        "employee_name": row.employee_name,
                        "year_month": row.year_month,
                        "target_amount": float(row.target_amount) if row.target_amount else 0,
                        "actual_sales": float(row.actual_sales) if row.actual_sales else 0,
                        "achievement_rate": float(row.achievement_rate) if row.achievement_rate else 0,
                        "sales_count": row.sales_count or 0,
                        "customer_count": row.customer_count or 0
                    })
                
                return performance_data
                
            except Exception as e:
                logger.error(f"실적 데이터 조회 오류: {e}")
                raise
    
    def get_performance_summary(
        self, 
        employee_id: int, 
        start_period: str, 
        end_period: str
    ) -> Dict[str, Any]:
        """
        직원 실적 요약 정보 조회
        
        Args:
            employee_id: 직원 ID
            start_period: 시작 기간 (YYYYMM)
            end_period: 종료 기간 (YYYYMM)
            
        Returns:
            Dict: 요약 정보
        """
        with self.SessionLocal() as db:
            try:
                start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
                end_date = f"{end_period[:4]}-{end_period[4:6]}-01"
                
                query = text("""
                    SELECT 
                        COUNT(*) as month_count,
                        SUM(target_amount) as total_target,
                        SUM(actual_sales) as total_sales,
                        AVG(achievement_rate) as avg_achievement_rate,
                        SUM(sales_count) as total_sales_count,
                        COUNT(DISTINCT customer_count) as unique_customers
                    FROM employee_performance_mv
                    WHERE employee_id = :employee_id
                        AND year_month >= CAST(:start_date AS date)
                        AND year_month <= CAST(:end_date AS date)
                """)
                
                result = db.execute(query, {
                    'employee_id': employee_id,
                    'start_date': start_date,
                    'end_date': end_date
                }).fetchone()
                
                if result:
                    return {
                        "month_count": result.month_count or 0,
                        "total_target": float(result.total_target) if result.total_target else 0,
                        "total_sales": float(result.total_sales) if result.total_sales else 0,
                        "avg_achievement_rate": float(result.avg_achievement_rate) if result.avg_achievement_rate else 0,
                        "total_sales_count": result.total_sales_count or 0,
                        "unique_customers": result.unique_customers or 0
                    }
                
                return {
                    "month_count": 0,
                    "total_target": 0,
                    "total_sales": 0,
                    "avg_achievement_rate": 0,
                    "total_sales_count": 0,
                    "unique_customers": 0
                }
                
            except Exception as e:
                logger.error(f"실적 요약 조회 오류: {e}")
                raise
    
    def get_product_performance(
        self, 
        employee_id: int, 
        start_period: str, 
        end_period: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        직원의 제품별 실적 조회
        
        Args:
            employee_id: 직원 ID
            start_period: 시작 기간 (YYYYMM)
            end_period: 종료 기간 (YYYYMM)
            limit: 상위 N개 제품
            
        Returns:
            List[Dict]: 제품별 실적 리스트
        """
        with self.SessionLocal() as db:
            try:
                start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
                end_date = f"{end_period[:4]}-{end_period[4:6]}-31"
                
                query = text("""
                    SELECT 
                        p.product_id,
                        p.product_name,
                        SUM(sr.sale_amount) as total_amount,
                        COUNT(sr.sale_id) as sales_count
                    FROM sales_records sr
                    INNER JOIN products p ON sr.product_id = p.product_id
                    WHERE sr.employee_id = :employee_id
                        AND sr.sale_date >= CAST(:start_date AS date)
                        AND sr.sale_date <= CAST(:end_date AS date)
                    GROUP BY p.product_id, p.product_name
                    ORDER BY total_amount DESC
                    LIMIT :limit
                """)
                
                result = db.execute(query, {
                    'employee_id': employee_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'limit': limit
                })
                
                products = []
                total_sales = 0
                
                for row in result:
                    total_sales += float(row.total_amount)
                    products.append({
                        "product_id": row.product_id,
                        "product_name": row.product_name,
                        "total_amount": float(row.total_amount),
                        "sales_count": row.sales_count
                    })
                
                # 비율 계산
                for product in products:
                    product["percentage"] = round((product["total_amount"] / total_sales * 100), 2) if total_sales > 0 else 0
                
                return products
                
            except Exception as e:
                logger.error(f"제품별 실적 조회 오류: {e}")
                raise
    
    def get_customer_performance(
        self, 
        employee_id: int, 
        start_period: str, 
        end_period: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        직원의 고객별 실적 조회
        
        Args:
            employee_id: 직원 ID
            start_period: 시작 기간 (YYYYMM)
            end_period: 종료 기간 (YYYYMM)
            limit: 상위 N개 고객
            
        Returns:
            List[Dict]: 고객별 실적 리스트
        """
        with self.SessionLocal() as db:
            try:
                start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
                end_date = f"{end_period[:4]}-{end_period[4:6]}-31"
                
                query = text("""
                    SELECT 
                        c.customer_id,
                        c.customer_name,
                        c.customer_grade,
                        SUM(sr.sale_amount) as total_amount,
                        COUNT(sr.sale_id) as sales_count
                    FROM sales_records sr
                    INNER JOIN customers c ON sr.customer_id = c.customer_id
                    WHERE sr.employee_id = :employee_id
                        AND sr.sale_date >= CAST(:start_date AS date)
                        AND sr.sale_date <= CAST(:end_date AS date)
                    GROUP BY c.customer_id, c.customer_name, c.customer_grade
                    ORDER BY total_amount DESC
                    LIMIT :limit
                """)
                
                result = db.execute(query, {
                    'employee_id': employee_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'limit': limit
                })
                
                customers = []
                total_sales = 0
                
                for row in result:
                    total_sales += float(row.total_amount)
                    customers.append({
                        "customer_id": row.customer_id,
                        "customer_name": row.customer_name,
                        "customer_grade": row.customer_grade,
                        "total_amount": float(row.total_amount),
                        "sales_count": row.sales_count
                    })
                
                # 비율 계산
                for customer in customers:
                    customer["percentage"] = round((customer["total_amount"] / total_sales * 100), 2) if total_sales > 0 else 0
                
                return customers
                
            except Exception as e:
                logger.error(f"고객별 실적 조회 오류: {e}")
                raise
    
    def get_departments(self) -> List[str]:
        """
        부서 목록 조회
        
        Returns:
            List[str]: 부서명 리스트
        """
        with self.SessionLocal() as db:
            try:
                query = text("""
                    SELECT DISTINCT branch_name as department
                    FROM branches
                    WHERE branch_name IS NOT NULL
                    ORDER BY branch_name
                """)
                
                result = db.execute(query)
                
                return [row.department for row in result]
                
            except Exception as e:
                logger.error(f"부서 목록 조회 오류: {e}")
                raise
    
    def get_employee_info_by_name(self, employee_name: str) -> Optional[Dict[str, Any]]:
        """
        직원명으로 직원 정보 조회
        
        Args:
            employee_name: 직원명
            
        Returns:
            Dict: 직원 정보 또는 None
        """
        with self.SessionLocal() as db:
            try:
                query = text("""
                    SELECT 
                        e.employee_id,
                        e.name,
                        ei.employee_number as 사번,
                        b.branch_name as department
                    FROM employees e
                    LEFT JOIN employee_info ei ON e.employee_id = ei.employee_id
                    LEFT JOIN branches b ON ei.branch_id = b.branch_id
                    WHERE e.name = :name AND e.is_deleted = false
                """)
                
                result = db.execute(query, {'name': employee_name}).fetchone()
                
                if result:
                    return {
                        "employee_id": result.employee_id,
                        "name": result.name,
                        "사번": result.사번,
                        "department": result.department
                    }
                
                return None
                
            except Exception as e:
                logger.error(f"직원 정보 조회 오류: {e}")
                raise

# 싱글톤 인스턴스 생성
employee_performance_service = EmployeePerformanceService()