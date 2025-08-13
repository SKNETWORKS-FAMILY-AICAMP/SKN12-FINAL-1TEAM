"""
지점 정보 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from . import Base

class Branch(Base):
    """지점 정보 테이블"""
    __tablename__ = "branches"
    
    # 기본 필드
    branch_id = Column(Integer, primary_key=True, index=True, comment="지점 ID")
    
    # 조직 구조
    headquarters = Column(String(100), nullable=False, comment="본부")
    department = Column(String(100), nullable=False, comment="부서")
    branch_name = Column(String(100), nullable=False, unique=True, comment="지점명")
    
    # 연락처 정보
    contact_number = Column(String(20), comment="연락처")
    
    # 추가 정보
    status = Column(String(20), default="active", comment="상태 (active/inactive)")
    notes = Column(String(500), comment="비고")
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일시")
    
    def __repr__(self):
        return f"<Branch(branch_id={self.branch_id}, branch_name={self.branch_name}, headquarters={self.headquarters})>"