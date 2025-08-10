"""
지점별 목표 및 실적 모델
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, func, UniqueConstraint
from sqlalchemy.orm import relationship
from . import Base

class BranchTarget(Base):
    """지점별 목표 및 실적 테이블"""
    __tablename__ = "branch_targets"
    
    # 기본 필드
    target_id = Column(Integer, primary_key=True, index=True, comment="목표 ID")
    
    # 외래키
    branch_id = Column(Integer, ForeignKey("branches.branch_id"), nullable=False, comment="지점 ID")
    employee_info_id = Column(Integer, ForeignKey("employee_info.employee_info_id"), nullable=False, comment="직원 인사정보 ID")
    
    # 기간 정보
    target_year = Column(Integer, nullable=False, comment="목표 년도")
    target_month = Column(Integer, nullable=False, comment="목표 월")
    target_date = Column(Date, nullable=False, comment="목표 년월 (YYYY-MM-01)")
    
    # 목표 및 실적
    target_amount = Column(Float, default=0.0, comment="목표 금액")
    actual_amount = Column(Float, default=0.0, comment="실적 금액")
    achievement_rate = Column(Float, default=0.0, comment="달성률 (%)")
    
    # # 추가 목표 지표들
    # target_visit_count = Column(Integer, default=0, comment="목표 방문 횟수")
    # actual_visit_count = Column(Integer, default=0, comment="실적 방문 횟수")
    
    # target_customer_count = Column(Integer, default=0, comment="목표 고객 수")
    # actual_customer_count = Column(Integer, default=0, comment="실적 고객 수")
    
    # 상태 및 비고
    # status = Column(String(20), default="in_progress", comment="상태 (in_progress/completed/cancelled)")
    notes = Column(String(500), comment="비고")
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일시")
    
    # 관계 정의
    branch = relationship("Branch", backref="targets")
    employee_info = relationship("EmployeeInfo", backref="branch_targets")
    
    # 유니크 제약조건: 동일 지점, 직원, 년월에 대해 중복 레코드 방지
    __table_args__ = (
        UniqueConstraint('branch_id', 'employee_info_id', 'target_year', 'target_month', 
                        name='uq_branch_employee_yearmonth'),
    )
    
    def __repr__(self):
        return f"<BranchTarget(target_id={self.target_id}, branch_id={self.branch_id}, " \
               f"employee_info_id={self.employee_info_id}, target_date={self.target_date}, " \
               f"achievement_rate={self.achievement_rate}%)>"
    
    def calculate_achievement_rate(self):
        """달성률 자동 계산"""
        if self.target_amount and self.target_amount > 0:
            self.achievement_rate = (self.actual_amount / self.target_amount) * 100
            return self.achievement_rate
        return 0.0