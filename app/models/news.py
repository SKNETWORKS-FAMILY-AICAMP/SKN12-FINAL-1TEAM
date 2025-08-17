from . import Base
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import JSONB
import enum

class NewsType(enum.Enum):
    """뉴스 타입 열거형"""
    GENERAL = "general"  # 일반 뉴스
    PHARMACEUTICAL = "pharmaceutical"  # 제약 뉴스

class News(Base):
    """뉴스 정보를 관리하는 테이블"""
    __tablename__ = "news"
    
    # 기본 식별 정보
    news_id = Column(Integer, primary_key=True, autoincrement=True)  # 뉴스 고유 ID
    title = Column(String(1000), nullable=False)  # 뉴스 제목
    content = Column(Text)  # 뉴스 내용
    
    # 뉴스 분류
    news_type = Column(Enum(NewsType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)  # 뉴스 타입 (일반/제약)
    
    # 출처 정보
    source = Column(String(200))  # 뉴스 출처
    author = Column(String(100))  # 기사 작성자
    published_date = Column(Date)  # 게시 날짜
    url = Column(String(1500), unique=True)  # 원문 URL
    
    # 메타데이터
    tags = Column(JSONB)  # 태그 정보 (JSON 형태)
    
    # 시스템 정보
    created_at = Column(DateTime(timezone=True), default=func.now())  # 생성 일시
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 수정 일시