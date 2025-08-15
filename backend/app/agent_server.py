"""
에이전트 전용 FastAPI 서버 (포트 8000)
docs_agent, router_agent 등 에이전트 API를 제공합니다.
8010 포트의 database API (user, admin, documents)를 프록시합니다.
"""
import sys
from pathlib import Path
import httpx
from fastapi import Request, Response

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

# 중앙 설정 import
from app.core.config import config

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
if config.get_openai_api_key():
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
    app.include_router(router_api, prefix="/api/v1")
    print("[OK] Router API registered at /api/v1")
except Exception as e:
    print(f"[ERROR] Failed to import router_api: {e}")

# Docs Agent API 임포트
try:
    from app.api.docs_agent_api import router as docs_router
    app.include_router(docs_router, prefix="/api/v1/docs")
    print("[OK] Docs agent API registered at /api/v1/docs")
except Exception as e:
    print(f"[ERROR] Failed to import docs_agent_api: {e}")

# Employee Agent API 임포트
try:
    from app.api.employee_agent_api import router as employee_router
    app.include_router(employee_router, prefix="/api/employee")
    print("[OK] Employee agent API registered at /api/employee")
except Exception as e:
    print(f"[ERROR] Failed to import employee_agent_api: {e}")

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

# Database API 프록시 (8010 포트로 전달)
# user, admin, documents 등의 요청을 database API로 프록시
from fastapi.responses import StreamingResponse
import asyncio

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_to_database(path: str, request: Request):
    """
    /user/*, /admin/*, /documents/* 등의 요청을 
    fastapi-app:8000 (database API)로 프록시합니다.
    """
    # API 요청이 아닌 경우만 프록시 (api로 시작하지 않는 경로)
    if not path.startswith("api/") and not path in ["health", "api-routes", "docs", "openapi.json", "redoc"]:
        # Database API URL 구성
        database_url = f"{config.get_database_api_url()}/{path}"
        
        # 디버깅용 로그
        print(f"[PROXY] Path: {path}")
        print(f"[PROXY] Method: {request.method}")
        print(f"[PROXY] Headers: {dict(request.headers)}")
        
        # 요청 본문 읽기
        body = await request.body()
        print(f"[PROXY] Body length: {len(body)}")
        
        # 프록시하지 말아야 할 헤더들 필터링
        skip_headers = ['host', 'content-length', 'connection']
        filtered_headers = {
            k: v for k, v in request.headers.items() 
            if k.lower() not in skip_headers
        }
        
        # SSE 엔드포인트 확인
        is_sse = path.endswith('-sse') or 'upload-sse' in path
        
        if is_sse:
            # SSE를 위한 스트리밍 요청
            print(f"[PROXY] SSE 스트리밍 요청: {path}")
            
            async def generate_sse():
                # 클라이언트를 제너레이터 내부에서 생성
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                    try:
                        async with client.stream(
                            method=request.method,
                            url=database_url,
                            headers=filtered_headers,
                            content=body,
                            params=dict(request.query_params)
                        ) as response:
                            print(f"[PROXY] SSE 응답 상태: {response.status_code}")
                            print(f"[PROXY] SSE 응답 헤더: {dict(response.headers)}")
                            
                            if response.status_code != 200:
                                error_text = await response.aread()
                                yield error_text
                                return
                            
                            async for chunk in response.aiter_bytes():
                                if chunk:
                                    yield chunk
                    except Exception as e:
                        print(f"[PROXY] SSE 스트리밍 에러: {e}")
                        yield f"data: {{\"step\": \"error\", \"message\": \"프록시 에러: {str(e)}\"}}\n\n".encode()
            
            # SSE 응답 반환
            return StreamingResponse(
                generate_sse(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # 일반 요청 처리
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            try:
                response = await client.request(
                    method=request.method,
                    url=database_url,
                    headers=filtered_headers,
                    content=body,
                    params=dict(request.query_params)
                )
                
                # 응답 반환
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            except httpx.ConnectError:
                return Response(
                    content=b'{"detail": "Database API service is not available"}',
                    status_code=503,
                    headers={"content-type": "application/json"}
                )
            except Exception as e:
                import traceback
                error_detail = f"Proxy error: {str(e)}\n{traceback.format_exc()}"
                print(f"[PROXY ERROR] {error_detail}")
                return Response(
                    content=f'{{"detail": "Proxy error: {str(e)}"}}'.encode(),
                    status_code=500,
                    headers={"content-type": "application/json"}
                )
    
    # API 경로는 404 반환 (위의 라우터들이 처리하지 못한 경우)
    return Response(
        content=b'{"detail": "Not Found"}',
        status_code=404,
        headers={"content-type": "application/json"}
    )

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
        "app.agent_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 핫리로드 활성화
        log_level="info"
    )