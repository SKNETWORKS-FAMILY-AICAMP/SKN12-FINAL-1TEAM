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
from app.routers.chat_history_router import router as chat_history_router
from app.routers.dashboard_router import router as dashboard_router
from app.routers.approval_router import router as approval_router
from app.routers.employee_performance_router import router as employee_performance_router
from app.routers.customer_router import router as customer_router
from app.routers.employee_info_router import router as employee_info_router
from app.routers.data_upload_router import router as data_upload_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.external.opensearch_service import initialize_search_pipeline

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
print("[INFO] Logging configuration complete - all logs will be output to terminal")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 이벤트 핸들러"""
    # 시작 시 실행
    logger.info("[INFO] FastAPI 앱 시작 중...")
    
    # Search Pipeline 초기화
    logger.info("[INFO] Search Pipeline 초기화 중...")
    pipeline_success = initialize_search_pipeline()
    if pipeline_success:
        logger.info("[OK] Search Pipeline 초기화 완료")
    else:
        logger.warning("[WARNING] Search Pipeline 초기화 실패 - 기본 검색 모드로 동작")
    
    # 벡터 데이터베이스 초기화 (수동으로 처리)
    logger.info("[INFO] 벡터 데이터베이스 초기화 건너뛰기...")
    logger.info("[INFO] 벡터 데이터베이스 초기화는 수동으로 진행하세요:")
    logger.info("   1. 데이터베이스 마이그레이션: docker exec -it fastapi-app alembic upgrade head")
    logger.info("   2. 벡터 초기화: docker exec -it fastapi-app python /app/app/scripts/init_vector_db.py")
    logger.info("[WARNING] 벡터 유사도 검색 기능이 제한적으로 동작할 수 있습니다")
    
    # 모델 로딩을 비동기로 처리 (앱 시작을 차단하지 않음)
    logger.info("[INFO] AI 모델 로딩을 백그라운드에서 시작...")
    def load_models():
        try:
            from app.services.external.opensearch_client import opensearch_client
            if opensearch_client:
                # 임베딩 모델 사전 로드
                embedding_model = opensearch_client.model
                if embedding_model:
                    logger.info("[OK] 임베딩 모델 사전 로딩 완료")
                else:
                    logger.warning("[WARNING] 임베딩 모델 사전 로딩 실패")
                
                # 재순위 모델 사전 로드
                reranker_model = opensearch_client.reranker
                if reranker_model:
                    logger.info("[OK] 재순위 모델 사전 로딩 완료")
                else:
                    logger.warning("[WARNING] 재순위 모델 사전 로딩 실패")
            else:
                logger.warning("[WARNING] OpenSearch 클라이언트가 초기화되지 않음")
        except Exception as e:
            logger.error(f"[ERROR] 모델 사전 로딩 중 오류: {e}")
    
    # 모델 로딩 스레드 생성 및 시작 (데몬 스레드로 설정하여 앱 종료 시 함께 종료)
    model_loading_thread = threading.Thread(target=load_models, daemon=True)
    model_loading_thread.start()
    logger.info("[OK] 모델 로딩 스레드가 백그라운드에서 시작되었습니다")
    
    logger.info("[OK] 모든 시스템 초기화 완료")
    
    yield
    
    # 종료 시 실행 (필요시)
    logger.info("[INFO] FastAPI app shutting down...")

app = FastAPI(lifespan=lifespan)

# CORS 미들웨어 추가 - 모든 도메인에서 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_router, prefix="", tags=["Documents"])
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(qa_router, prefix="/qa", tags=["QA"])
app.include_router(hybrid_search_router, prefix="", tags=["Hybrid Search"])
app.include_router(chat_history_router, prefix="", tags=["Chat History"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(approval_router, prefix="/approval", tags=["Approval"])
app.include_router(employee_performance_router, prefix="", tags=["Employee Performance"])
app.include_router(customer_router, prefix="", tags=["Customer"])
app.include_router(employee_info_router, prefix="", tags=["Employee Info"])
app.include_router(data_upload_router, prefix="/data", tags=["Data Upload"])

@app.get("/")
def root():
    logger.info("루트 엔드포인트 호출됨")
    return {"message": "Welcome to the Database API!"}

@app.get("/health")
def health():
    logger.info("헬스체크 엔드포인트 호출됨")
    return {"status": "healthy"}

# Only keep root and ping endpoints here, all others should be in routers 