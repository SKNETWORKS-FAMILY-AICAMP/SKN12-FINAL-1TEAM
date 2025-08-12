from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func

class CustomerMonthlyPatient(Base):
    """거래처별 월간 환자수를 관리하는 테이블"""
    __tablename__ = "customer_monthly_patients"
    
    # 기본 식별 정보
    patient_record_id = Column(Integer, primary_key=True, autoincrement=True)  # 환자수 기록 고유 ID (자동 증가)
    
    # 관계 정보
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)  # 거래처 ID (외래키, 필수)
    
    # 월별 데이터
    year_month = Column(String, nullable=False)  # 년월 (YYYY-MM 형식, 필수)
    patient_count = Column(Integer, nullable=False, default=0)  # 월간 환자수 (필수)
    
    # 시스템 정보
    created_at = Column(DateTime, default=func.now())  # 생성 일시 (자동 설정)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 수정 일시 (자동 업데이트)
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('customer_id', 'year_month', name='uq_customer_month'),  # 거래처+년월 조합 유니크 제약
    )