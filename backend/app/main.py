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

# 통합 라우터 API import
try:
    from app.api.router_api import router
    print("✅ 통합 라우터 API import 성공")
except ImportError as e:
    print(f"❌ API import 오류: {e}")
    # 최소한의 더미 라우터로 fallback
    from fastapi import APIRouter
    router = APIRouter()
    
    @router.get("/")
    def dummy_router():
        return {"message": "Router API (더미 모드)"}

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# FastAPI 앱 생성
app = FastAPI(
    title="NaruTalk AI 통합 챗봇 API",
    description="LangGraph 기반 통합 에이전트 시스템",
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

# 통합 라우터 등록
app.include_router(router, prefix="/api/router", tags=["Unified Router"])

# 기본 루트 엔드포인트
@app.get("/")
def root():
    return {
        "message": "🚀 NaruTalk AI 통합 챗봇 API가 실행 중입니다!",
        "version": "2.0.0",
        "architecture": "LangGraph + FastAPI",
        "agents": [
            "Employee Agent - 직원 실적 분석",
            "Client Agent - 고객/거래처 분석", 
            "Create Document Agent - 문서 초안 작성",
            "Search Agent - 내부 데이터 검색"
        ],
        "unified_graph": True,
        "endpoints": {
            "main_router": "/api/router/router",
            "system_info": "/api/router/system-info",
            "agents_list": "/api/router/agents",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "통합 에이전트 시스템이 정상적으로 작동 중입니다.",
        "version": "2.0.0",
        "architecture": "LangGraph + FastAPI",
        "unified_graph": True
    }

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 NaruTalk AI 통합 챗봇 백엔드 서버 시작")
    print("="*50)
    print(f"📱 서버 주소: http://localhost:8000")
    print(f"📚 API 문서: http://localhost:8000/docs")
    print(f"🔍 헬스 체크: http://localhost:8000/health")
    print(f"🎯 통합 라우터: http://localhost:8000/api/router/router")
    print(f"⏹️  서버 중지: Ctrl+C")
    print("="*50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)