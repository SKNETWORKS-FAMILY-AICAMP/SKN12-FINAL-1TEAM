"""
직원 실적 테이블 모델
목표 금액을 저장하고, 실제 매출은 Materialized View에서 가져옴
"""

from sqlalchemy import Column, Integer, Float, Date, DateTime, String, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from . import Base

class EmployeePerformance(Base):
    """직원별 월간 실적 테이블 (목표 저장용)"""
    __tablename__ = "employee_performance"
    
    # 기본 필드
    performance_id = Column(Integer, primary_key=True, index=True, comment="실적 ID")
    
    # 외래키
    employee_id = Column(Integer, ForeignKey("employee_info.employee_info_id"), nullable=False, comment="직원 ID")
    
    # 기간 정보 (년월)
    year_month = Column(Date, nullable=False, comment="실적 년월 (YYYY-MM-01 형식)")
    
    # 목표 금액
    target_amount = Column(Float, default=0.0, nullable=False, comment="목표 매출 금액")
    
    # 메타데이터
    notes = Column(String(500), comment="비고")
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일시")
    
    # 관계 정의
    employee = relationship("EmployeeInfo", backref="performance_records")
    
    # 유니크 제약조건 (직원별 월별 중복 방지)
    __table_args__ = (
        UniqueConstraint('employee_id', 'year_month', name='uq_employee_performance_yearmonth'),
    )
    
    def __repr__(self):
        return f"<EmployeePerformance(employee_id={self.employee_id}, year_month={self.year_month}, target={self.target_amount:,.0f})>"