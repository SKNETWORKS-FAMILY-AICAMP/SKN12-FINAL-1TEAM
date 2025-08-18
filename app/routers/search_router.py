"""
검색 API 라우터

Text2SQL 검색과 OpenSearch 파이프라인 검색 기능을 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from app.services.core.text2sql_search import text2sql_search_service
from app.services.external.opensearch_client import opensearch_client
from app.routers.user_router import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Response Models
class Text2SQLSearchResult(BaseModel):
    """Text2SQL 검색 결과 모델"""
    id: int
    doc_id: int
    table_type: str
    content: Dict[str, Any]
    created_at: Optional[str] = None
    similarity_score: Optional[float] = None
    source: str = "text2sql"

class OpenSearchResult(BaseModel):
    """OpenSearch 검색 결과 모델"""
    id: str
    doc_id: Optional[Union[int, str]] = None  # UUID 또는 정수 허용
    doc_title: Optional[str] = None
    content: str
    created_at: Optional[str] = None
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None
    source: str = "opensearch"

class SearchResponse(BaseModel):
    """검색 응답 모델"""
    success: bool
    message: str
    query: str
    results: List[Any]
    total_count: int
    search_time: float

# Text2SQL Search Endpoints
@router.get("/text2sql", response_model=SearchResponse)
async def search_text2sql(
    query: str = Query(..., description="검색 쿼리"),
    limit: Optional[int] = Query(20, description="결과 개수 제한", ge=1, le=100),
    user=Depends(get_current_user)
):
    """
    Text2SQL을 사용하여 테이블 데이터를 검색합니다.
    
    Args:
        query: 검색 쿼리
        limit: 결과 개수 제한 (기본값: 20)
        user: 현재 인증된 사용자
        
    Returns:
        SearchResponse: Text2SQL 검색 결과
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Text2SQL 검색 시작: '{query}'")
        
        # Text2SQL 검색 수행
        search_result = text2sql_search_service.search(
            query=query,
            limit=limit
        )
        
        if not search_result['success']:
            raise HTTPException(status_code=500, detail=search_result['message'])
        
        # 결과 형식 변환
        formatted_results = []
        for result in search_result['results']:
            formatted_result = Text2SQLSearchResult(
                id=result['id'],
                doc_id=result['doc_id'],
                table_type=result['table_type'],
                content=result['content'],
                created_at=result.get('created_at'),
                similarity_score=result.get('similarity_score'),
                source="text2sql"
            )
            formatted_results.append(formatted_result.dict())
        
        search_time = time.time() - start_time
        
        logger.info(f"Text2SQL 검색 완료: {len(formatted_results)}개 결과")
        
        return SearchResponse(
            success=True,
            message=f"Text2SQL 검색이 완료되었습니다.",
            query=query,
            results=formatted_results,
            total_count=len(formatted_results),
            search_time=search_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text2SQL 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

# OpenSearch Pipeline Search Endpoints
@router.get("/opensearch", response_model=SearchResponse)
async def search_opensearch(
    query: str = Query(..., description="검색 쿼리"),
    limit: Optional[int] = Query(20, description="결과 개수 제한", ge=1, le=100),
    pipeline_id: Optional[str] = Query("hybrid-minmax-pipeline", description="사용할 파이프라인 ID"),
    user=Depends(get_current_user)
):
    """
    OpenSearch 파이프라인을 사용하여 문서를 검색합니다.
    
    Args:
        query: 검색 쿼리
        limit: 결과 개수 제한 (기본값: 20)
        pipeline_id: 사용할 검색 파이프라인 ID
        user: 현재 인증된 사용자
        
    Returns:
        SearchResponse: OpenSearch 검색 결과
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"OpenSearch 파이프라인 검색 시작: '{query}'")
        
        # OpenSearch 클라이언트 확인
        if not opensearch_client or not opensearch_client.client:
            raise HTTPException(status_code=503, detail="OpenSearch 서비스를 사용할 수 없습니다.")
        
        # 키워드 추출
        from app.services.external.opensearch_service import extract_keywords_from_question
        keywords = extract_keywords_from_question(query, top_k=10)
        
        # OpenSearch 파이프라인 검색 수행
        search_results = opensearch_client.search_with_pipeline(
            query_text=query,
            keywords=keywords,
            pipeline_id=pipeline_id,
            top_k=limit,
            index_name="document_chunks"  # 올바른 인덱스 이름 지정
        )
        
        # 결과 형식 변환 (search_results는 리스트)
        formatted_results = []
        for hit in search_results:  # 리스트로 직접 순회
            source = hit.get('source', {})
            formatted_result = OpenSearchResult(
                id=str(source.get('document_id', '')),  # 정수를 문자열로 변환
                doc_id=source.get('document_id'),  # document_id 필드 사용
                doc_title=source.get('title'),  # title 필드 사용
                content=source.get('content', ''),
                created_at=source.get('created_at'),
                similarity_score=hit.get('score', 0.0) if hit.get('score') else hit.get('rerank_score', 0.0),  # rerank_score도 체크
                metadata=source.get('metadata'),
                source="opensearch"
            )
            formatted_results.append(formatted_result.dict())
        
        search_time = time.time() - start_time
        total_count = len(formatted_results)  # 리스트이므로 길이로 계산
        
        logger.info(f"OpenSearch 검색 완료: {len(formatted_results)}개 결과")
        
        return SearchResponse(
            success=True,
            message=f"OpenSearch 파이프라인 검색이 완료되었습니다.",
            query=query,
            results=formatted_results,
            total_count=total_count,
            search_time=search_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OpenSearch 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

# Combined Search Endpoint
@router.get("/all", response_model=Dict[str, SearchResponse])
async def search_all(
    query: str = Query(..., description="검색 쿼리"),
    limit: Optional[int] = Query(20, description="각 검색 방식별 결과 개수 제한", ge=1, le=100),
    user=Depends(get_current_user)
):
    """
    Text2SQL과 OpenSearch 모두를 사용하여 검색합니다.
    
    Args:
        query: 검색 쿼리
        limit: 각 검색 방식별 결과 개수 제한 (기본값: 20)
        user: 현재 인증된 사용자
        
    Returns:
        Dict: 각 검색 방식별 결과를 포함한 딕셔너리
    """
    try:
        logger.info(f"통합 검색 시작: '{query}'")
        
        results = {}
        
        # Text2SQL 검색
        try:
            text2sql_result = await search_text2sql(query, limit, user)
            results['text2sql'] = text2sql_result
        except Exception as e:
            logger.error(f"Text2SQL 검색 실패: {e}")
            results['text2sql'] = SearchResponse(
                success=False,
                message=f"Text2SQL 검색 실패: {str(e)}",
                query=query,
                results=[],
                total_count=0,
                search_time=0.0
            )
        
        # OpenSearch 검색
        try:
            opensearch_result = await search_opensearch(query, limit, "hybrid-minmax-pipeline", user)
            results['opensearch'] = opensearch_result
        except Exception as e:
            logger.error(f"OpenSearch 검색 실패: {e}")
            results['opensearch'] = SearchResponse(
                success=False,
                message=f"OpenSearch 검색 실패: {str(e)}",
                query=query,
                results=[],
                total_count=0,
                search_time=0.0
            )
        
        logger.info(f"통합 검색 완료")
        
        return results
        
    except Exception as e:
        logger.error(f"통합 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

# Search Statistics Endpoint
@router.get("/stats")
async def get_search_stats(user=Depends(get_current_user)):
    """
    검색 시스템 통계 정보를 조회합니다.
    
    Args:
        user: 현재 인증된 사용자
        
    Returns:
        Dict: 검색 시스템 통계 정보
    """
    try:
        stats = {
            'text2sql': {
                'available': False,
                'message': ''
            },
            'opensearch': {
                'available': False,
                'message': '',
                'indices': []
            }
        }
        
        # Text2SQL 상태 확인
        try:
            if text2sql_search_service:
                stats['text2sql']['available'] = True
                stats['text2sql']['message'] = 'Text2SQL 검색 서비스가 정상 작동 중입니다.'
        except:
            stats['text2sql']['message'] = 'Text2SQL 검색 서비스를 사용할 수 없습니다.'
        
        # OpenSearch 상태 확인
        try:
            if opensearch_client and opensearch_client.client:
                if opensearch_client.client.ping():
                    stats['opensearch']['available'] = True
                    stats['opensearch']['message'] = 'OpenSearch가 정상 작동 중입니다.'
                    
                    # 인덱스 정보 조회
                    indices = opensearch_client.client.indices.get_alias("*")
                    stats['opensearch']['indices'] = list(indices.keys())
        except:
            stats['opensearch']['message'] = 'OpenSearch를 사용할 수 없습니다.'
        
        return {
            'success': True,
            'message': '검색 시스템 통계 조회 완료',
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"검색 통계 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")