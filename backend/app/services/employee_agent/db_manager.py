"""
PostgreSQL 기반 직원 실적 데이터베이스 관리 클래스
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class EmployeeDBManager:
    """PostgreSQL 기반 직원 실적 및 목표 데이터베이스 관리 클래스"""
    
    def __init__(self):
        # PostgreSQL 연결 설정
        POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword")
        POSTGRES_DB = os.getenv("POSTGRES_DB", "mydatabase")
        POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
        POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
        
        self.DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        self.engine = create_engine(
            self.DATABASE_URL,
            connect_args={"client_encoding": "utf8"}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_connection(self):
        """데이터베이스 세션을 반환합니다."""
        return self.SessionLocal()
    
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """모든 직원 목록을 반환합니다."""
        with self.get_connection() as db:
            try:
                query = text("""
                    SELECT 
                        ei.employee_info_id as employee_id,
                        ei.name,
                        ei.employee_number,
                        ei.position,
                        b.branch_name as department
                    FROM employee_info ei
                    LEFT JOIN branches b ON ei.branch_id = b.branch_id
                    ORDER BY ei.name
                """)
                
                result = db.execute(query)
                employees = []
                for row in result:
                    employees.append({
                        "employee_id": row.employee_id,
                        "name": row.name,
                        "employee_number": row.employee_number,
                        "position": row.position,
                        "department": row.department
                    })
                return employees
                
            except Exception as e:
                logger.error(f"직원 목록 조회 오류: {e}")
                return []
    
    def get_available_employees(self) -> List[str]:
        """사용 가능한 직원 이름 목록을 반환합니다."""
        employees = self.get_all_employees()
        return [emp["name"] for emp in employees]
    
    def get_employee_performance(self, employee_name: str, start_period: str, end_period: str) -> Dict[str, Any]:
        """직원의 실적 데이터를 조회합니다."""
        with self.get_connection() as db:
            try:
                # 직원 ID 조회
                emp_query = text("""
                    SELECT employee_info_id 
                    FROM employee_info 
                    WHERE name = :name
                """)
                emp_result = db.execute(emp_query, {"name": employee_name}).fetchone()
                
                if not emp_result:
                    return None
                
                employee_id = emp_result.employee_info_id
                
                # 기간 변환
                start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
                end_date = f"{end_period[:4]}-{end_period[4:6]}-31"
                
                # 월별 실적 조회
                monthly_query = text("""
                    SELECT 
                        TO_CHAR(sale_date, 'YYYYMM') as month,
                        SUM(sale_amount) as amount
                    FROM sales_records
                    WHERE employee_id = :employee_id
                        AND sale_date >= :start_date::date
                        AND sale_date <= :end_date::date
                    GROUP BY TO_CHAR(sale_date, 'YYYYMM')
                    ORDER BY month
                """)
                
                monthly_result = db.execute(monthly_query, {
                    "employee_id": employee_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                monthly_breakdown = []
                total_performance = 0
                
                for row in monthly_result:
                    amount = float(row.amount) if row.amount else 0
                    monthly_breakdown.append({
                        "month": row.month,
                        "amount": amount
                    })
                    total_performance += amount
                
                # 제품별 실적 조회
                product_query = text("""
                    SELECT 
                        p.product_name as name,
                        SUM(sr.sale_amount) as amount
                    FROM sales_records sr
                    JOIN products p ON sr.product_id = p.product_id
                    WHERE sr.employee_id = :employee_id
                        AND sr.sale_date >= :start_date::date
                        AND sr.sale_date <= :end_date::date
                    GROUP BY p.product_name
                    ORDER BY amount DESC
                """)
                
                product_result = db.execute(product_query, {
                    "employee_id": employee_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                product_breakdown = []
                for row in product_result:
                    product_breakdown.append({
                        "name": row.name,
                        "amount": float(row.amount) if row.amount else 0
                    })
                
                # 거래처별 실적 조회
                client_query = text("""
                    SELECT 
                        c.customer_name as name,
                        SUM(sr.sale_amount) as amount
                    FROM sales_records sr
                    JOIN customers c ON sr.customer_id = c.customer_id
                    WHERE sr.employee_id = :employee_id
                        AND sr.sale_date >= :start_date::date
                        AND sr.sale_date <= :end_date::date
                    GROUP BY c.customer_name
                    ORDER BY amount DESC
                """)
                
                client_result = db.execute(client_query, {
                    "employee_id": employee_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                client_breakdown = []
                for row in client_result:
                    client_breakdown.append({
                        "name": row.name,
                        "amount": float(row.amount) if row.amount else 0
                    })
                
                return {
                    "total_performance": total_performance,
                    "monthly_breakdown": monthly_breakdown,
                    "product_breakdown": product_breakdown,
                    "client_breakdown": client_breakdown,
                    "monthly_average": total_performance / len(monthly_breakdown) if monthly_breakdown else 0
                }
                
            except Exception as e:
                logger.error(f"실적 데이터 조회 오류: {e}")
                return None
    
    def get_employee_targets(self, employee_name: str, start_period: str, end_period: str) -> Dict[str, Any]:
        """직원의 목표 데이터를 조회합니다."""
        with self.get_connection() as db:
            try:
                # 직원 ID 조회
                emp_query = text("""
                    SELECT employee_info_id 
                    FROM employee_info 
                    WHERE name = :name
                """)
                emp_result = db.execute(emp_query, {"name": employee_name}).fetchone()
                
                if not emp_result:
                    return None
                
                employee_id = emp_result.employee_info_id
                
                # 기간 변환
                start_date = f"{start_period[:4]}-{start_period[4:6]}-01"
                end_date = f"{end_period[:4]}-{end_period[4:6]}-01"
                
                # 월별 목표 vs 실적 조회
                target_query = text("""
                    WITH monthly_targets AS (
                        SELECT 
                            TO_CHAR(year_month, 'YYYYMM') as month,
                            target_amount as target
                        FROM employee_performance
                        WHERE employee_id = :employee_id
                            AND year_month >= :start_date::date
                            AND year_month <= :end_date::date
                    ),
                    monthly_actuals AS (
                        SELECT 
                            TO_CHAR(sale_date, 'YYYYMM') as month,
                            SUM(sale_amount) as actual
                        FROM sales_records
                        WHERE employee_id = :employee_id
                            AND sale_date >= :start_date::date
                            AND sale_date <= :end_date::date
                        GROUP BY TO_CHAR(sale_date, 'YYYYMM')
                    )
                    SELECT 
                        COALESCE(t.month, a.month) as month,
                        COALESCE(t.target, 0) as target,
                        COALESCE(a.actual, 0) as actual
                    FROM monthly_targets t
                    FULL OUTER JOIN monthly_actuals a ON t.month = a.month
                    ORDER BY month
                """)
                
                result = db.execute(target_query, {
                    "employee_id": employee_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                monthly_targets = []
                total_target = 0
                total_actual = 0
                
                for row in result:
                    target = float(row.target) if row.target else 0
                    actual = float(row.actual) if row.actual else 0
                    
                    monthly_targets.append({
                        "month": row.month,
                        "target": target,
                        "actual": actual
                    })
                    
                    total_target += target
                    total_actual += actual
                
                achievement_rate = (total_actual / total_target * 100) if total_target > 0 else 0
                
                # 평가 등급 결정
                if achievement_rate >= 120:
                    evaluation = "매우 우수"
                    grade = "S"
                elif achievement_rate >= 100:
                    evaluation = "우수"
                    grade = "A"
                elif achievement_rate >= 80:
                    evaluation = "양호"
                    grade = "B"
                elif achievement_rate >= 60:
                    evaluation = "보통"
                    grade = "C"
                else:
                    evaluation = "개선 필요"
                    grade = "D"
                
                return {
                    "monthly_targets": monthly_targets,
                    "total_target": total_target,
                    "total_actual": total_actual,
                    "achievement_rate": round(achievement_rate, 1),
                    "gap_amount": total_actual - total_target,
                    "evaluation": evaluation,
                    "grade": grade
                }
                
            except Exception as e:
                logger.error(f"목표 데이터 조회 오류: {e}")
                return None
    
    def get_employee_performance_data(self, employee_name: str = None,
                                     start_period: str = None,
                                     end_period: str = None) -> pd.DataFrame:
        """직원의 실적 데이터를 DataFrame으로 반환합니다. (호환성 유지)"""
        if not employee_name:
            return pd.DataFrame()
        
        data = self.get_employee_performance(employee_name, start_period, end_period)
        if not data:
            return pd.DataFrame()
        
        # DataFrame으로 변환
        monthly_data = data.get("monthly_breakdown", [])
        if monthly_data:
            df = pd.DataFrame(monthly_data)
            df["담당자"] = employee_name
            return df
        
        return pd.DataFrame()
    
    def get_employee_target_data(self, employee_name: str = None,
                                start_period: str = None,
                                end_period: str = None) -> pd.DataFrame:
        """직원의 목표 데이터를 DataFrame으로 반환합니다. (호환성 유지)"""
        if not employee_name:
            return pd.DataFrame()
        
        data = self.get_employee_targets(employee_name, start_period, end_period)
        if not data:
            return pd.DataFrame()
        
        # DataFrame으로 변환
        monthly_data = data.get("monthly_targets", [])
        if monthly_data:
            df = pd.DataFrame(monthly_data)
            df["담당자"] = employee_name
            df["년월"] = df["month"]
            df["목표"] = df["target"]
            return df[["담당자", "년월", "목표", "actual"]]
        
        return pd.DataFrame()