"""
직원 실적 관리 서비스
목표 설정 및 실적 조회
"""

import logging
from datetime import date
from typing import List, Dict, Any, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.employee_performance import EmployeePerformance
from app.models.employee_performance_mv import EmployeePerformanceMV

logger = logging.getLogger(__name__)

class EmployeePerformanceService:
    """직원 실적 관리 서비스"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def set_target(self, employee_id: int, year_month: date, target_amount: float, notes: str = None) -> Dict[str, Any]:
        """목표 설정"""
        try:
            # 기존 목표 조회
            result = await self.session.execute(
                select(EmployeePerformance).where(
                    EmployeePerformance.employee_id == employee_id,
                    EmployeePerformance.year_month == year_month
                )
            )
            performance = result.scalar_one_or_none()
            
            if performance:
                # 업데이트
                performance.target_amount = target_amount
                if notes:
                    performance.notes = notes
                logger.info(f"목표 업데이트: 직원 {employee_id}, {year_month}, 목표: {target_amount:,.0f}")
            else:
                # 신규 생성
                performance = EmployeePerformance(
                    employee_id=employee_id,
                    year_month=year_month,
                    target_amount=target_amount,
                    notes=notes
                )
                self.session.add(performance)
                logger.info(f"목표 신규 설정: 직원 {employee_id}, {year_month}, 목표: {target_amount:,.0f}")
            
            await self.session.commit()
            return {'success': True, 'message': '목표 설정 완료'}
            
        except Exception as e:
            logger.error(f"목표 설정 실패: {e}")
            await self.session.rollback()
            return {'success': False, 'message': str(e)}
    
    async def refresh_performance_view(self) -> bool:
        """Materialized View 갱신"""
        try:
            await self.session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY employee_performance_mv"))
            await self.session.commit()
            logger.info("직원 실적 뷰 갱신 완료")
            return True
        except Exception as e:
            logger.error(f"직원 실적 뷰 갱신 실패: {e}")
            return False
    
    async def get_employee_performance(self, employee_id: int, year_month: date) -> Dict[str, Any]:
        """특정 직원의 월간 실적 조회 (목표 대비 실적)"""
        try:
            result = await self.session.execute(
                select(EmployeePerformanceMV).where(
                    EmployeePerformanceMV.employee_id == employee_id,
                    EmployeePerformanceMV.year_month == year_month
                )
            )
            performance = result.scalar_one_or_none()
            
            if performance:
                return {
                    'employee_id': performance.employee_id,
                    'employee_name': performance.employee_name,
                    'employee_number': performance.employee_number,
                    'year_month': performance.year_month.isoformat(),
                    'target_amount': float(performance.target_amount),
                    'actual_sales': float(performance.actual_sales),
                    'achievement_rate': float(performance.achievement_rate),
                    'sales_count': performance.sales_count,
                    'customer_count': performance.customer_count
                }
            return None
            
        except Exception as e:
            logger.error(f"실적 조회 실패: {e}")
            return None
    
    async def get_monthly_ranking(self, year_month: date) -> List[Dict[str, Any]]:
        """월간 실적 순위"""
        try:
            query = text("""
                SELECT 
                    *,
                    RANK() OVER (ORDER BY actual_sales DESC) as rank
                FROM employee_performance_mv
                WHERE year_month = :year_month
                ORDER BY actual_sales DESC
            """)
            
            result = await self.session.execute(query, {'year_month': year_month})
            rankings = result.fetchall()
            
            return [
                {
                    'rank': row.rank,
                    'employee_id': row.employee_id,
                    'employee_name': row.employee_name,
                    'employee_number': row.employee_number,
                    'actual_sales': float(row.actual_sales),
                    'sales_count': row.sales_count,
                    'customer_count': row.customer_count
                }
                for row in rankings
            ]
            
        except Exception as e:
            logger.error(f"순위 조회 실패: {e}")
            return []