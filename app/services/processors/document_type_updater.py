"""
문서 타입 업데이트를 위한 헬퍼 함수들
"""
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.documents import Document
import logging

logger = logging.getLogger(__name__)

class DocumentTypeUpdater:
    """문서 타입 업데이트를 위한 헬퍼 클래스"""
    
    @staticmethod
    async def update_after_success(doc: Document, result: Dict[str, Any], session: Session) -> None:
        """
        Text2SQL 분류 성공 시 문서 타입 업데이트
        
        Args:
            doc: 업데이트할 문서 객체
            result: Text2SQL 분류 결과
            session: 데이터베이스 세션
        """
        try:
            # 문서 타입을 'table_data'로 업데이트
            doc.doc_type = f"text2sql_{result.get('target_table', 'unknown')}"
            doc.processing_status = 'processed'
            doc.processed_at = datetime.now()
            
            # 처리 결과 메타데이터 저장
            doc.processing_metadata = {
                'target_table': result.get('target_table'),
                'confidence': result.get('confidence', 0.0),
                'column_mapping': result.get('column_mapping', {}),
                'reasoning': result.get('reasoning', ''),
                'method': 'text2sql',
                'processed_at': datetime.now().isoformat()
            }
            
            session.flush()
            logger.info(f"문서 타입 업데이트 성공: {doc.doc_id} -> {doc.doc_type}")
            
        except Exception as e:
            logger.error(f"문서 타입 업데이트 실패: {e}")
            session.rollback()
            raise
    
    @staticmethod
    async def update_after_failure(doc: Document, result: Dict[str, Any], session: Session) -> None:
        """
        Text2SQL 분류 실패 시 문서 타입 업데이트
        
        Args:
            doc: 업데이트할 문서 객체
            result: Text2SQL 분류 결과
            session: 데이터베이스 세션
        """
        try:
            doc.processing_status = 'failed'
            doc.processed_at = datetime.now()
            
            # 실패 정보 메타데이터 저장
            doc.processing_metadata = {
                'error': result.get('message', 'Unknown error'),
                'method': 'text2sql',
                'failed_at': datetime.now().isoformat()
            }
            
            session.flush()
            logger.warning(f"문서 처리 실패 상태 업데이트: {doc.doc_id}")
            
        except Exception as e:
            logger.error(f"실패 상태 업데이트 실패: {e}")
            session.rollback()
            raise
    
    @staticmethod
    async def update_partial_success(doc: Document, result: Dict[str, Any], session: Session) -> None:
        """
        부분 성공 시 문서 타입 업데이트
        
        Args:
            doc: 업데이트할 문서 객체
            result: Text2SQL 분류 결과
            session: 데이터베이스 세션
        """
        try:
            doc.doc_type = 'table_data_partial'
            doc.processing_status = 'partially_processed'
            doc.processed_at = datetime.now()
            
            # 부분 성공 정보 메타데이터 저장
            doc.processing_metadata = {
                'successful_tables': result.get('successful_tables', []),
                'failed_tables': result.get('failed_tables', []),
                'method': 'text2sql',
                'processed_at': datetime.now().isoformat()
            }
            
            session.flush()
            logger.info(f"문서 부분 성공 상태 업데이트: {doc.doc_id}")
            
        except Exception as e:
            logger.error(f"부분 성공 상태 업데이트 실패: {e}")
            session.rollback()
            raise
    
    @staticmethod
    async def update_processing_status(doc: Document, status: str, session: Session) -> None:
        """
        문서 처리 상태 업데이트
        
        Args:
            doc: 업데이트할 문서 객체
            status: 새로운 처리 상태
            session: 데이터베이스 세션
        """
        try:
            doc.processing_status = status
            if status in ['processed', 'failed', 'partially_processed']:
                doc.processed_at = datetime.now()
            
            session.flush()
            logger.info(f"문서 처리 상태 업데이트: {doc.doc_id} -> {status}")
            
        except Exception as e:
            logger.error(f"처리 상태 업데이트 실패: {e}")
            session.rollback()
            raise 