"""
Search Service API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import time
import sys
import os

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from models import SearchRequest, SearchResponse, SearchResult, BaseResponse
from services import SearchService

router = APIRouter(tags=["Search"])


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    search_service: SearchService = Depends()
):
    """
    통합 문서 검색 API
    - FAISS 벡터 검색
    - BGE 재순위 지정
    - GPT-4o-mini 향상
    """
    try:
        start_time = time.time()
        
        # 검색 실행
        results = await search_service.search(
            query=request.query,
            filters=request.filters,
            limit=request.limit,
            offset=request.offset
        )
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            success=True,
            message=f"검색 완료: {len(results)} 건의 결과를 찾았습니다.",
            results=results,
            total_count=len(results),
            query=request.query,
            request_id=request.request_id,
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"검색 중 오류 발생: {str(e)}"
        )


@router.post("/search/vector", response_model=SearchResponse)
async def vector_search(
    request: SearchRequest,
    search_service: SearchService = Depends()
):
    """
    벡터 검색 전용 API (FAISS)
    """
    try:
        start_time = time.time()
        
        results = await search_service.vector_search(
            query=request.query,
            limit=request.limit,
            threshold=0.7  # 유사도 임계값
        )
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            success=True,
            message=f"벡터 검색 완료: {len(results)} 건",
            results=results,
            total_count=len(results),
            query=request.query,
            request_id=request.request_id,
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"벡터 검색 중 오류 발생: {str(e)}"
        )


@router.post("/search/keyword", response_model=SearchResponse)
async def keyword_search(
    request: SearchRequest,
    search_service: SearchService = Depends()
):
    """
    키워드 검색 전용 API (전체 텍스트)
    """
    try:
        start_time = time.time()
        
        results = await search_service.keyword_search(
            query=request.query,
            limit=request.limit,
            offset=request.offset
        )
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            success=True,
            message=f"키워드 검색 완료: {len(results)} 건",
            results=results,
            total_count=len(results),
            query=request.query,
            request_id=request.request_id,
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"키워드 검색 중 오류 발생: {str(e)}"
        )


@router.post("/search/enhanced", response_model=SearchResponse)
async def enhanced_search(
    request: SearchRequest,
    search_service: SearchService = Depends()
):
    """
    GPT-4o-mini 향상된 검색 API
    """
    try:
        start_time = time.time()
        
        # 1단계: 기본 검색
        basic_results = await search_service.search(
            query=request.query,
            limit=request.limit * 2  # 더 많은 결과 수집
        )
        
        # 2단계: GPT-4o-mini로 향상
        enhanced_results = await search_service.enhance_results(
            results=basic_results,
            query=request.query,
            limit=request.limit
        )
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            success=True,
            message=f"향상된 검색 완료: {len(enhanced_results)} 건",
            results=enhanced_results,
            total_count=len(enhanced_results),
            query=request.query,
            request_id=request.request_id,
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"향상된 검색 중 오류 발생: {str(e)}"
        )


@router.get("/search/stats")
async def get_search_stats(
    search_service: SearchService = Depends()
):
    """
    검색 서비스 통계 API
    """
    try:
        stats = await search_service.get_stats()
        
        return BaseResponse(
            success=True,
            message="검색 서비스 통계를 조회했습니다.",
            data=stats
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"통계 조회 중 오류 발생: {str(e)}"
        )


@router.post("/search/reindex")
async def reindex_documents(
    search_service: SearchService = Depends()
):
    """
    문서 재인덱싱 API (관리자용)
    """
    try:
        result = await search_service.reindex()
        
        return BaseResponse(
            success=True,
            message="문서 재인덱싱이 완료되었습니다.",
            data=result
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"재인덱싱 중 오류 발생: {str(e)}"
        ) 