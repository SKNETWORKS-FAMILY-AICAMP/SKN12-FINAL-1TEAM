from . import Base
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

class Law(Base):
    """법령 정보를 관리하는 테이블"""
    __tablename__ = "laws"
    
    # 기본 식별 정보
    law_id = Column(Integer, primary_key=True, autoincrement=True)  # 법령 고유 ID
    title = Column(String(1000), nullable=False)  # 법령 제목
    law_number = Column(String(100))  # 법령 번호
    
    # 법령 내용
    content = Column(Text)  # 법령 전문
    article = Column(String(100))  # 조문 (예: 제31조, 제5조 제2항)
    
    # URL 정보
    url = Column(String(1000))  # 출처 URL
    
    # 시스템 정보
    created_at = Column(DateTime(timezone=True), default=func.now())  # 생성 일시
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 수정 일시
    
    # 복합 유니크 제약조건: law_number + article 조합이 유니크해야 함
    __table_args__ = (
        UniqueConstraint('law_number', 'article', name='uq_law_number_article'),
    )