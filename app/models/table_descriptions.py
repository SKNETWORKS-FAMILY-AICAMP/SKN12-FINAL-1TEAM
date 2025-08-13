from . import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import VECTOR

class TableDescription(Base):
    """테이블 설명 벡터 저장 모델"""
    __tablename__ = "table_descriptions"
    
    # 기본 식별 정보
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String, nullable=False, unique=True)  # 테이블명 (고유값)
    
    # 설명 정보
    description = Column(Text, nullable=False)  # 테이블 설명
    columns = Column(JSONB, nullable=True)  # 컬럼 정보 (JSON)
    sample_data = Column(JSONB, nullable=True)  # 샘플 데이터 (JSON)
    
    # 벡터 정보
    embedding = Column(VECTOR(1536), nullable=False)  # OpenAI 임베딩 벡터 (1536차원)
    
    # 시스템 정보
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<TableDescription(table_name='{self.table_name}', description='{self.description[:50]}...')>" 