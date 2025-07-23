from dotenv import load_dotenv
from pathlib import Path
import os
import sys

# 현재 파일의 부모 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir.parent))

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

# 절대 임포트로 변경
try:
    # 패키지 구조에서 실행될 때
    from .api.router_api import router
    from .api.docs_api import router as docs_router
    from .api.employee_api import router as employee_router
    from .api.client_api import router as client_router
    from .api.download_api import router as download_router
    from .api.fastapi_router_main import api_router as tool_calling_router
except ImportError:
    # 직접 실행될 때
    from app.api.router_api import router
    from app.api.docs_api import router as docs_router
    from app.api.employee_api import router as employee_router
    from app.api.client_api import router as client_router
    from app.api.download_api import router as download_router
    from app.api.fastapi_router_main import api_router as tool_calling_router

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)