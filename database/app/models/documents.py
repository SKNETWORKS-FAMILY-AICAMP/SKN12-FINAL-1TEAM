from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

class Document(Base):
    """문서 정보를 관리하는 테이블"""
    __tablename__ = "documents"
    
    # 기본 식별 정보
    doc_id = Column(Integer, primary_key=True, autoincrement=True)  # 문서 고유 ID (자동 증가)
    
    # 업로드 정보 (역사적 기록이므로 NULL 불가)
    uploader_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)  # 문서 업로드한 직원 ID (외래키, 필수)
    
    # 문서 정보
    doc_title = Column(String, nullable=False)  # 문서 제목 (필수)
    doc_type = Column(String)  # 문서 유형 (예: 규정, 매뉴얼, 보고서, 계약서)
    file_path = Column(String, nullable=False)  # 파일 저장 경로 (필수)
    version = Column(String)  # 문서 버전 (예: 1.0, 2.1)
    
    # 처리 상태 정보
    processing_status = Column(String, default='pending')  # 처리 상태 (pending, processing, processed, failed)
    processed_at = Column(DateTime)  # 처리 완료 시간
    processing_metadata = Column(JSONB)  # 처리 결과 메타데이터 (JSON)
    
    # 시스템 정보
    created_at = Column(DateTime, default=func.now())  # 문서 업로드 일시 (자동 설정)
    
 
