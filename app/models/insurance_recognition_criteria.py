from . import Base
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

class InsuranceRecognitionCriteria(Base):
    """보험 인정기준을 관리하는 테이블"""
    __tablename__ = "insurance_recognition_criteria"
    
    # 기본 식별 정보
    criteria_id = Column(Integer, primary_key=True, autoincrement=True)  # 인정기준 고유 ID
    
    # 제품 연결
    product_id = Column(Integer, ForeignKey("products.product_id"))  # 관련 제품 ID
    
    # 인정기준 정보
    criteria_code = Column(String(50))  # 인정기준 코드 (고시번호)
    criteria_name = Column(String(200), nullable=False)  # 인정기준명
    description = Column(Text)  # 상세 설명
    
    # 요구사항 및 조건
    requirements = Column(JSONB)  # 인정 요구사항 (JSON 형태)
    
    # 보장 정보
    coverage_amount = Column(Numeric(15, 2))  # 보장 금액
    
    # 유효 기간
    effective_from = Column(Date)  # 시작일
    effective_to = Column(Date)  # 종료일
    
    # 상태
    status = Column(String(50), default='active')  # 상태 (active, inactive, expired)
    
    # 시스템 정보
    created_at = Column(DateTime(timezone=True), default=func.now())  # 생성 일시
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 수정 일시
    
    # 관계 설정
    product = relationship("Product", backref="insurance_criteria")
    
    # 복합 유니크 제약조건: criteria_code + criteria_name 조합이 유니크해야 함
    __table_args__ = (
        UniqueConstraint('criteria_code', 'criteria_name', name='uq_criteria_code_name'),
    )