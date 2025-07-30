from dotenv import load_dotenv
from pathlib import Path
import os
import sys

# 환경변수 및 경로 설정
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
backend_root = current_dir.parent

# sys.path 설정 (중복 방지)
paths_to_add = [str(project_root), str(backend_root), str(current_dir)]
for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)

# .env 로드
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    print(f"✅ .env 로드됨: {env_file}")
else:
    print("⚠️ .env 파일을 찾을 수 없습니다")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# 4개 기본 API 라우터 import (절대 import만 사용)
try:
    from app.api.router_api import router
    from app.api.docs_api import router as docs_router
    from app.api.employee_api import router as employee_router
    from app.api.client_api import router as client_router
    from app.api.download_api import router as download_router
    print("✅ 모든 API 라우터 import 성공")
except ImportError as e:
    print(f"❌ API import 오류: {e}")
    # 최소한의 더미 라우터로 fallback
    from fastapi import APIRouter
    router = APIRouter()
    docs_router = APIRouter()
    employee_router = APIRouter()
    client_router = APIRouter()
    download_router = APIRouter()
    
    # @router.get("/")
    # def dummy_router():
    #     return {"message": "Router API (더미 모드)"}
    
    # @docs_router.get("/")
    # def dummy_docs():
    #     return {"message": "Docs API (더미 모드)"}
    
    # @employee_router.get("/")
    # def dummy_employee():
    #     return {"message": "Employee API (더미 모드)"}
    
    # @client_router.get("/")
    # def dummy_client():
    #     return {"message": "Client API (더미 모드)"}
    
    # @download_router.get("/")
    # def dummy_download():
    #     return {"message": "Download API (더미 모드)"}

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# FastAPI 앱 생성
app = FastAPI(
    title="NaruTalk AI 챗봇 API",
    description="4개 에이전트 기반 AI 챗봇 시스템",
    version="2.0.0"
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4개 API 라우터 등록
app.include_router(router, prefix="/api/router", tags=["Router Agent"])
app.include_router(docs_router, prefix="/api/docs", tags=["Docs Agent"])
app.include_router(employee_router, prefix="/api/employee", tags=["Employee Agent"])
app.include_router(client_router, prefix="/api/client", tags=["Client Agent"])
app.include_router(download_router, prefix="/api/download", tags=["Download"])

# 기본 루트 엔드포인트
@app.get("/")
def root():
    return {
        "message": "🚀 NaruTalk AI 챗봇 API가 실행 중입니다!",
        "version": "2.0.0",
        "agents": [
            "Router Agent - 쿼리 라우팅",
            "Docs Agent - 문서 생성/분류", 
            "Employee Agent - 직원 실적 분석",
            "Client Agent - 고객 분석"
        ],
        "endpoints": {
            "router": "/api/router/router",
            "docs_classify": "/api/docs/classify",
            "docs_write": "/api/docs/write",
            "employee_analyze": "/api/employee/analyze",
            "client_analyze": "/api/client/analyze",
            "download": "/api/download/{filename}"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "시스템이 정상적으로 작동 중입니다.",
        "version": "2.0.0"
    }

# 프론트엔드에서 필요한 추가 API 엔드포인트들
@app.get("/api/chat-history")
def get_chat_history():
    return {"history": [], "message": "채팅 히스토리가 비어있습니다."}

@app.get("/api/current-agent/{session_id}")
def get_current_agent(session_id: str):
    return {"current_agent": "router", "session_id": session_id}

@app.post("/api/initial-agent-select")
def initial_agent_select(data: dict = None):
    return {"status": "success", "selected_agent": "router"}

@app.post("/api/chat")
def chat_endpoint(data: dict = None):
    return {"response": "라우터 에이전트가 응답합니다.", "agent": "router"}

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 NaruTalk AI 챗봇 백엔드 서버 시작")
    print("="*50)
    print(f"📱 서버 주소: http://localhost:8000")
    print(f"📚 API 문서: http://localhost:8000/docs")
    print(f"🔍 헬스 체크: http://localhost:8000/health")
    print(f"⏹️  서버 중지: Ctrl+C")
    print("="*50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)