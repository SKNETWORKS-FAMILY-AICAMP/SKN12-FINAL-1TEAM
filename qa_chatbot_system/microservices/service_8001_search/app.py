"""
Search Service FastAPI Application
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
import os

from routes import router
from services import SearchService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 서비스 인스턴스
search_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global search_service
    
    # 시작 시
    logger.info("🔍 Search Service 시작 중...")
    search_service = SearchService()
    await search_service.initialize()
    logger.info("✅ Search Service 준비 완료!")
    
    yield
    
    # 종료 시
    logger.info("🔄 Search Service 종료 중...")
    if search_service:
        await search_service.cleanup()
    logger.info("✅ Search Service 종료 완료!")


def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    
    app = FastAPI(
        title="QA Chatbot - Search Service",
        description="통합 검색 서비스 (FAISS + BGE + GPT-4o-mini)",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발용
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 라우터 등록
    app.include_router(router, prefix="/api/v1")
    
    # 헬스체크 엔드포인트
    @app.get("/health")
    async def health_check():
        return {
            "service": "search",
            "status": "healthy",
            "port": 8001,
            "timestamp": time.time(),
            "features": [
                "FAISS Vector Search",
                "BGE Reranking", 
                "GPT-4o-mini Enhancement",
                "Full-text Search"
            ]
        }
    
    # 서비스 인스턴스 의존성
    def get_search_service():
        if search_service is None:
            raise HTTPException(status_code=503, detail="Search service not initialized")
        return search_service
    
    # 의존성을 앱에 추가
    app.dependency_overrides[SearchService] = get_search_service
    
    return app 