"""
최소 작동 서버 - 문제 격리를 위한 테스트
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    query: str

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """최소 기능 채팅"""
    return {
        "success": True,
        "response": f"Echo: {request.query}",
        "agent": "minimal_agent",
        "session_id": request.session_id
    }

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("\n" + "="*60)
    print("최소 작동 서버")
    print("포트: 8002 (기존 서버와 충돌 방지)")
    print("테스트: http://localhost:8002/api/chat")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8002)