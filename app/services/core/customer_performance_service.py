"""
거래처 성과 관리 서비스
거래처별 월간 성과 데이터 조회 및 분석 기능 제공
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CustomerPerformanceService:
    """거래처 성과 관리 서비스 클래스"""
    
    def __init__(self, db: Session):
        """
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
    
    def get_customer_info(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        거래처 기본 정보 조회
        
        Args:
            customer_id: 거래처 ID
            
        Returns:
            Dict: 거래처 정보 또는 None
        """
        try:
            query = text("""
                SELECT 
                    customer_id,
                    customer_name,
                    customer_grade,
                    address,
                    doctor_name,
                    total_patients,
                    notes
                FROM customers
                WHERE customer_id = :customer_id
                    AND is_deleted = false
            """)
            
            result = self.db.execute(query, {"customer_id": customer_id}).fetchone()
            
            if result:
                return {
                    "customer_id": result.customer_id,
                    "customer_name": result.customer_name,
                    "customer_grade": result.customer_grade,
                    "address": result.address,
                    "doctor_name": result.doctor_name,
                    "total_patients": result.total_patients,
                    "notes": result.notes
                }
            return None
            
        except Exception as e:
            logger.error(f"거래처 정보 조회 중 오류: {e}")
            raise
    
    def get_monthly_performance(
        self, 
        customer_id: int, 
        start_month: str, 
        end_month: str
    ) -> List[Dict[str, Any]]:
        """
        거래처의 월별 성과 데이터 조회
        
        Args:
            customer_id: 거래처 ID
            start_month: 시작 월 (YYYYMM 형식)
            end_month: 종료 월 (YYYYMM 형식)
            
        Returns:
            List[Dict]: 월별 성과 데이터 목록
        """
        try:
            # YYYYMM을 YYYY-MM 형식으로 변환
            start_ym = f"{start_month[:4]}-{start_month[4:6]}"
            end_ym = f"{end_month[:4]}-{end_month[4:6]}"
            
            # customer_monthly_performance_mv 테이블에서 데이터 조회
            query = text("""
                SELECT 
                    year_month,
                    monthly_sales,
                    budget_used,
                    visit_count,
                    patient_count
                FROM customer_monthly_performance_mv
                WHERE customer_id = :customer_id
                    AND year_month BETWEEN :start_month AND :end_month
                ORDER BY year_month
            """)
            
            results = self.db.execute(
                query,
                {
                    "customer_id": customer_id,
                    "start_month": start_ym,
                    "end_month": end_ym
                }
            ).fetchall()
            
            # 데이터가 없는 경우, sales_records에서 직접 집계
            if not results:
                logger.info(f"MV에 데이터가 없어 sales_records에서 직접 집계: customer_id={customer_id}")
                results = self._aggregate_from_sales_records(customer_id, start_month, end_month)
            
            # 결과 포맷팅
            monthly_data = []
            for row in results:
                # year_month를 YYYYMM 형식으로 변환
                if hasattr(row, 'year_month') and row.year_month:
                    if '-' in str(row.year_month):
                        month = str(row.year_month).replace('-', '')
                    else:
                        month = str(row.year_month)
                else:
                    month = ""
                
                # 환자수는 MV에서 직접 가져옴
                patient_count = 0
                if hasattr(row, 'patient_count') and row.patient_count:
                    patient_count = row.patient_count
                elif hasattr(row, 'visit_count') and row.visit_count:
                    # patient_count가 없는 경우 fallback
                    patient_count = row.visit_count * 100  # 방문당 평균 환자수를 가정
                
                monthly_data.append({
                    "month": month,
                    "매출": row.monthly_sales or 0,
                    "사용예산": row.budget_used or 0,
                    "총환자수": patient_count
                })
            
            return monthly_data
            
        except Exception as e:
            logger.error(f"월별 성과 데이터 조회 중 오류: {e}")
            return []
    
    def _aggregate_from_sales_records(
        self,
        customer_id: int,
        start_month: str,
        end_month: str
    ) -> List:
        """
        sales_records 테이블에서 직접 월별 데이터 집계
        
        Args:
            customer_id: 거래처 ID
            start_month: 시작 월 (YYYYMM)
            end_month: 종료 월 (YYYYMM)
            
        Returns:
            List: 집계된 데이터
        """
        try:
            # YYYYMM을 날짜 범위로 변환
            start_date = f"{start_month[:4]}-{start_month[4:6]}-01"
            end_year = int(end_month[:4])
            end_month_int = int(end_month[4:6])
            
            # 마지막 날 계산
            if end_month_int == 12:
                end_date = f"{end_year}-12-31"
            else:
                next_month = f"{end_year:04d}-{end_month_int+1:02d}-01"
                end_date = f"{end_year:04d}-{end_month_int:02d}-31"  # 간단히 31일로 설정
            
            query = text("""
                SELECT 
                    TO_CHAR(sale_date, 'YYYY-MM') as year_month,
                    SUM(sales_amount) as monthly_sales,
                    SUM(
                        CASE 
                            WHEN sales_amount > 0 THEN sales_amount * 0.15
                            ELSE 0
                        END
                    ) as budget_used,
                    COUNT(DISTINCT sale_date) as visit_count
                FROM sales_records
                WHERE customer_id = :customer_id
                    AND sale_date >= :start_date::date
                    AND sale_date < :end_date::date + INTERVAL '1 day'
                    AND is_deleted = false
                GROUP BY TO_CHAR(sale_date, 'YYYY-MM')
                ORDER BY year_month
            """)
            
            results = self.db.execute(
                query,
                {
                    "customer_id": customer_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            ).fetchall()
            
            return results
            
        except Exception as e:
            logger.error(f"sales_records 집계 중 오류: {e}")
            return []
    
    def calculate_summary(self, monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        월별 데이터의 요약 통계 계산
        
        Args:
            monthly_data: 월별 성과 데이터 목록
            
        Returns:
            Dict: 요약 통계
        """
        if not monthly_data:
            return {
                "total_sales": 0,
                "total_budget": 0,
                "total_patients": 0,
                "average_monthly_sales": 0,
                "average_monthly_budget": 0,
                "average_monthly_patients": 0,
                "month_count": 0
            }
        
        total_sales = sum(item.get("매출", 0) for item in monthly_data)
        total_budget = sum(item.get("사용예산", 0) for item in monthly_data)
        total_patients = sum(item.get("총환자수", 0) for item in monthly_data)
        month_count = len(monthly_data)
        
        return {
            "total_sales": total_sales,
            "total_budget": total_budget,
            "total_patients": total_patients,
            "average_monthly_sales": total_sales // month_count if month_count > 0 else 0,
            "average_monthly_budget": total_budget // month_count if month_count > 0 else 0,
            "average_monthly_patients": total_patients // month_count if month_count > 0 else 0,
            "month_count": month_count
        }
    
    def compare_periods(
        self,
        period1_summary: Dict[str, Any],
        period2_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        두 기간의 성과 비교 분석
        
        Args:
            period1_summary: 첫 번째 기간 요약
            period2_summary: 두 번째 기간 요약
            
        Returns:
            Dict: 비교 분석 결과
        """
        def calculate_change(old_value: float, new_value: float) -> Dict[str, Any]:
            """변화량 및 변화율 계산"""
            if old_value == 0:
                if new_value == 0:
                    return {"amount": 0, "rate": 0.0}
                else:
                    return {"amount": new_value, "rate": 100.0}
            
            amount = new_value - old_value
            rate = (amount / old_value) * 100
            
            return {
                "amount": amount,
                "rate": round(rate, 2)
            }
        
        comparison = {
            "sales_change": calculate_change(
                period1_summary.get("total_sales", 0),
                period2_summary.get("total_sales", 0)
            ),
            "budget_change": calculate_change(
                period1_summary.get("total_budget", 0),
                period2_summary.get("total_budget", 0)
            ),
            "patients_change": calculate_change(
                period1_summary.get("total_patients", 0),
                period2_summary.get("total_patients", 0)
            ),
            "avg_monthly_sales_change": calculate_change(
                period1_summary.get("average_monthly_sales", 0),
                period2_summary.get("average_monthly_sales", 0)
            ),
            "avg_monthly_budget_change": calculate_change(
                period1_summary.get("average_monthly_budget", 0),
                period2_summary.get("average_monthly_budget", 0)
            ),
            "avg_monthly_patients_change": calculate_change(
                period1_summary.get("average_monthly_patients", 0),
                period2_summary.get("average_monthly_patients", 0)
            )
        }
        
        return comparison