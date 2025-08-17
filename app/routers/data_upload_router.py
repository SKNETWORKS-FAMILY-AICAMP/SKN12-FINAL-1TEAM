"""
데이터 업로드 라우터
뉴스, 법률, 보험 인정기준, 뉴스 전략 레포트 업로드 엔드포인트
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
import json
import logging

from app.schemas.data_upload import (
    NewsUploadResult,
    LawUploadResult,
    InsuranceCriteriaUploadResult,
    NewsStrategyReportUploadResult
)
from app.services.core.data_upload_processor import data_upload_processor
from app.routers.user_router import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# 파일 크기 제한 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

@router.post("/upload/news", response_model=NewsUploadResult)
async def upload_news(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    뉴스 Excel 파일 업로드
    
    필수 컬럼:
    - 제목: 뉴스 제목
    - url: 뉴스 URL
    - 언론사: 뉴스 출처
    - 업로드_날짜: 게시 날짜
    - 타입: 뉴스 타입 (common news / medical news)
    - 요약: 뉴스 요약 내용
    """
    try:
        # 파일 확장자 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Excel 파일(.xlsx, .xls)만 업로드 가능합니다."
            )
        
        # 파일 크기 검증
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 가능합니다."
            )
        
        logger.info(f"뉴스 Excel 업로드 시작: {file.filename} (사용자: {current_user.email})")
        
        # 처리
        result = await data_upload_processor.process_news_excel(
            file_content,
            file.filename
        )
        
        return NewsUploadResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스 업로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/upload/laws", response_model=LawUploadResult)
async def upload_laws(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    법률 Excel 파일 업로드
    
    필수 컬럼:
    - 법명: 법률 제목
    - 법률정보: 법률 번호
    - 조문: 조문 정보
    - 내용: 법률 내용
    - 소스_URL: 출처 URL
    """
    try:
        # 파일 확장자 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Excel 파일(.xlsx, .xls)만 업로드 가능합니다."
            )
        
        # 파일 크기 검증
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 가능합니다."
            )
        
        logger.info(f"법률 Excel 업로드 시작: {file.filename} (사용자: {current_user.email})")
        
        # 처리
        result = await data_upload_processor.process_laws_excel(
            file_content,
            file.filename
        )
        
        return LawUploadResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"법률 업로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/upload/insurance-criteria", response_model=InsuranceCriteriaUploadResult)
async def upload_insurance_criteria(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    보험 인정기준 Excel 파일 업로드
    
    필수 컬럼:
    - 고시: 고시 번호
    - 제목: 인정기준 제목
    - 업로드_날짜: 업로드 날짜
    - url: 관련 URL
    - 수집날짜: 수집 날짜
    """
    try:
        # 파일 확장자 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Excel 파일(.xlsx, .xls)만 업로드 가능합니다."
            )
        
        # 파일 크기 검증
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 가능합니다."
            )
        
        logger.info(f"보험 인정기준 Excel 업로드 시작: {file.filename} (사용자: {current_user.email})")
        
        # 처리
        result = await data_upload_processor.process_insurance_criteria_excel(
            file_content,
            file.filename
        )
        
        return InsuranceCriteriaUploadResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보험 인정기준 업로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/upload/news-strategy-report", response_model=NewsStrategyReportUploadResult)
async def upload_news_strategy_report(
    file: UploadFile = File(...),
    news_titles: str = Form(...),  # JSON 문자열로 전달
    current_user = Depends(get_current_user)
):
    """
    뉴스 전략 레포트 MD 파일 업로드
    
    Parameters:
    - file: MD 파일
    - news_titles: 관련 뉴스 제목 리스트 (JSON 문자열)
    
    Example news_titles:
    ["뉴스 제목 1", "뉴스 제목 2", "뉴스 제목 3"]
    """
    try:
        # 파일 확장자 검증
        if not file.filename.endswith('.md'):
            raise HTTPException(
                status_code=400,
                detail="Markdown 파일(.md)만 업로드 가능합니다."
            )
        
        # 파일 크기 검증
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 가능합니다."
            )
        
        # news_titles JSON 파싱
        try:
            news_title_list = json.loads(news_titles)
            if not isinstance(news_title_list, list):
                raise ValueError("news_titles는 배열이어야 합니다.")
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="news_titles가 올바른 JSON 형식이 아닙니다."
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        logger.info(f"뉴스 전략 레포트 업로드 시작: {file.filename} (사용자: {current_user.email})")
        logger.info(f"  - 관련 뉴스 개수: {len(news_title_list)}")
        
        # 처리
        result = await data_upload_processor.process_news_strategy_report(
            file_content,
            file.filename,
            news_titles=news_title_list,
            uploader_id=current_user.employee_id
        )
        
        # 에러 체크
        if 'errors' in result:
            raise HTTPException(
                status_code=500,
                detail=result['errors'][0] if result['errors'] else "처리 중 오류가 발생했습니다."
            )
        
        return NewsStrategyReportUploadResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"뉴스 전략 레포트 업로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")

@router.get("/upload/template/{data_type}")
async def get_upload_template(
    data_type: str,
    current_user = Depends(get_current_user)
):
    """
    업로드용 Excel 템플릿 다운로드 링크 제공
    
    Parameters:
    - data_type: news, laws, insurance-criteria 중 하나
    """
    templates = {
        "news": {
            "columns": ["제목", "url", "언론사", "업로드_날짜", "타입", "요약"],
            "sample": {
                "제목": "신약 개발 소식",
                "url": "https://example.com/news/1",
                "언론사": "의학신문",
                "업로드_날짜": "2024-01-15",
                "타입": "medical news",
                "요약": "새로운 항암제 개발 성공..."
            }
        },
        "laws": {
            "columns": ["법명", "법률정보", "조문", "내용", "소스_URL"],
            "sample": {
                "법명": "약사법",
                "법률정보": "제2024-001호",
                "조문": "제31조",
                "내용": "의약품 제조업 허가...",
                "소스_URL": "https://law.go.kr/..."
            }
        },
        "insurance-criteria": {
            "columns": ["고시", "제목", "업로드_날짜", "url", "수집날짜"],
            "sample": {
                "고시": "제2024-001호",
                "제목": "항암제 급여기준",
                "업로드_날짜": "2024-01-15",
                "url": "https://hira.or.kr/...",
                "수집날짜": "2024-01-16"
            }
        }
    }
    
    if data_type not in templates:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 데이터 타입입니다. 가능한 값: {', '.join(templates.keys())}"
        )
    
    return templates[data_type]