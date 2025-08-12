import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, and_, func
from sqlalchemy.orm import sessionmaker, Session
import os
import logging

# 모델 임포트
from app.models.employee_info import EmployeeInfo
from app.models.employee_performance import EmployeePerformance
from app.models.employee_performance_mv import EmployeePerformanceMV
from app.models.sales_records import SalesRecord
from app.models.employees import Employee

logger = logging.getLogger(__name__)

class EmployeeDBManager:
    """PostgreSQL 기반 직원 실적 및 목표 데이터베이스 관리 클래스"""
    
    def __init__(self):
        # PostgreSQL 연결 설정 (.env 파일과 일치하도록 수정)
        self.db_url = os.getenv(
            "DATABASE_URL",
            f"postgresql://{os.getenv('POSTGRES_USER', 'myuser')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'mypassword')}@"
            f"{os.getenv('POSTGRES_HOST', 'postgres')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'mydatabase')}"
        )
        
        # SQLAlchemy 엔진 및 세션 설정
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        """데이터베이스 세션을 반환합니다."""
        return self.SessionLocal()
    
    def get_available_employees(self) -> List[str]:
        """사용 가능한 직원 목록을 반환합니다."""
        try:
            with self.get_session() as session:
                # employee_info 테이블에서 활성 직원 조회
                employees = session.query(EmployeeInfo.name).distinct().all()
                return [emp[0] for emp in employees if emp[0]]
        except Exception as e:
            logger.error(f"직원 목록 조회 오류: {e}")
            return []
    
    def get_employee_performance_data(self, employee_name: str = None,
                                     start_period: str = None,
                                     end_period: str = None) -> pd.DataFrame:
        """직원의 실적 데이터를 조회합니다."""
        try:
            with self.get_session() as session:
                # 직원 ID 찾기
                employee = session.query(EmployeeInfo).filter(
                    EmployeeInfo.name == employee_name
                ).first()
                
                if not employee:
                    logger.warning(f"직원을 찾을 수 없습니다: {employee_name}")
                    return pd.DataFrame()
                
                # 기간 변환 (YYYYMM → YYYY-MM-01)
                if start_period:
                    start_date = datetime.strptime(start_period, "%Y%m").date()
                else:
                    start_date = datetime.now().date() - timedelta(days=90)
                
                if end_period:
                    end_date = datetime.strptime(end_period, "%Y%m").date()
                    # 월말로 설정
                    if end_date.month == 12:
                        end_date = end_date.replace(day=31)
                    else:
                        end_date = end_date.replace(month=end_date.month + 1, day=1) - timedelta(days=1)
                else:
                    end_date = datetime.now().date()
                
                # Materialized View에서 실적 데이터 조회
                query = session.query(EmployeePerformanceMV).filter(
                    and_(
                        EmployeePerformanceMV.employee_id == employee.employee_info_id,
                        EmployeePerformanceMV.year_month >= start_date,
                        EmployeePerformanceMV.year_month <= end_date
                    )
                ).all()
                
                # DataFrame으로 변환
                data = []
                for record in query:
                    data.append({
                        'employee_id': record.employee_id,
                        'employee_name': record.employee_name,
                        'year_month': record.year_month.strftime("%Y%m"),
                        'target_amount': float(record.target_amount or 0),
                        'actual_sales': float(record.actual_sales or 0),
                        'achievement_rate': float(record.achievement_rate or 0),
                        'sales_count': record.sales_count or 0,
                        'customer_count': record.customer_count or 0
                    })
                
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"실적 데이터 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_employee_target_data(self, employee_name: str = None,
                                start_period: str = None,
                                end_period: str = None) -> pd.DataFrame:
        """직원의 목표 데이터를 조회합니다."""
        try:
            with self.get_session() as session:
                # 직원 ID 찾기
                employee = session.query(EmployeeInfo).filter(
                    EmployeeInfo.name == employee_name
                ).first()
                
                if not employee:
                    return pd.DataFrame()
                
                # 기간 변환
                if start_period:
                    start_date = datetime.strptime(start_period, "%Y%m").date()
                else:
                    start_date = datetime.now().date() - timedelta(days=90)
                
                if end_period:
                    end_date = datetime.strptime(end_period, "%Y%m").date()
                else:
                    end_date = datetime.now().date()
                
                # 목표 데이터 조회
                query = session.query(EmployeePerformance).filter(
                    and_(
                        EmployeePerformance.employee_id == employee.employee_info_id,
                        EmployeePerformance.year_month >= start_date,
                        EmployeePerformance.year_month <= end_date
                    )
                ).all()
                
                # DataFrame으로 변환
                data = []
                for record in query:
                    data.append({
                        '직원명': employee_name,
                        '년월': int(record.year_month.strftime("%Y%m")),
                        '목표': float(record.target_amount or 0)
                    })
                
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"목표 데이터 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_performance_summary(self, employee_name: str, 
                              start_period: str, end_period: str) -> Dict[str, Any]:
        """직원의 실적 요약을 반환합니다."""
        try:
            # 실적 데이터 조회
            df = self.get_employee_performance_data(employee_name, start_period, end_period)
            
            if df.empty:
                return {
                    "employee_name": employee_name,
                    "period": f"{start_period}~{end_period}",
                    "total_performance": 0,
                    "monthly_breakdown": [],
                    "product_breakdown": [],
                    "client_breakdown": []
                }
            
            # 총 실적 계산
            total_performance = df['actual_sales'].sum()
            
            # 월별 분석
            monthly_breakdown = []
            for _, row in df.iterrows():
                monthly_breakdown.append({
                    "month": row['year_month'],
                    "amount": int(row['actual_sales']),
                    "count": int(row['sales_count'])
                })
            
            # 제품별 분석 (sales_records에서 직접 조회)
            product_breakdown = self._get_product_breakdown(
                employee_name, start_period, end_period
            )
            
            # 거래처별 분석
            client_breakdown = self._get_client_breakdown(
                employee_name, start_period, end_period
            )
            
            return {
                "employee_name": employee_name,
                "period": f"{start_period}~{end_period}",
                "total_performance": int(total_performance),
                "monthly_breakdown": monthly_breakdown,
                "product_breakdown": product_breakdown,
                "client_breakdown": client_breakdown
            }
            
        except Exception as e:
            logger.error(f"실적 요약 계산 오류: {e}")
            return {
                "employee_name": employee_name,
                "period": f"{start_period}~{end_period}",
                "total_performance": 0,
                "monthly_breakdown": [],
                "product_breakdown": [],
                "client_breakdown": []
            }
    
    def _get_product_breakdown(self, employee_name: str, 
                              start_period: str, end_period: str) -> List[Dict]:
        """제품별 실적 분석"""
        try:
            with self.get_session() as session:
                # 직원 ID 찾기
                employee = session.query(EmployeeInfo).filter(
                    EmployeeInfo.name == employee_name
                ).first()
                
                if not employee:
                    return []
                
                # 기간 변환
                start_date = datetime.strptime(start_period, "%Y%m").date()
                end_date = datetime.strptime(end_period, "%Y%m").date()
                if end_date.month == 12:
                    end_date = end_date.replace(day=31)
                else:
                    end_date = end_date.replace(month=end_date.month + 1, day=1) - timedelta(days=1)
                
                # 제품별 매출 집계
                query = text("""
                    SELECT 
                        p.product_name,
                        SUM(sr.sale_amount) as total_amount
                    FROM sales_records sr
                    LEFT JOIN products p ON sr.product_id = p.product_id
                    WHERE sr.employee_id = :employee_id
                        AND sr.sale_date >= :start_date
                        AND sr.sale_date <= :end_date
                    GROUP BY p.product_name
                    ORDER BY total_amount DESC
                    LIMIT 10
                """)
                
                result = session.execute(query, {
                    'employee_id': employee.employee_info_id,
                    'start_date': start_date,
                    'end_date': end_date
                }).fetchall()
                
                product_breakdown = []
                for row in result:
                    product_breakdown.append({
                        "name": row[0] or "기타",
                        "amount": int(row[1])
                    })
                
                return product_breakdown
                
        except Exception as e:
            logger.error(f"제품별 분석 오류: {e}")
            return []
    
    def _get_client_breakdown(self, employee_name: str, 
                             start_period: str, end_period: str) -> List[Dict]:
        """거래처별 실적 분석"""
        try:
            with self.get_session() as session:
                # 직원 ID 찾기
                employee = session.query(EmployeeInfo).filter(
                    EmployeeInfo.name == employee_name
                ).first()
                
                if not employee:
                    return []
                
                # 기간 변환
                start_date = datetime.strptime(start_period, "%Y%m").date()
                end_date = datetime.strptime(end_period, "%Y%m").date()
                if end_date.month == 12:
                    end_date = end_date.replace(day=31)
                else:
                    end_date = end_date.replace(month=end_date.month + 1, day=1) - timedelta(days=1)
                
                # 거래처별 매출 집계
                query = text("""
                    SELECT 
                        c.customer_name,
                        SUM(sr.sale_amount) as total_amount
                    FROM sales_records sr
                    LEFT JOIN customers c ON sr.customer_id = c.customer_id
                    WHERE sr.employee_id = :employee_id
                        AND sr.sale_date >= :start_date
                        AND sr.sale_date <= :end_date
                    GROUP BY c.customer_name
                    ORDER BY total_amount DESC
                    LIMIT 10
                """)
                
                result = session.execute(query, {
                    'employee_id': employee.employee_info_id,
                    'start_date': start_date,
                    'end_date': end_date
                }).fetchall()
                
                client_breakdown = []
                for row in result:
                    client_breakdown.append({
                        "name": row[0] or "기타",
                        "amount": int(row[1])
                    })
                
                return client_breakdown
                
        except Exception as e:
            logger.error(f"거래처별 분석 오류: {e}")
            return []
    
    def analyze_performance_trend(self, employee_name: str,
                                start_period: str, end_period: str) -> Dict[str, Any]:
        """실적 트렌드를 분석합니다."""
        try:
            summary = self.get_performance_summary(employee_name, start_period, end_period)
            monthly_data = summary["monthly_breakdown"]
            
            if len(monthly_data) < 2:
                return {
                    "trend": "데이터 부족",
                    "analysis": "트렌드 분석을 위해서는 최소 2개월 이상의 데이터가 필요합니다."
                }
            
            # 월별 실적 추이 분석
            amounts = [data["amount"] for data in monthly_data]
            
            # 단순 트렌드 계산
            if len(amounts) >= 3:
                recent_avg = sum(amounts[-2:]) / 2
                early_avg = sum(amounts[:2]) / 2
                
                if recent_avg > early_avg * 1.1:
                    trend = "상승"
                elif recent_avg < early_avg * 0.9:
                    trend = "하락"
                else:
                    trend = "안정"
            else:
                if amounts[-1] > amounts[0]:
                    trend = "상승"
                elif amounts[-1] < amounts[0]:
                    trend = "하락"
                else:
                    trend = "안정"
            
            return {
                "trend": trend,
                "analysis": f"분석 기간 동안 실적은 {trend} 추세를 보이고 있습니다.",
                "monthly_amounts": amounts
            }
            
        except Exception as e:
            logger.error(f"트렌드 분석 오류: {e}")
            return {
                "trend": "분석 실패",
                "analysis": "트렌드 분석 중 오류가 발생했습니다."
            }
    
    def get_target_vs_performance(self, employee_name: str,
                                 start_period: str, end_period: str) -> Dict[str, Any]:
        """목표 대비 실적을 비교 분석합니다."""
        try:
            # 실적 데이터 조회
            df = self.get_employee_performance_data(employee_name, start_period, end_period)
            
            if df.empty:
                return {
                    "total_performance": 0,
                    "total_target": 0,
                    "achievement_rate": 0,
                    "evaluation": "데이터 없음",
                    "grade": "N/A",
                    "gap_amount": 0
                }
            
            # 총 실적과 목표 계산
            total_performance = df['actual_sales'].sum()
            total_target = df['target_amount'].sum()
            
            # 목표가 0인 경우 처리
            if total_target <= 0:
                total_target = total_performance * 0.9  # 가상 목표 설정
            
            # 달성률 계산
            achievement_rate = (total_performance / total_target * 100) if total_target > 0 else 0
            
            # 평가 등급 결정
            if achievement_rate >= 120:
                evaluation = "매우 우수"
                grade = "A+"
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
                "total_performance": int(total_performance),
                "total_target": int(total_target),
                "achievement_rate": float(achievement_rate),
                "gap_amount": int(total_performance - total_target),
                "evaluation": evaluation,
                "grade": grade
            }
            
        except Exception as e:
            logger.error(f"목표 대비 실적 분석 오류: {e}")
            return {
                "total_performance": 0,
                "total_target": 0,
                "achievement_rate": 0,
                "evaluation": "분석 실패",
                "grade": "N/A",
                "gap_amount": 0
            }