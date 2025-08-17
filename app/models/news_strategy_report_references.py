from . import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship

class NewsStrategyReportReference(Base):
    """뉴스와 전략 보고서 간의 참조 관계를 관리하는 테이블"""
    __tablename__ = "news_strategy_report_references"
    
    # 기본 식별 정보
    id = Column(Integer, primary_key=True, autoincrement=True)  # 참조 고유 ID
    
    # 외래 키
    report_id = Column(Integer, ForeignKey("news_strategy_reports.report_id", ondelete="CASCADE"), nullable=False)  # 보고서 ID
    news_id = Column(Integer, ForeignKey("news.news_id", ondelete="CASCADE"), nullable=False)  # 뉴스 ID
    
    # 참조 정보
    reference_type = Column(String(50))  # 참조 유형 (main_source, supporting, related 등)
    notes = Column(Text)  # 참조 관련 메모
    
    # 시스템 정보
    created_at = Column(DateTime(timezone=True), default=func.now())  # 생성 일시
    
    # 제약 조건
    __table_args__ = (
        UniqueConstraint('report_id', 'news_id', name='uq_report_news'),  # 보고서-뉴스 조합 유니크 제약
    )
    
    # 관계 설정
    report = relationship("NewsStrategyReport", back_populates="news_references")
    news = relationship("News", backref="strategy_report_references")