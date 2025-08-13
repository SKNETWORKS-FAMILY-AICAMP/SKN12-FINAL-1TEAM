"""
대시보드 라우터
문서 업로드로 인한 자동 생성 데이터 모니터링 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.utils.db import get_db
from app.services.core.dashboard_service import DashboardService
from app.routers.user_router import get_current_user, get_current_admin_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(
    days: int = Query(30, description="조회 기간 (일)", ge=1, le=365),
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    대시보드 통계 조회
    
    Args:
        days: 조회 기간 (일)
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        Dict: 대시보드 통계 정보
    """
    try:
        # 트랜잭션 격리 레벨 설정으로 락 경합 방지
        db.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
        
        dashboard_service = DashboardService(db)
        
        stats = dashboard_service.get_dashboard_stats(days)
        
        logger.info(f"대시보드 통계 조회 완료: {days}일간")
        return stats
        
    except Exception as e:
        logger.error(f"대시보드 통계 조회 중 오류: {e}")
        # 트랜잭션 롤백 후 기본값 반환
        try:
            db.rollback()
        except:
            pass
        return {
            'total_documents': 0,
            'total_auto_created': 0,
            'auto_created_by_type': {},
            'recent_uploads': [],
            'upload_success_rate': 0.0,
            'auto_create_success_rate': 0.0
        }

@router.get("/auto-create/{entity_type}")
def get_auto_create_summary(
    entity_type: str,
    days: int = Query(30, description="조회 기간 (일)", ge=1, le=365),
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    특정 엔티티 타입의 자동 생성 요약 조회
    
    Args:
        entity_type: 엔티티 타입 (employee, customer, product, sales_record)
        days: 조회 기간 (일)
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        Dict: 자동 생성 요약 정보
    """
    try:
        # 유효한 엔티티 타입 검증
        valid_entity_types = ['employee', 'customer', 'product', 'sales_record']
        if entity_type not in valid_entity_types:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 엔티티 타입입니다. 지원되는 타입: {valid_entity_types}")
        
        dashboard_service = DashboardService(db)
        
        summary = dashboard_service.get_auto_create_summary(entity_type, days)
        
        logger.info(f"자동 생성 요약 조회 완료: {entity_type}, {days}일간")
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동 생성 요약 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"자동 생성 요약 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/document/{document_id}")
def get_document_upload_summary(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    특정 문서의 업로드 요약 조회
    
    Args:
        document_id: 문서 ID
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        Dict: 문서 업로드 요약 정보
    """
    try:
        dashboard_service = DashboardService(db)
        
        summary = dashboard_service.get_document_upload_summary(document_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        
        logger.info(f"문서 업로드 요약 조회 완료: document_id={document_id}")
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 업로드 요약 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문서 업로드 요약 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/recent-activities")
def get_recent_activities(
    entity_type: Optional[str] = Query(None, description="엔티티 타입 필터"),
    limit: int = Query(20, description="조회 개수", ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    최근 자동 생성 활동 조회
    
    Args:
        entity_type: 엔티티 타입 필터 (선택사항)
        limit: 조회 개수
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        Dict: 최근 활동 목록
    """
    try:
        # 최근 활동 조회 (간단한 구현)
        from app.models.system_trace_logs import SystemTraceLog
        from sqlalchemy import desc
        
        query = db.query(SystemTraceLog).filter(
            SystemTraceLog.event_type == 'auto_create'
        )
        
        recent_logs = query.order_by(desc(SystemTraceLog.created_at)).limit(limit).all()
        
        activities = []
        for log in recent_logs:
            log_data = log.log_data or {}
            log_entity_type = log_data.get('entity_type', '')
            
            # 엔티티 타입 필터 적용
            if entity_type and log_entity_type != entity_type:
                continue
                
            activities.append({
                'trace_id': log.trace_id,
                'event_type': log.event_type,
                'entity_type': log_entity_type,
                'action': log_data.get('action', ''),
                'entity_id': log_data.get('entity_id'),
                'document_id': log_data.get('document_id'),
                'message': log_data.get('message', ''),
                'created_at': log.created_at.isoformat(),
                'details': log_data.get('details', {})
            })
        
        logger.info(f"최근 활동 조회 완료: {len(activities)}개")
        return {
            'activities': activities,
            'total_count': len(activities)
        }
        
    except Exception as e:
        logger.error(f"최근 활동 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"최근 활동 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/health")
def get_dashboard_health(
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    대시보드 시스템 상태 확인
    
    Args:
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        Dict: 시스템 상태 정보
    """
    try:
        # 기본 통계 조회
        from app.models.system_trace_logs import SystemTraceLog
        from app.models.documents import Document
        
        total_logs = db.query(SystemTraceLog).count()
        total_documents = db.query(Document).count()
        
        # 최근 24시간 활동
        from datetime import datetime, timedelta
        recent_24h = datetime.now() - timedelta(hours=24)
        
        recent_logs = db.query(SystemTraceLog).filter(
            SystemTraceLog.created_at >= recent_24h
        ).count()
        
        recent_documents = db.query(Document).filter(
            Document.created_at >= recent_24h
        ).count()
        
        return {
            'status': 'healthy',
            'total_logs': total_logs,
            'total_documents': total_documents,
            'recent_24h_logs': recent_logs,
            'recent_24h_documents': recent_documents,
            'last_check': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"대시보드 상태 확인 중 오류: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'last_check': datetime.now().isoformat()
        }

@router.get("/system-documents")
def get_system_documents(
    system: str = Query(..., description="시스템 타입 (postgresql, minio, opensearch)"),
    db: Session = Depends(get_db),
    user=Depends(get_current_admin_user)
):
    """
    시스템별 문서 정보 조회
    
    Args:
        system: 시스템 타입
        db: 데이터베이스 세션
        user: 현재 인증된 관리자
        
    Returns:
        Dict: 시스템별 문서 정보
    """
    try:
        # 유효한 시스템 타입 검증
        valid_systems = ['postgresql', 'minio', 'opensearch']
        if system not in valid_systems:
            raise HTTPException(status_code=400, detail=f"유효하지 않은 시스템 타입입니다. 지원되는 타입: {valid_systems}")
        
        dashboard_service = DashboardService(db)
        
        result = dashboard_service.get_system_documents(system)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        logger.info(f"시스템 문서 조회 완료: {system}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시스템 문서 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"시스템 문서 조회 중 오류가 발생했습니다: {str(e)}") 