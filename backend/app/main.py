from dotenv import load_dotenv
from pathlib import Path
import os

# .env 로드
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from .api.router_api import router
import logging

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

# ✅ API 라우터 등록
app.include_router(router, prefix="/api/v1", tags=["RouterAgent"])

# ✅ 기본 루트 엔드포인트
@app.get("/")
def root():
    return {"message": "🚀 RouterAgent API is running!"}
