from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Minimal server is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/user/login")
async def login(username: str = Form(...), password: str = Form(...)):
    print(f"Login attempt: {username}")
    
    if username == "admin@example.com" and password == "admin123456":
        return {
            "success": True,
            "message": "로그인 성공",
            "user": {
                "username": username,
                "role": "admin",
                "employee_id": "1"
            },
            "token": "dummy_token_12345"
        }
    else:
        return {"success": False, "message": "잘못된 사용자명 또는 비밀번호"}

if __name__ == "__main__":
    import uvicorn
    print("Starting minimal server on port 8010...")
    uvicorn.run(app, host="0.0.0.0", port=8010) 