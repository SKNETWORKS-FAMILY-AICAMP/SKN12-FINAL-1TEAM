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
from api.router_api import router
from api.docs_api import router as docs_router
from api.employee_api import router as employee_router
from api.client_api import router as client_router
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

# ✅ API 라우터 등록
app.include_router(router, prefix="/api/route", tags=["RouterAgent"])
app.include_router(docs_router, prefix="/api/docs", tags=["DocsAgent"])
app.include_router(employee_router, prefix="/api/employee", tags=["Employee Analysis"])
app.include_router(client_router, prefix="/api/client", tags=["Client Analysis"])

# ✅ 기본 루트 엔드포인트
@app.get("/")
def root():
    return {"message": "🚀 RouterAgent API is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)