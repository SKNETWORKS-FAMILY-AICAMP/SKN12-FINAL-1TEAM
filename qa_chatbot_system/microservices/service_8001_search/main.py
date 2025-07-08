"""
Search Service (Port 8001)
통합 검색 서비스 - FAISS + BGE + GPT-4o-mini
"""
import uvicorn
from app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 