import logging
import sys
import threading
import time
from contextlib import asynccontextmanager
from app.routers.document_router import router as document_router
from app.routers.user_router import router as user_router
from app.routers.admin_router import router as admin_router
from app.routers.qa_router import router as qa_router
from app.routers.hybrid_search_router import router as hybrid_search_router
from fastapi import FastAPI
from app.services.opensearch_service import initialize_search_pipeline

# 로깅 설정 - 터미널에서 모든 로그 보이도록
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # 기존 로거 설정을 강제로 덮어쓰기
)

# 루트 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 모든 로거를 INFO 레벨로 설정
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("opensearch").setLevel(logging.INFO)
logging.getLogger("services.opensearch_client").setLevel(logging.INFO)
logging.getLogger("services.opensearch_service").setLevel(logging.INFO)

# 로그 출력 확인
print("🔧 로깅 설정 완료 - 모든 로그가 터미널에 출력됩니다")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 이벤트 핸들러"""
    # 시작 시 실행
    logger.info("🚀 FastAPI 앱 시작 중...")
    
    # Search Pipeline 초기화
    logger.info("🔧 Search Pipeline 초기화 중...")
    pipeline_success = initialize_search_pipeline()
    if pipeline_success:
        logger.info("✅ Search Pipeline 초기화 완료")
    else:
        logger.warning("⚠️ Search Pipeline 초기화 실패 - 기본 검색 모드로 동작")
    
    # 모델 로딩 스레드 시작
    logger.info("🤖 AI 모델 로딩 스레드 시작...")
    def load_models():
        try:
            from app.services.opensearch_client import opensearch_client
            if opensearch_client:
                # 임베딩 모델 사전 로드
                embedding_model = opensearch_client.model
                if embedding_model:
                    logger.info("✅ 임베딩 모델 사전 로딩 완료")
                else:
                    logger.warning("⚠️ 임베딩 모델 사전 로딩 실패")
                
                # 재순위 모델 사전 로드
                reranker_model = opensearch_client.reranker
                if reranker_model:
                    logger.info("✅ 재순위 모델 사전 로딩 완료")
                else:
                    logger.warning("⚠️ 재순위 모델 사전 로딩 실패")
            else:
                logger.warning("⚠️ OpenSearch 클라이언트가 초기화되지 않음")
        except Exception as e:
            logger.error(f"❌ 모델 사전 로딩 중 오류: {e}")
    
    # 모델 로딩 스레드 생성 및 시작
    model_loading_thread = threading.Thread(target=load_models)
    model_loading_thread.start()
    logger.info("✅ 모델 로딩 스레드 시작")
    
    logger.info("🎉 모든 시스템 초기화 완료")
    
    yield
    
    # 종료 시 실행 (필요시)
    logger.info("🛑 FastAPI 앱 종료 중...")

app = FastAPI(lifespan=lifespan)

app.include_router(document_router, prefix="", tags=["Documents"])
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(qa_router, prefix="/qa", tags=["QA"])
app.include_router(hybrid_search_router, prefix="", tags=["Hybrid Search"])

@app.get("/")
def root():
    logger.info("루트 엔드포인트 호출됨")
    return {"message": "Welcome to the Database API!"}

@app.get("/ping")
def ping():
    logger.info("핑 엔드포인트 호출됨")
    return {"message": "pong"}

# Only keep root and ping endpoints here, all others should be in routers 