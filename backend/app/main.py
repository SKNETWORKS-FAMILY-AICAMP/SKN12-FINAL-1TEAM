<<<<<<< HEAD
import sys
from pathlib import Path

# 경로 설정 - main.py가 어디서 실행되든 작동하도록
current_file = Path(__file__).resolve()
app_dir = current_file.parent  # backend/app
backend_dir = app_dir.parent    # backend

# backend를 Python 경로에 추가하여 app.* 형태로 import 가능하게 함
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

print(f"[PATH] Added to sys.path: {backend_dir}")
print(f"[PATH] Current working dir: {Path.cwd()}")

# 이제 일반적인 import 가능
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# .env 파일 로드
# 1. backend/app/.env 우선
# 2. 프로젝트 루트의 .env 
env_paths = [
    app_dir / ".env",
    backend_dir.parent / ".env"
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[ENV] Loaded .env from: {env_path}")
        break

# OPENAI_API_KEY 확인
if os.getenv("OPENAI_API_KEY"):
    print("[ENV] OPENAI_API_KEY is set")
else:
    print("[WARNING] OPENAI_API_KEY is not set")

# 이제 상대 경로 import 대신 app.으로 시작하는 import 사용
from app.api.router_api import router
print("[OK] router_api imported successfully")

app = FastAPI(title="Multi-Agent Router API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
=======
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# .env 로드 (현재 경로와 상위 경로에서 찾기)
current_env = Path(__file__).parent / ".env"
parent_env = Path(__file__).resolve().parents[2] / ".env"

if current_env.exists():
    load_dotenv(dotenv_path=current_env)
    print(f"✅ .env 로드됨: {current_env}")
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
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# 라우터 등록 - /api prefix로 통일
app.include_router(router, prefix="/api")
print("[OK] Router registered at /api")

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

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("[FastAPI Server]")
    print("Running at: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("API Routes: http://localhost:8000/api-routes")
    print("Health Check: http://localhost:8000/health")
    print("Stop: Ctrl+C")
    print("="*60 + "\n")
    
    # reload를 위해서는 문자열로 전달해야 함
    # 하지만 현재 경로 문제로 인해 reload 없이 실행
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # reload 비활성화
        log_level="info"
    )
=======
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
