from . import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func

class Product(Base):
    """제품 정보를 관리하는 테이블"""
    __tablename__ = "products"
    
    # 기본 식별 정보
    product_id = Column(Integer, primary_key=True, autoincrement=True)  # 제품 고유 ID (자동 증가)
    product_name = Column(String, nullable=False)  # 제품명 (필수)
    
    # 제품 상세 정보
    description = Column(String)  # 제품 설명 및 상세 정보
    
    # 분류 정보
    category = Column(String)  # 제품 카테고리 (예: 의약품, 의료기기, 건강기능식품)
    
    # 승인 시스템 필드
    is_auto_created = Column(Boolean, default=False)  # 자동 생성 여부
    approval_status = Column(String, default='pending')  # 승인 상태 (pending, approved, rejected)
    approved_by = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)  # 승인자 ID
    approved_at = Column(DateTime, nullable=True)  # 승인 일시
    approval_notes = Column(String)  # 승인/거부 메모
    
    # 상태 정보
    is_active = Column(Boolean, default=True)  # 제품 활성화 상태 (기본값: 활성)
    
    # 시스템 정보
    created_at = Column(DateTime, default=func.now())  # 제품 등록 일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 제품 수정 일시 
