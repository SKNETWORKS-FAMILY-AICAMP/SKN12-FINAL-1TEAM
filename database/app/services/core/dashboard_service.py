"""
대시보드 서비스
문서 업로드로 인한 자동 생성 데이터 모니터링 및 통계 제공
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.system_trace_logs import SystemTraceLog
from app.models.documents import Document
from app.models.employees import Employee
from app.models.employee_info import EmployeeInfo
from app.models.customers import Customer
from app.models.products import Product
from app.models.sales_records import SalesRecord

logger = logging.getLogger(__name__)

class DashboardService:
    """대시보드 서비스"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_dashboard_stats(self, days: int = 30) -> Dict[str, Any]:
        """대시보드 통계 조회"""
        try:
            # 기간 설정
            start_date = datetime.now() - timedelta(days=days)
            
            # 전체 문서 수
            total_documents = self.db.query(Document).filter(
                Document.created_at >= start_date
            ).count()
            
            # 자동 생성된 데이터 통계 (log_data에서 추출)
            auto_created_stats = self.db.query(SystemTraceLog).filter(
                and_(
                    SystemTraceLog.created_at >= start_date,
                    SystemTraceLog.event_type == 'auto_create'
                )
            ).all()
            
            auto_created_by_type = {}
            total_auto_created = 0
            
            for log in auto_created_stats:
                log_data = log.log_data or {}
                entity_type = log_data.get('entity_type', 'unknown')
                action = log_data.get('action', 'unknown')
                
                if action == 'created':
                    auto_created_by_type[entity_type] = auto_created_by_type.get(entity_type, 0) + 1
                    total_auto_created += 1
            
            # 최근 업로드 현황
            recent_uploads = self._get_recent_uploads(days)
            
            # 성공률 계산
            upload_success_rate = self._calculate_upload_success_rate(days)
            auto_create_success_rate = self._calculate_auto_create_success_rate(days)
            
            return {
                'total_documents': total_documents,
                'total_auto_created': total_auto_created,
                'auto_created_by_type': auto_created_by_type,
                'recent_uploads': recent_uploads,
                'upload_success_rate': upload_success_rate,
                'auto_create_success_rate': auto_create_success_rate
            }
            
        except Exception as e:
            logger.error(f"대시보드 통계 조회 중 오류: {e}")
            return {
                'total_documents': 0,
                'total_auto_created': 0,
                'auto_created_by_type': {},
                'recent_uploads': [],
                'upload_success_rate': 0.0,
                'auto_create_success_rate': 0.0
            }
    
    def get_auto_create_summary(self, entity_type: str, days: int = 30) -> Dict[str, Any]:
        """특정 엔티티 타입의 자동 생성 요약"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 해당 엔티티 타입의 로그 조회
            logs = self.db.query(SystemTraceLog).filter(
                and_(
                    SystemTraceLog.event_type == 'auto_create',
                    SystemTraceLog.created_at >= start_date
                )
            ).order_by(desc(SystemTraceLog.created_at)).all()
            
            # 통계 계산
            total_created = 0
            total_skipped = 0
            total_failed = 0
            
            recent_activities = []
            
            for log in logs:
                log_data = log.log_data or {}
                log_entity_type = log_data.get('entity_type', '')
                action = log_data.get('action', '')
                
                if log_entity_type == entity_type:
                    if action == 'created':
                        total_created += 1
                    elif action == 'skipped':
                        total_skipped += 1
                    elif action == 'failed':
                        total_failed += 1
                    
                    # 최근 활동 (최대 10개)
                    if len(recent_activities) < 10:
                        recent_activities.append({
                            'trace_id': log.trace_id,
                            'action': action,
                            'entity_id': log_data.get('entity_id'),
                            'document_id': log_data.get('document_id'),
                            'message': log_data.get('message', ''),
                            'created_at': log.created_at.isoformat(),
                            'details': log_data.get('details', {})
                        })
            
            total_actions = total_created + total_skipped + total_failed
            success_rate = (total_created / total_actions * 100) if total_actions > 0 else 0.0
            
            return {
                'entity_type': entity_type,
                'total_created': total_created,
                'total_skipped': total_skipped,
                'total_failed': total_failed,
                'success_rate': success_rate,
                'recent_activities': recent_activities
            }
            
        except Exception as e:
            logger.error(f"자동 생성 요약 조회 중 오류: {e}")
            return {
                'entity_type': entity_type,
                'total_created': 0,
                'total_skipped': 0,
                'total_failed': 0,
                'success_rate': 0.0,
                'recent_activities': []
            }
    
    def get_document_upload_summary(self, document_id: int) -> Optional[Dict[str, Any]]:
        """특정 문서의 업로드 요약"""
        try:
            # 문서 정보 조회
            document = self.db.query(Document).filter(Document.doc_id == document_id).first()
            if not document:
                return None
            
            # 해당 문서의 자동 생성 로그 조회
            logs = self.db.query(SystemTraceLog).filter(
                and_(
                    SystemTraceLog.event_type == 'auto_create'
                )
            ).all()
            
            auto_created_count = 0
            skipped_count = 0
            
            for log in logs:
                log_data = log.log_data or {}
                log_document_id = log_data.get('document_id')
                action = log_data.get('action', '')
                
                if log_document_id == document_id:
                    if action == 'created':
                        auto_created_count += 1
                    elif action == 'skipped':
                        skipped_count += 1
            
            # Text2SQL 분류 결과에서 신뢰도 추출
            confidence_score = 0.0
            target_table = ""
            
            # 문서 타입에서 정보 추출
            if document.doc_type and document.doc_type.startswith('text2sql_'):
                target_table = document.doc_type.replace('text2sql_', '')
                confidence_score = 0.95  # 기본값, 실제로는 저장된 분석 결과에서 추출해야 함
            
            return {
                'document_id': document.doc_id,
                'document_title': document.doc_title,
                'uploader_id': document.uploader_id,
                'upload_date': document.created_at,
                'auto_created_count': auto_created_count,
                'skipped_count': skipped_count,
                'target_table': target_table,
                'confidence_score': confidence_score
            }
            
        except Exception as e:
            logger.error(f"문서 업로드 요약 조회 중 오류: {e}")
            return None
    
    def _get_recent_uploads(self, days: int) -> List[Dict[str, Any]]:
        """최근 업로드 현황 조회"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 최근 문서 업로드 조회
            recent_docs = self.db.query(Document).filter(
                Document.created_at >= start_date
            ).order_by(desc(Document.created_at)).limit(10).all()
            
            recent_uploads = []
            for doc in recent_docs:
                # 각 문서의 자동 생성 통계
                logs = self.db.query(SystemTraceLog).filter(
                    SystemTraceLog.event_type == 'auto_create'
                ).all()
                
                auto_created_count = 0
                for log in logs:
                    log_data = log.log_data or {}
                    log_document_id = log_data.get('document_id')
                    action = log_data.get('action', '')
                    
                    if log_document_id == doc.doc_id and action == 'created':
                        auto_created_count += 1
                
                recent_uploads.append({
                    'document_id': doc.doc_id,
                    'title': doc.doc_title,
                    'type': doc.doc_type,
                    'upload_date': doc.created_at.isoformat(),
                    'auto_created_count': auto_created_count
                })
            
            return recent_uploads
            
        except Exception as e:
            logger.error(f"최근 업로드 조회 중 오류: {e}")
            return []
    
    def _calculate_upload_success_rate(self, days: int) -> float:
        """업로드 성공률 계산"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 전체 업로드 시도
            total_uploads = self.db.query(SystemTraceLog).filter(
                and_(
                    SystemTraceLog.event_type == 'document_upload',
                    SystemTraceLog.created_at >= start_date
                )
            ).count()
            
            # 성공한 업로드
            successful_uploads = self.db.query(SystemTraceLog).filter(
                and_(
                    SystemTraceLog.event_type == 'document_upload',
                    SystemTraceLog.created_at >= start_date
                )
            ).all()
            
            success_count = 0
            for log in successful_uploads:
                log_data = log.log_data or {}
                if log_data.get('status') == 'success':
                    success_count += 1
            
            return (success_count / total_uploads * 100) if total_uploads > 0 else 0.0
            
        except Exception as e:
            logger.error(f"업로드 성공률 계산 중 오류: {e}")
            return 0.0
    
    def _calculate_auto_create_success_rate(self, days: int) -> float:
        """자동 생성 성공률 계산"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 자동 생성 시도
            logs = self.db.query(SystemTraceLog).filter(
                and_(
                    SystemTraceLog.event_type == 'auto_create',
                    SystemTraceLog.created_at >= start_date
                )
            ).all()
            
            total_attempts = len(logs)
            successful_creations = 0
            
            for log in logs:
                log_data = log.log_data or {}
                if log_data.get('action') == 'created':
                    successful_creations += 1
            
            return (successful_creations / total_attempts * 100) if total_attempts > 0 else 0.0
            
        except Exception as e:
            logger.error(f"자동 생성 성공률 계산 중 오류: {e}")
            return 0.0
    
    def log_auto_create_activity(self, entity_type: str, action: str, 
                                entity_id: Optional[int] = None, document_id: Optional[int] = None,
                                uploader_id: Optional[int] = None, details: Optional[Dict] = None,
                                message: Optional[str] = None):
        """자동 생성 활동 로깅"""
        try:
            log_data = {
                'entity_type': entity_type,
                'action': action,
                'entity_id': entity_id,
                'document_id': document_id,
                'uploader_id': uploader_id,
                'details': details or {},
                'message': message or f"{entity_type} {action}"
            }
            
            log = SystemTraceLog(
                message_id=None,  # 시스템 활동이므로 chat_history와 무관
                event_type='auto_create',
                log_data=log_data,
                latency_ms=0
            )
            
            self.db.add(log)
            self.db.commit()
            
            logger.info(f"자동 생성 로그 기록: {entity_type} {action} (ID: {entity_id})")
            
        except Exception as e:
            logger.error(f"자동 생성 로그 기록 중 오류: {e}")
            self.db.rollback()
    
    def get_system_documents(self, system_type: str) -> Dict[str, Any]:
        """시스템별 문서 정보 조회"""
        try:
            logger.info(f"시스템 문서 조회 시작: {system_type}")
            
            if system_type == "postgresql":
                # PostgreSQL의 documents 테이블 조회
                documents = self.db.query(Document).all()
                logger.info(f"PostgreSQL에서 {len(documents)}개의 문서를 찾았습니다.")
                
                result = {
                    "documents": [
                        {
                            "doc_id": doc.doc_id,
                            "title": doc.doc_title,
                            "file_type": doc.doc_type,
                            "file_path": doc.file_path,
                            "upload_date": doc.created_at.isoformat() if doc.created_at else None,
                            "uploader_id": doc.uploader_id,
                            "version": doc.version
                        }
                        for doc in documents
                    ]
                }
                logger.info(f"PostgreSQL 문서 조회 완료: {len(result['documents'])}개")
                return result
            
            elif system_type == "minio":
                # MinIO 파일 목록 조회 (실제로는 MinIO 클라이언트를 통해 조회)
                # 여기서는 documents 테이블의 정보를 기반으로 파일 정보 제공
                documents = self.db.query(Document).all()
                logger.info(f"MinIO에서 {len(documents)}개의 파일을 찾았습니다.")
                
                result = {
                    "files": [
                        {
                            "title": doc.doc_title,
                            "file_type": doc.doc_type,
                            "file_path": doc.file_path,
                            "upload_date": doc.created_at.isoformat() if doc.created_at else None,
                            "bucket": "documents",  # 기본 버킷
                            "path": f"uploads/{doc.doc_title}"
                        }
                        for doc in documents
                    ]
                }
                logger.info(f"MinIO 파일 조회 완료: {len(result['files'])}개")
                return result
            
            elif system_type == "opensearch":
                # OpenSearch 인덱스 정보 조회
                # 실제로는 OpenSearch 클라이언트를 통해 조회해야 함
                # 여기서는 documents 테이블의 정보를 기반으로 인덱스 정보 제공
                documents = self.db.query(Document).all()
                logger.info(f"OpenSearch에서 {len(documents)}개의 인덱스를 찾았습니다.")
                
                result = {
                    "indices": [
                        {
                            "index_name": f"document_{doc.doc_id}",
                            "document_count": 1,
                            "size_bytes": 0,  # 파일 크기 정보가 없으므로 0으로 설정
                            "created_date": doc.created_at.isoformat() if doc.created_at else None,
                            "title": doc.doc_title
                        }
                        for doc in documents
                    ]
                }
                logger.info(f"OpenSearch 인덱스 조회 완료: {len(result['indices'])}개")
                return result
            
            else:
                return {"error": "지원하지 않는 시스템 타입입니다."}
                
        except Exception as e:
            logger.error(f"시스템 문서 조회 중 오류: {str(e)}")
            return {"error": f"문서 조회 중 오류가 발생했습니다: {str(e)}"} 