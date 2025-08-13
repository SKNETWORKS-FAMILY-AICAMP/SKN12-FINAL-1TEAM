"""
에이전트 전용 FastAPI 서버 (포트 8000)
docs_agent, router_agent 등 에이전트 API를 제공합니다.
"""
import sys
from pathlib import Path

# 경로 설정
current_file = Path(__file__).resolve()
app_dir = current_file.parent  # backend/app
backend_dir = app_dir.parent    # backend

# backend를 Python 경로에 추가
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

print(f"[PATH] Added to sys.path: {backend_dir}")
print(f"[PATH] Current working dir: {Path.cwd()}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# .env 파일 로드
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

# FastAPI 앱 생성
app = FastAPI(title="Multi-Agent API Server", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Agent API 임포트
try:
    from app.api.router_api import router as router_api
    app.include_router(router_api, prefix="/api")
    print("[OK] Router API registered at /api")
except Exception as e:
    print(f"[ERROR] Failed to import router_api: {e}")

# Docs Agent API 임포트
try:
    from app.api.docs_agent_api import router as docs_router
    app.include_router(docs_router, prefix="/api")
    print("[OK] Docs agent API registered at /api/v1/docs")
except Exception as e:
    print(f"[ERROR] Failed to import docs_agent_api: {e}")

# 헬스 체크
@app.get("/health")
def health():
    return {"status": "ok", "server": "agent_server", "port": 8000}

# API 라우트 확인
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
    print("[Agent Server]")
    print("Running at: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("API Routes: http://localhost:8000/api-routes")
    print("Health Check: http://localhost:8000/health")
    print("Stop: Ctrl+C")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )