from dotenv import load_dotenv
from pathlib import Path
import os
import sys

# 환경변수 및 경로 설정 개선
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
backend_root = current_dir.parent

# sys.path 설정 (중복 방지)
paths_to_add = [str(project_root), str(backend_root), str(current_dir)]
for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

print(f"📁 현재 디렉토리: {current_dir}")
print(f"📁 프로젝트 루트: {project_root}")
print(f"📁 백엔드 루트: {backend_root}")

# .env 파일 로드 개선
env_paths = [
    current_dir / ".env",
    backend_root / ".env", 
    project_root / ".env"
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✅ .env 로드됨: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("⚠️ .env 파일을 찾을 수 없습니다. 환경변수를 직접 설정하세요.")

# OpenAI API 키 확인
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    print(f"✅ OPENAI_API_KEY 로드됨: {openai_key[:10]}...")
else:
    print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 임포트 개선 - 상대 임포트와 절대 임포트 둘 다 시도
def safe_import():
    """안전한 임포트를 위한 함수"""
    try:
        # 상대 임포트 시도 (패키지로 실행될 때)
        from .api.router_api import router
        from .api.docs_api import router as docs_router
        from .api.employee_api import router as employee_router
        from .api.client_api import router as client_router
        from .api.download_api import router as download_router
        from .api.fastapi_router_main import api_router as tool_calling_router
        print("✅ 상대 임포트 성공")
        return router, docs_router, employee_router, client_router, download_router, tool_calling_router
    except ImportError as e:
        print(f"⚠️ 상대 임포트 실패: {e}")
        try:
            # 절대 임포트 시도 (직접 실행될 때)
            from app.api.router_api import router
            from app.api.docs_api import router as docs_router
            from app.api.employee_api import router as employee_router
            from app.api.client_api import router as client_router
            from app.api.download_api import router as download_router
            from app.api.fastapi_router_main import api_router as tool_calling_router
            print("✅ 절대 임포트 성공")
            return router, docs_router, employee_router, client_router, download_router, tool_calling_router
        except ImportError as e2:
            print(f"❌ 절대 임포트도 실패: {e2}")
            print("📍 현재 sys.path:")
            for i, path in enumerate(sys.path[:5]):
                print(f"  {i}: {path}")
            raise ImportError(f"API 라우터 임포트 실패: {e2}")

# 라우터 임포트
router, docs_router, employee_router, client_router, download_router, tool_calling_router = safe_import()

import logging
import uvicorn

# ✅ 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ FastAPI 앱 생성
app = FastAPI(
    title="NaruTalk AI 챗봇 API",
    description="LangGraph 기반 4분류 자동 라우팅 시스템",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ✅ CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서만 사용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API 라우터 등록
try:
    app.include_router(router, prefix="/api/route", tags=["RouterAgent"])
    app.include_router(docs_router, prefix="/api/docs", tags=["DocsAgent"])
    app.include_router(employee_router, prefix="/api/employee", tags=["Employee Analysis"])
    app.include_router(client_router, prefix="/api/client", tags=["Client Analysis"])
    app.include_router(download_router, prefix="/api/download", tags=["Download API"])
    app.include_router(tool_calling_router, prefix="/api/v1", tags=["Tool Calling"])
    logger.info("✅ 모든 API 라우터가 성공적으로 등록되었습니다.")
except Exception as e:
    logger.error(f"❌ API 라우터 등록 중 오류: {e}")
    raise

# ✅ 기본 루트 엔드포인트
@app.get("/")
def root():
    return {
        "message": "🚀 NaruTalk AI 챗봇 API가 실행 중입니다!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "message": "시스템이 정상적으로 작동 중입니다.",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "environment": "development" if os.getenv("DEBUG") else "production"
    }

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 NaruTalk AI 챗봇 백엔드 서버 시작")
    print("="*50)
    print(f"📱 서버 주소: http://localhost:8000")
    print(f"📚 API 문서: http://localhost:8000/docs")
    print(f"🔍 헬스 체크: http://localhost:8000/health")
    print(f"⏹️  서버 중지: Ctrl+C")
    print("="*50)
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 서버가 중지되었습니다.")
    except Exception as e:
        print(f"\n❌ 서버 실행 중 오류: {e}")
        sys.exit(1)