import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv

# .env 파일 경로 설정
env_path = project_root / ".env"
parent_env = project_root.parent / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ .env 로드됨: {env_path}")
elif parent_env.exists():
    load_dotenv(dotenv_path=parent_env)
    print(f"✅ .env 로드됨: {parent_env}")
else:
    print("⚠️ .env 파일을 찾을 수 없습니다")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.router_api import router
from .api.docs_api import router as docs_router
from .api.employee_api import router as employee_router
from .api.client_api import router as client_router
from .api.download_api import router as download_router
from .api.fastapi_router_main import api_router as tool_calling_router
import logging
import uvicorn

# 확인용 (선택)
print("✅ OPENAI_API_KEY 로드됨:", os.getenv("OPENAI_API_KEY")[:10])

# ✅ 로깅 설정
logging.basicConfig(level=logging.INFO)

# ✅ FastAPI 앱 생성
app = FastAPI(
    title="RouterAgent API",
    description="GPT-4o 기반 4분류 자동 라우팅 시스템",
    version="1.0.0"
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
app.include_router(router, prefix="/api/route", tags=["RouterAgent"])
app.include_router(docs_router, prefix="/api/docs", tags=["DocsAgent"])
app.include_router(employee_router, prefix="/api/employee", tags=["Employee Analysis"])
app.include_router(client_router, prefix="/api/client", tags=["Client Analysis"])
app.include_router(download_router, prefix="/api/download", tags=["Download API"])
app.include_router(tool_calling_router, prefix="/api/v1", tags=["Tool Calling"])

# ✅ 기본 루트 엔드포인트
@app.get("/")
def root():
    return {"message": "🚀 RouterAgent API is running!"}

# 헬스 체크
@app.get("/health")
def health():
    return {"status": "ok"}

# API 경로 확인용
@app.get("/api-routes")
def get_api_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else []
            })
    return {"routes": routes}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("[FastAPI Server]")
    print("Running at: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("API Routes: http://localhost:8000/api-routes")
    print("Health Check: http://localhost:8000/health")
    print("Stop: Ctrl+C")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
