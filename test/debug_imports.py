"""
Import 디버깅 스크립트
main.py의 import 문제를 확인
"""

import sys
import os
from pathlib import Path

# backend 경로를 Python 경로에 추가
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

print("=== Import 디버깅 ===")
print(f"Python 경로: {sys.path[:3]}")
print(f"현재 디렉토리: {os.getcwd()}")
print(f"Backend 경로: {backend_path}")

try:
    print("\n1. app.api.router_api 임포트 시도...")
    from app.api.router_api import router
    print("   [OK] router_api 임포트 성공")
    
    # router 객체 확인
    print(f"\n2. Router 객체 정보:")
    print(f"   - 타입: {type(router)}")
    print(f"   - 라우트 수: {len(router.routes)}")
    
    # 각 라우트 정보
    print(f"\n3. 등록된 라우트:")
    for route in router.routes:
        if hasattr(route, 'path'):
            print(f"   - {route.methods} {route.path}")
    
except Exception as e:
    print(f"   [ERROR] 임포트 실패: {e}")
    import traceback
    traceback.print_exc()

# FastAPI 앱 생성 테스트
try:
    print("\n4. FastAPI 앱 생성 테스트...")
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/api/router")
    
    print("   [OK] 앱 생성 및 라우터 등록 성공")
    
    # 최종 경로 확인
    print(f"\n5. 최종 API 경로:")
    for route in app.routes:
        if hasattr(route, 'path') and route.path != "/openapi.json" and route.path != "/docs" and route.path != "/docs/oauth2-redirect" and route.path != "/redoc":
            print(f"   - {route.methods if hasattr(route, 'methods') else 'N/A'} {route.path}")
            
except Exception as e:
    print(f"   [ERROR] 앱 생성 실패: {e}")