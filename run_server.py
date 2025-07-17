import uvicorn
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

if __name__ == "__main__":
    # OPENAI_API_KEY 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        exit(1)
    
    print(f"✅ OPENAI_API_KEY 로드됨: {api_key[:10]}...")
    
    # FastAPI 서버 실행
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 