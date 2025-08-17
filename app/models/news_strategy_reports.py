from . import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

class NewsStrategyReport(Base):
    """뉴스 전략 보고서를 관리하는 테이블"""
    __tablename__ = "news_strategy_reports"
    
    # 기본 식별 정보
    report_id = Column(Integer, primary_key=True, autoincrement=True)  # 보고서 고유 ID
    title = Column(String(500), nullable=False)  # 보고서 제목
    
    # MinIO 파일 경로 저장
    content = Column(Text)  # MinIO 파일 경로
    
    # 작성자 정보
    created_by = Column(Integer, ForeignKey("employees.employee_id"))  # 작성자 ID
    
    # 시스템 정보
    created_at = Column(DateTime(timezone=True), default=func.now())  # 생성 일시
    
    # 관계 설정
    creator = relationship("Employee", backref="strategy_reports")
    news_references = relationship("NewsStrategyReportReference", back_populates="report", cascade="all, delete-orphan")