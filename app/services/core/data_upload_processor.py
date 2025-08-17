"""
데이터 업로드 처리 서비스
뉴스, 법률, 보험 인정기준, 뉴스 전략 레포트 처리
"""

import logging
import pandas as pd
import io
import json
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError

from app.models.news import News, NewsType
from app.models.laws import Law
from app.models.insurance_recognition_criteria import InsuranceRecognitionCriteria
from app.models.news_strategy_reports import NewsStrategyReport
from app.models.news_strategy_report_references import NewsStrategyReportReference
from app.services.external.s3_service import upload_file
from app.services.utils.db import AsyncSessionLocal

logger = logging.getLogger(__name__)

class DataUploadProcessor:
    """데이터 업로드 처리 클래스"""
    
    def __init__(self):
        self.session_factory = AsyncSessionLocal
    
    async def process_news_excel(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        뉴스 Excel 파일 처리
        컬럼: 제목, url, 언론사, 업로드_날짜, 타입, 요약
        """
        try:
            # Excel 파일 읽기
            df = pd.read_excel(io.BytesIO(file_bytes))
            logger.info(f"뉴스 Excel 파일 읽기 완료: {len(df)}행")
            
            # 컬럼명 확인
            required_columns = ['제목', 'url', '언론사', '업로드_날짜', '타입', '요약']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    'success_count': 0,
                    'duplicate_count': 0,
                    'error_count': len(df),
                    'errors': [f"필수 컬럼 누락: {', '.join(missing_columns)}"]
                }
            
            success_count = 0
            duplicate_count = 0
            error_count = 0
            errors = []
            
            async with self.session_factory() as session:
                for idx, row in df.iterrows():
                    try:
                        # 타입 변환
                        news_type = self._convert_news_type(row['타입'])
                        if not news_type:
                            error_count += 1
                            errors.append(f"행 {idx+2}: 잘못된 뉴스 타입 '{row['타입']}'")
                            continue
                        
                        # URL 중복 체크
                        existing = await session.execute(
                            select(News).where(News.url == row['url'])
                        )
                        if existing.scalar_one_or_none():
                            duplicate_count += 1
                            logger.debug(f"중복 URL 건너뜀: {row['url']}")
                            continue
                        
                        # 날짜 파싱
                        published_date = None
                        if pd.notna(row['업로드_날짜']):
                            try:
                                published_date = pd.to_datetime(row['업로드_날짜']).date()
                            except:
                                logger.warning(f"날짜 파싱 실패: {row['업로드_날짜']}")
                        
                        # 뉴스 생성
                        news = News(
                            title=str(row['제목']),
                            url=str(row['url']) if pd.notna(row['url']) else None,
                            source=str(row['언론사']) if pd.notna(row['언론사']) else None,
                            published_date=published_date,
                            news_type=news_type,
                            content=str(row['요약']) if pd.notna(row['요약']) else None
                        )
                        session.add(news)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"행 {idx+2}: {str(e)}")
                        if len(errors) >= 10:
                            errors.append("... 추가 에러 생략")
                            break
                
                await session.commit()
                logger.info(f"뉴스 저장 완료: 성공 {success_count}, 중복 {duplicate_count}, 실패 {error_count}")
            
            return {
                'success_count': success_count,
                'duplicate_count': duplicate_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"뉴스 Excel 처리 중 오류: {e}")
            return {
                'success_count': 0,
                'duplicate_count': 0,
                'error_count': 0,
                'errors': [f"파일 처리 실패: {str(e)}"]
            }
    
    def _convert_news_type(self, type_str: str) -> Optional[NewsType]:
        """뉴스 타입 변환"""
        if pd.isna(type_str):
            return None
        
        type_str = str(type_str).lower().strip()
        if type_str in ['common news', 'common', '일반']:
            return NewsType.GENERAL
        elif type_str in ['medical news', 'medical', '제약', 'pharmaceutical']:
            return NewsType.PHARMACEUTICAL
        else:
            return None
    
    async def process_laws_excel(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        법률 Excel 파일 처리
        컬럼: 법명, 법률정보, 조문, 내용, 소스_URL
        """
        try:
            # Excel 파일 읽기
            df = pd.read_excel(io.BytesIO(file_bytes))
            logger.info(f"법률 Excel 파일 읽기 완료: {len(df)}행")
            
            # 컬럼명 확인
            required_columns = ['법명', '법률정보', '조문', '내용', '소스_URL']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    'success_count': 0,
                    'duplicate_count': 0,
                    'error_count': len(df),
                    'errors': [f"필수 컬럼 누락: {', '.join(missing_columns)}"]
                }
            
            success_count = 0
            duplicate_count = 0
            error_count = 0
            errors = []
            
            async with self.session_factory() as session:
                for idx, row in df.iterrows():
                    try:
                        # law_number 중복 체크
                        if pd.notna(row['법률정보']):
                            existing = await session.execute(
                                select(Law).where(Law.law_number == str(row['법률정보']))
                            )
                            if existing.scalar_one_or_none():
                                duplicate_count += 1
                                logger.debug(f"중복 법률번호 건너뜀: {row['법률정보']}")
                                continue
                        
                        # 법률 생성
                        law = Law(
                            title=str(row['법명']),
                            law_number=str(row['법률정보']) if pd.notna(row['법률정보']) else None,
                            article=str(row['조문']) if pd.notna(row['조문']) else None,
                            content=str(row['내용']) if pd.notna(row['내용']) else None,
                            url=str(row['소스_URL']) if pd.notna(row['소스_URL']) else None
                        )
                        session.add(law)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"행 {idx+2}: {str(e)}")
                        if len(errors) >= 10:
                            errors.append("... 추가 에러 생략")
                            break
                
                await session.commit()
                logger.info(f"법률 저장 완료: 성공 {success_count}, 중복 {duplicate_count}, 실패 {error_count}")
            
            return {
                'success_count': success_count,
                'duplicate_count': duplicate_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"법률 Excel 처리 중 오류: {e}")
            return {
                'success_count': 0,
                'duplicate_count': 0,
                'error_count': 0,
                'errors': [f"파일 처리 실패: {str(e)}"]
            }
    
    async def process_insurance_criteria_excel(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        보험 인정기준 Excel 파일 처리
        컬럼: 고시, 제목, 업로드_날짜, url, 수집날짜
        """
        try:
            # Excel 파일 읽기
            df = pd.read_excel(io.BytesIO(file_bytes))
            logger.info(f"보험 인정기준 Excel 파일 읽기 완료: {len(df)}행")
            
            # 컬럼명 확인
            required_columns = ['고시', '제목', '업로드_날짜', 'url', '수집날짜']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    'success_count': 0,
                    'duplicate_count': 0,
                    'error_count': len(df),
                    'errors': [f"필수 컬럼 누락: {', '.join(missing_columns)}"]
                }
            
            success_count = 0
            duplicate_count = 0
            error_count = 0
            errors = []
            
            async with self.session_factory() as session:
                for idx, row in df.iterrows():
                    try:
                        # criteria_code 중복 체크
                        if pd.notna(row['고시']):
                            existing = await session.execute(
                                select(InsuranceRecognitionCriteria).where(
                                    InsuranceRecognitionCriteria.criteria_code == str(row['고시'])
                                )
                            )
                            if existing.scalar_one_or_none():
                                duplicate_count += 1
                                logger.debug(f"중복 고시번호 건너뜀: {row['고시']}")
                                continue
                        
                        # 날짜 파싱
                        effective_from = None
                        if pd.notna(row['업로드_날짜']):
                            try:
                                effective_from = pd.to_datetime(row['업로드_날짜']).date()
                            except:
                                logger.warning(f"날짜 파싱 실패: {row['업로드_날짜']}")
                        
                        # URL을 requirements JSON에 저장
                        requirements = None
                        if pd.notna(row['url']):
                            requirements = {'url': str(row['url'])}
                        
                        # 보험 인정기준 생성
                        criteria = InsuranceRecognitionCriteria(
                            criteria_code=str(row['고시']) if pd.notna(row['고시']) else None,
                            criteria_name=str(row['제목']),
                            effective_from=effective_from,
                            requirements=requirements,
                            status='active'
                        )
                        session.add(criteria)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"행 {idx+2}: {str(e)}")
                        if len(errors) >= 10:
                            errors.append("... 추가 에러 생략")
                            break
                
                await session.commit()
                logger.info(f"보험 인정기준 저장 완료: 성공 {success_count}, 중복 {duplicate_count}, 실패 {error_count}")
            
            return {
                'success_count': success_count,
                'duplicate_count': duplicate_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"보험 인정기준 Excel 처리 중 오류: {e}")
            return {
                'success_count': 0,
                'duplicate_count': 0,
                'error_count': 0,
                'errors': [f"파일 처리 실패: {str(e)}"]
            }
    
    async def process_news_strategy_report(
        self,
        file_bytes: bytes,
        filename: str,
        news_titles: List[str],
        uploader_id: int
    ) -> Dict[str, Any]:
        """
        뉴스 전략 레포트 MD 파일 처리
        1. MD 파일을 MinIO에 저장
        2. 파일명에서 제목 추출 (.md 제거)
        3. news_strategy_reports 테이블에 레코드 생성
        4. 뉴스 제목으로 검색하여 관계 생성
        """
        try:
            # 파일명에서 제목 추출 (.md 확장자 제거)
            title = filename.replace('.md', '').replace('_', ' ').replace('-', ' ')
            
            # 파일 경로 생성 (년-월 폴더 구조)
            now = datetime.now()
            folder = f"strategy-reports/{now.strftime('%Y-%m')}"
            file_id = str(uuid.uuid4())
            file_path = f"{folder}/{file_id}.md"
            
            # MinIO에 파일 업로드 (동기 함수를 별도 스레드에서 실행)
            loop = asyncio.get_event_loop()
            upload_result = await loop.run_in_executor(
                None, upload_file, file_bytes, file_path, 'text/markdown'
            )
            if not upload_result:
                return {
                    'report_id': 0,
                    'title': title,
                    'file_path': '',
                    'connected_news_count': 0,
                    'not_found_news': [],
                    'created_at': datetime.now(),
                    'errors': ["MinIO 파일 업로드 실패"]
                }
            
            logger.info(f"MD 파일 MinIO 업로드 완료: {file_path}")
            
            # 데이터베이스 작업은 업로드 완료 후 실행
            async with self.session_factory() as session:
                # 보고서 생성
                report = NewsStrategyReport(
                    title=title,
                    content=file_path,  # MinIO 파일 경로 저장
                    created_by=uploader_id
                )
                session.add(report)
                await session.flush()  # report_id 생성을 위해 flush
                
                # refresh를 통해 모든 속성을 명시적으로 로드
                await session.refresh(report)
                
                # 이제 안전하게 속성에 접근
                report_id = report.report_id
                created_at = report.created_at
                
                # 뉴스 제목으로 검색 및 관계 생성
                connected_count = 0
                not_found_news = []
                
                for news_title in news_titles:
                    # 제목으로 뉴스 검색 (부분 일치)
                    result = await session.execute(
                        select(News).where(News.title.ilike(f"%{news_title}%"))
                    )
                    news = result.scalar_one_or_none()
                    
                    if news:
                        # 관계 생성
                        reference = NewsStrategyReportReference(
                            report_id=report_id,  # 저장된 값 사용
                            news_id=news.news_id,
                            reference_type='main'
                        )
                        session.add(reference)
                        connected_count += 1
                        logger.debug(f"뉴스 연결: {news_title} -> {news.news_id}")
                    else:
                        not_found_news.append(news_title)
                        logger.warning(f"뉴스를 찾을 수 없음: {news_title}")
                
                await session.commit()
                
                logger.info(f"뉴스 전략 레포트 저장 완료: ID={report_id}, 연결된 뉴스={connected_count}")
                
                return {
                    'report_id': report_id,
                    'title': title,
                    'file_path': file_path,
                    'connected_news_count': connected_count,
                    'not_found_news': not_found_news,
                    'created_at': created_at
                }
                
        except Exception as e:
            logger.error(f"뉴스 전략 레포트 처리 중 오류: {e}", exc_info=True)
            # 변수가 정의되지 않았을 수 있으므로 안전하게 처리
            safe_title = locals().get('title', filename.replace('.md', '').replace('_', ' ').replace('-', ' '))
            return {
                'report_id': 0,
                'title': safe_title,
                'file_path': '',
                'connected_news_count': 0,
                'not_found_news': news_titles,
                'created_at': datetime.now(),
                'errors': [f"처리 실패: {str(e)}"]
            }

# 싱글톤 인스턴스
data_upload_processor = DataUploadProcessor()