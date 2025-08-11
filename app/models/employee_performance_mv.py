"""
직원 실적 Materialized View 모델
목표와 실제 매출을 조인한 뷰
"""

from sqlalchemy import Column, Integer, Float, Date, String
from . import Base

class EmployeePerformanceMV(Base):
    """직원 실적 Materialized View (읽기 전용)"""
    __tablename__ = "employee_performance_mv"
    __table_args__ = {'info': {'is_view': True}}  # 뷰임을 명시
    
    # 복합 기본키
    employee_id = Column(Integer, primary_key=True)
    year_month = Column(Date, primary_key=True)
    
    # 직원 정보
    employee_name = Column(String)
    employee_number = Column(String)
    
    # 목표 및 실적
    target_amount = Column(Float)      # employee_performance 테이블에서
    actual_sales = Column(Float)       # sales_records 집계
    achievement_rate = Column(Float)   # 달성률 (%)
    
    # 추가 집계 정보
    sales_count = Column(Integer)
    customer_count = Column(Integer)
    
    def __repr__(self):
        return f"<EmployeePerformanceMV({self.employee_name}, {self.year_month}, 달성률: {self.achievement_rate:.1f}%)>"