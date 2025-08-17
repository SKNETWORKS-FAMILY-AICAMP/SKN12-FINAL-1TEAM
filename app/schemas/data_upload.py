"""
데이터 업로드 관련 스키마 정의
뉴스, 법률, 보험 인정기준, 뉴스 전략 레포트
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NewsUploadResult(BaseModel):
    """뉴스 Excel 업로드 결과"""
    success_count: int
    duplicate_count: int
    error_count: int
    errors: List[str] = []
    
class LawUploadResult(BaseModel):
    """법률 Excel 업로드 결과"""
    success_count: int
    duplicate_count: int
    error_count: int
    errors: List[str] = []
    
class InsuranceCriteriaUploadResult(BaseModel):
    """보험 인정기준 Excel 업로드 결과"""
    success_count: int
    duplicate_count: int
    error_count: int
    errors: List[str] = []
    
class NewsStrategyReportUploadResult(BaseModel):
    """뉴스 전략 레포트 업로드 결과"""
    report_id: int
    title: str
    file_path: str
    connected_news_count: int
    not_found_news: List[str] = []
    created_at: datetime