"""
Search Service Business Logic
통합 검색 서비스 - FAISS + BGE + GPT-4o-mini
"""
import os
import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional
import time
import json
import sqlite3
from pathlib import Path

# 공통 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from models import SearchResult
from openai_client import multi_gpt_client

logger = logging.getLogger(__name__)


class SearchService:
    """
    통합 검색 서비스
    - FAISS 벡터 검색
    - BGE 재순위 지정  
    - GPT-4o-mini 향상
    - 키워드 검색
    """
    
    def __init__(self):
        self.is_initialized = False
        self.vector_index = None
        self.embeddings_model = None
        self.bge_model = None
        self.search_stats = {
            "total_searches": 0,
            "vector_searches": 0,
            "keyword_searches": 0,
            "enhanced_searches": 0,
            "avg_response_time": 0.0,
            "last_reindex": None
        }
        
        # 데이터베이스 경로
        self.db_path = Path(__file__).parent.parent.parent.parent / "data" / "databases"
        self.documents_path = Path(__file__).parent.parent.parent.parent / "data" / "documents"
        
    async def initialize(self):
        """서비스 초기화"""
        try:
            logger.info("🔍 검색 서비스 초기화 시작...")
            
            # 1. 디렉토리 생성
            self.db_path.mkdir(parents=True, exist_ok=True)
            self.documents_path.mkdir(parents=True, exist_ok=True)
            
            # 2. 벡터 검색 초기화 (시뮬레이션)
            await self._initialize_vector_search()
            
            # 3. 임베딩 모델 초기화 (시뮬레이션)
            await self._initialize_embeddings()
            
            # 4. BGE 모델 초기화 (시뮬레이션)
            await self._initialize_bge()
            
            # 5. 샘플 데이터 생성
            await self._create_sample_data()
            
            self.is_initialized = True
            logger.info("✅ 검색 서비스 초기화 완료!")
            
        except Exception as e:
            logger.error(f"❌ 검색 서비스 초기화 실패: {e}")
            raise
    
    async def _initialize_vector_search(self):
        """FAISS 벡터 검색 초기화"""
        logger.info("📊 FAISS 벡터 인덱스 초기화...")
        # 실제 구현에서는 FAISS 인덱스 로드
        self.vector_index = "faiss_index_simulation"
        await asyncio.sleep(0.1)  # 시뮬레이션
        
    async def _initialize_embeddings(self):
        """임베딩 모델 초기화"""
        logger.info("🔤 KURE-v1 임베딩 모델 초기화...")
        # 실제 구현에서는 sentence-transformers 로드
        self.embeddings_model = "kure_v1_simulation"
        await asyncio.sleep(0.1)  # 시뮬레이션
        
    async def _initialize_bge(self):
        """BGE 재순위 모델 초기화"""
        logger.info("🎯 BGE 재순위 모델 초기화...")
        # 실제 구현에서는 BGE 모델 로드
        self.bge_model = "bge_simulation"
        await asyncio.sleep(0.1)  # 시뮬레이션
    
    async def _create_sample_data(self):
        """샘플 데이터 생성"""
        sample_documents = [
            {
                "id": "doc_001",
                "title": "의료기기 영업 전략 가이드",
                "content": "의료기기 영업에서 중요한 것은 의료진과의 신뢰 관계 구축입니다. 제품의 기술적 우수성뿐만 아니라 의료진의 니즈를 파악하고 맞춤형 솔루션을 제공하는 것이 핵심입니다.",
                "category": "sales",
                "keywords": ["의료기기", "영업", "신뢰관계", "맞춤형솔루션"]
            },
            {
                "id": "doc_002", 
                "title": "병원 구매 담당자와의 소통 방법",
                "content": "병원 구매 담당자와 효과적으로 소통하기 위해서는 비용 효율성, 품질 보증, 사후 서비스 등을 명확하게 제시해야 합니다. 데이터 기반의 설득이 중요합니다.",
                "category": "communication",
                "keywords": ["병원", "구매담당자", "비용효율성", "품질보증", "데이터기반"]
            },
            {
                "id": "doc_003",
                "title": "의료업계 최신 동향 분석",
                "content": "2024년 의료업계는 디지털 헬스케어, AI 진단, 원격 진료 등의 트렌드가 주목받고 있습니다. 이러한 변화에 맞춰 영업 전략도 수정이 필요합니다.",
                "category": "trends",
                "keywords": ["디지털헬스케어", "AI진단", "원격진료", "2024트렌드"]
            }
        ]
        
        # 샘플 문서를 메모리에 저장 (실제로는 DB에 저장)
        self.sample_documents = sample_documents
        logger.info(f"📄 샘플 문서 {len(sample_documents)}건 생성 완료")
    
    async def search(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10, 
        offset: int = 0
    ) -> List[SearchResult]:
        """
        통합 검색 (벡터 + 키워드 + BGE 재순위)
        """
        try:
            start_time = time.time()
            
            # 1단계: 벡터 검색
            vector_results = await self.vector_search(query, limit=limit*2)
            
            # 2단계: 키워드 검색
            keyword_results = await self.keyword_search(query, limit=limit*2)
            
            # 3단계: 결과 합성 및 중복 제거
            combined_results = self._combine_results(vector_results, keyword_results)
            
            # 4단계: BGE 재순위
            reranked_results = await self._bge_rerank(combined_results, query)
            
            # 5단계: 필터링 및 페이징
            filtered_results = self._apply_filters(reranked_results, filters)
            paginated_results = filtered_results[offset:offset+limit]
            
            # 통계 업데이트
            self.search_stats["total_searches"] += 1
            self.search_stats["avg_response_time"] = (
                self.search_stats["avg_response_time"] * (self.search_stats["total_searches"] - 1) +
                (time.time() - start_time)
            ) / self.search_stats["total_searches"]
            
            return paginated_results
            
        except Exception as e:
            logger.error(f"통합 검색 실패: {e}")
            return []
    
    async def vector_search(
        self, 
        query: str, 
        limit: int = 10, 
        threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        FAISS 벡터 검색
        """
        try:
            # 실제 구현에서는 query를 임베딩으로 변환 후 FAISS 검색
            # 여기서는 시뮬레이션
            
            results = []
            for i, doc in enumerate(self.sample_documents[:limit]):
                # 시뮬레이션된 유사도 점수
                score = max(0.6, 1.0 - (i * 0.1))
                
                if score >= threshold:
                    results.append(SearchResult(
                        id=doc["id"],
                        title=doc["title"],
                        content=doc["content"],
                        score=score,
                        metadata={
                            "category": doc["category"],
                            "keywords": doc["keywords"],
                            "search_type": "vector"
                        },
                        source="vector_search"
                    ))
            
            self.search_stats["vector_searches"] += 1
            return results
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return []
    
    async def keyword_search(
        self, 
        query: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[SearchResult]:
        """
        키워드 기반 전체 텍스트 검색
        """
        try:
            query_words = query.lower().split()
            results = []
            
            for doc in self.sample_documents:
                # 간단한 키워드 매칭 점수 계산
                content_lower = (doc["title"] + " " + doc["content"]).lower()
                matches = sum(1 for word in query_words if word in content_lower)
                score = matches / len(query_words) if query_words else 0
                
                if score > 0:
                    results.append(SearchResult(
                        id=doc["id"],
                        title=doc["title"],
                        content=doc["content"],
                        score=score,
                        metadata={
                            "category": doc["category"],
                            "keywords": doc["keywords"],
                            "search_type": "keyword",
                            "matches": matches
                        },
                        source="keyword_search"
                    ))
            
            # 점수 순으로 정렬
            results.sort(key=lambda x: x.score, reverse=True)
            
            self.search_stats["keyword_searches"] += 1
            return results[offset:offset+limit]
            
        except Exception as e:
            logger.error(f"키워드 검색 실패: {e}")
            return []
    
    async def _bge_rerank(
        self, 
        results: List[SearchResult], 
        query: str
    ) -> List[SearchResult]:
        """
        BGE 모델을 사용한 재순위 지정
        """
        try:
            # 실제 구현에서는 BGE 모델로 query-document 유사도 재계산
            # 여기서는 시뮬레이션으로 점수 조정
            
            for result in results:
                # 시뮬레이션: 키워드 매칭 기반 점수 보정
                keyword_bonus = 0.1 if any(
                    keyword.lower() in query.lower() 
                    for keyword in result.metadata.get("keywords", [])
                ) else 0
                
                result.score = min(1.0, result.score + keyword_bonus)
                result.metadata["reranked"] = True
            
            # 재정렬
            results.sort(key=lambda x: x.score, reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"BGE 재순위 실패: {e}")
            return results  # 실패 시 원본 반환
    
    def _combine_results(
        self, 
        vector_results: List[SearchResult], 
        keyword_results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        벡터 검색과 키워드 검색 결과 합성
        """
        combined = {}
        
        # 벡터 검색 결과 추가
        for result in vector_results:
            combined[result.id] = result
        
        # 키워드 검색 결과 추가 (중복 시 높은 점수 선택)
        for result in keyword_results:
            if result.id in combined:
                if result.score > combined[result.id].score:
                    combined[result.id] = result
            else:
                combined[result.id] = result
        
        return list(combined.values())
    
    def _apply_filters(
        self, 
        results: List[SearchResult], 
        filters: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """
        필터 적용
        """
        if not filters:
            return results
        
        filtered = []
        for result in results:
            include = True
            
            # 카테고리 필터
            if "category" in filters:
                if result.metadata.get("category") != filters["category"]:
                    include = False
            
            # 최소 점수 필터
            if "min_score" in filters:
                if result.score < filters["min_score"]:
                    include = False
            
            if include:
                filtered.append(result)
        
        return filtered
    
    async def enhance_results(
        self, 
        results: List[SearchResult], 
        query: str, 
        limit: int = 10
    ) -> List[SearchResult]:
        """
        GPT-4o-mini를 사용한 검색 결과 향상
        """
        try:
            enhanced_results = []
            
            for result in results[:limit]:
                # GPT-4o-mini로 컨텐츠 향상
                enhanced_content = await multi_gpt_client.enhance_content(
                    content=result.content,
                    context=f"사용자 질의: {query}"
                )
                
                # 향상된 결과 생성
                enhanced_result = SearchResult(
                    id=result.id,
                    title=result.title,
                    content=enhanced_content,
                    score=result.score,
                    metadata={
                        **result.metadata,
                        "enhanced": True,
                        "original_content": result.content
                    },
                    source=f"{result.source}_enhanced"
                )
                
                enhanced_results.append(enhanced_result)
            
            self.search_stats["enhanced_searches"] += 1
            return enhanced_results
            
        except Exception as e:
            logger.error(f"결과 향상 실패: {e}")
            return results  # 실패 시 원본 반환
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        검색 서비스 통계 조회
        """
        return {
            **self.search_stats,
            "service_status": "healthy" if self.is_initialized else "initializing",
            "available_documents": len(self.sample_documents),
            "supported_features": [
                "FAISS Vector Search",
                "BGE Reranking",
                "GPT-4o-mini Enhancement", 
                "Keyword Search",
                "Filtering",
                "Pagination"
            ]
        }
    
    async def reindex(self) -> Dict[str, Any]:
        """
        문서 재인덱싱
        """
        try:
            start_time = time.time()
            
            # 실제 구현에서는 모든 문서를 다시 임베딩하고 FAISS 인덱스 재생성
            await asyncio.sleep(1)  # 시뮬레이션
            
            processing_time = time.time() - start_time
            self.search_stats["last_reindex"] = time.time()
            
            return {
                "reindexed_documents": len(self.sample_documents),
                "processing_time": processing_time,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"재인덱싱 실패: {e}")
            raise
    
    async def cleanup(self):
        """서비스 정리"""
        logger.info("🧹 검색 서비스 정리 중...")
        # 리소스 정리 작업
        self.vector_index = None
        self.embeddings_model = None
        self.bge_model = None
        self.is_initialized = False 