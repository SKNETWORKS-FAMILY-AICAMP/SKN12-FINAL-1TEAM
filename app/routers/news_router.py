"""
뉴스 데이터 조회 관련 라우터
일반 뉴스, 제약 뉴스 및 관련 전략 레포트 조회 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date, datetime
from pydantic import BaseModel

from app.services.utils.db import get_db
from app.routers.user_router import get_current_user
from app.models.news import News, NewsType
from app.models.news_strategy_reports import NewsStrategyReport
from app.models.news_strategy_report_references import NewsStrategyReportReference
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class NewsResponse(BaseModel):
    """뉴스 응답 스키마"""
    news_id: int
    title: str
    content: Optional[str] = None
    news_type: str
    source: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[date] = None
    url: Optional[str] = None
    tags: Optional[Dict] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class StrategyReportResponse(BaseModel):
    """전략 레포트 응답 스키마"""
    report_id: int
    title: str
    content: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    reference_type: Optional[str] = None
    reference_notes: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/general/{target_date}", response_model=List[NewsResponse])
def get_general_news_by_date(
    target_date: date = Path(..., description="조회할 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[NewsResponse]:
    """
    특정 날짜의 일반 뉴스 조회
    
    Args:
        target_date: 조회할 날짜 (YYYY-MM-DD 형식)
        
    Returns:
        해당 날짜의 일반 뉴스 목록
    """
    try:
        news_list = db.query(News).filter(
            and_(
                News.published_date == target_date,
                News.news_type == NewsType.GENERAL
            )
        ).order_by(News.created_at.desc()).all()
        
        if not news_list:
            logger.info(f"No general news found for date: {target_date}")
            return []
        
        return [NewsResponse.model_validate(news) for news in news_list]
    
    except Exception as e:
        logger.error(f"Error fetching general news for date {target_date}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/pharmaceutical/{target_date}", response_model=List[NewsResponse])
def get_pharmaceutical_news_by_date(
    target_date: date = Path(..., description="조회할 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[NewsResponse]:
    """
    특정 날짜의 제약 뉴스 조회
    
    Args:
        target_date: 조회할 날짜 (YYYY-MM-DD 형식)
        
    Returns:
        해당 날짜의 제약 뉴스 목록
    """
    try:
        news_list = db.query(News).filter(
            and_(
                News.published_date == target_date,
                News.news_type == NewsType.PHARMACEUTICAL
            )
        ).order_by(News.created_at.desc()).all()
        
        if not news_list:
            logger.info(f"No pharmaceutical news found for date: {target_date}")
            return []
        
        return [NewsResponse.model_validate(news) for news in news_list]
    
    except Exception as e:
        logger.error(f"Error fetching pharmaceutical news for date {target_date}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/{news_id}/strategy-reports", response_model=List[StrategyReportResponse])
def get_strategy_reports_by_news(
    news_id: int = Path(..., description="뉴스 ID"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[StrategyReportResponse]:
    """
    특정 뉴스와 관련된 전략 레포트 조회
    
    Args:
        news_id: 뉴스 ID
        
    Returns:
        해당 뉴스와 관련된 전략 레포트 목록
    """
    try:
        # 먼저 뉴스가 존재하는지 확인
        news = db.query(News).filter(News.news_id == news_id).first()
        if not news:
            raise HTTPException(status_code=404, detail=f"뉴스 ID {news_id}를 찾을 수 없습니다")
        
        # 관련 전략 레포트 조회
        reports = db.query(
            NewsStrategyReport,
            NewsStrategyReportReference.reference_type,
            NewsStrategyReportReference.notes
        ).join(
            NewsStrategyReportReference,
            NewsStrategyReport.report_id == NewsStrategyReportReference.report_id
        ).filter(
            NewsStrategyReportReference.news_id == news_id
        ).order_by(NewsStrategyReport.created_at.desc()).all()
        
        if not reports:
            logger.info(f"No strategy reports found for news ID: {news_id}")
            return []
        
        # 응답 데이터 구성
        result = []
        for report, ref_type, ref_notes in reports:
            report_data = StrategyReportResponse(
                report_id=report.report_id,
                title=report.title,
                content=report.content,
                created_by=report.created_by,
                created_at=report.created_at,
                reference_type=ref_type,
                reference_notes=ref_notes
            )
            result.append(report_data)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching strategy reports for news ID {news_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"전략 레포트 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/search", response_model=List[NewsResponse])
def search_news(
    keyword: Optional[str] = Query(None, description="검색 키워드"),
    news_type: Optional[str] = Query(None, description="뉴스 타입 (general/pharmaceutical)"),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    limit: int = Query(100, description="최대 결과 수"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[NewsResponse]:
    """
    뉴스 검색 (선택적 필터링)
    
    Args:
        keyword: 제목 또는 내용에서 검색할 키워드
        news_type: 뉴스 타입 필터 (general 또는 pharmaceutical)
        start_date: 검색 시작 날짜
        end_date: 검색 종료 날짜
        limit: 최대 결과 수
        
    Returns:
        검색 조건에 맞는 뉴스 목록
    """
    try:
        query = db.query(News)
        
        # 키워드 검색
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    News.title.ilike(search_pattern),
                    News.content.ilike(search_pattern)
                )
            )
        
        # 뉴스 타입 필터
        if news_type:
            if news_type.lower() == "general":
                query = query.filter(News.news_type == NewsType.GENERAL)
            elif news_type.lower() == "pharmaceutical":
                query = query.filter(News.news_type == NewsType.PHARMACEUTICAL)
        
        # 날짜 범위 필터
        if start_date:
            query = query.filter(News.published_date >= start_date)
        if end_date:
            query = query.filter(News.published_date <= end_date)
        
        # 정렬 및 제한
        news_list = query.order_by(News.published_date.desc()).limit(limit).all()
        
        return [NewsResponse.model_validate(news) for news in news_list]
    
    except Exception as e:
        logger.error(f"Error searching news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 검색 중 오류가 발생했습니다: {str(e)}")