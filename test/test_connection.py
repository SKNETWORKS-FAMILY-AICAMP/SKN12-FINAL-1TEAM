"""
백엔드 서버 연결 테스트 스크립트
- API 엔드포인트 확인
- CORS 설정 확인
- 서버 상태 확인
"""

import requests
import json
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8000"
FRONTEND_ORIGIN = "http://localhost:3000"

def test_health_check():
    """헬스 체크 API 테스트"""
    print("\n=== 1. Health Check API 테스트 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] 오류: {e}")
        return False

def test_cors_headers():
    """CORS 헤더 확인"""
    print("\n=== 2. CORS 헤더 테스트 ===")
    try:
        # OPTIONS 요청으로 CORS 확인
        headers = {
            'Origin': FRONTEND_ORIGIN,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{BASE_URL}/api/router/router", headers=headers)
        print(f"상태 코드: {response.status_code}")
        print(f"CORS 헤더:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] 오류: {e}")
        return False

def test_router_endpoint():
    """Router API 엔드포인트 테스트"""
    print("\n=== 3. Router API 엔드포인트 테스트 ===")
    try:
        # POST 요청
        headers = {
            'Content-Type': 'application/json',
            'Origin': FRONTEND_ORIGIN
        }
        data = {
            'session_id': f'test_session_{datetime.now().timestamp()}',
            'query': '김철수 사원의 실적을 알려줘'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",  # 변경된 경로
            headers=headers,
            json=data
        )
        
        print(f"상태 코드: {response.status_code}")
        print(f"응답 헤더 (CORS):")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"  {header}: {value}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n응답 데이터:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"응답 텍스트: {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] 오류: {e}")
        return False

def test_api_docs():
    """API 문서 접근 테스트"""
    print("\n=== 4. API 문서 테스트 ===")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"상태 코드: {response.status_code}")
        print(f"API 문서 접근 가능: {response.status_code == 200}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] 오류: {e}")
        return False

def test_from_frontend_perspective():
    """프론트엔드 관점에서 테스트 (fetch 시뮬레이션)"""
    print("\n=== 5. 프론트엔드 fetch 시뮬레이션 ===")
    try:
        # 프론트엔드에서 보내는 것과 동일한 요청
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:3000',
            'Referer': 'http://localhost:3000/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        data = {
            'session_id': 'frontend_test_session',
            'query': '테스트 질문입니다'
        }
        
        # ChatScreen.js에서 사용하는 것과 동일한 요청
        response = requests.post(
            'http://localhost:8000/api/chat',  # 변경된 경로
            headers=headers,
            json=data,
            timeout=10
        )
        
        print(f"상태 코드: {response.status_code}")
        print(f"응답 헤더:")
        for header, value in response.headers.items():
            print(f"  {header}: {value}")
        
        if response.status_code == 200:
            print(f"\n[OK] 응답 성공!")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"\n[FAIL] 응답 실패!")
            print(f"응답 본문: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] 연결 오류: 백엔드 서버가 실행 중이지 않습니다.")
        print(f"   서버 주소: http://localhost:8000")
        return False
    except requests.exceptions.Timeout as e:
        print(f"[ERROR] 타임아웃: 서버가 응답하지 않습니다.")
        return False
    except Exception as e:
        print(f"[ERROR] 기타 오류: {type(e).__name__}: {e}")
        return False

def check_server_running():
    """서버 실행 상태 확인"""
    print("\n=== 서버 상태 확인 ===")
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"[OK] 서버가 실행 중입니다 (포트 8000)")
        return True
    except:
        print(f"[FAIL] 서버가 실행 중이지 않습니다!")
        print(f"   다음 명령어로 서버를 실행하세요:")
        print(f"   cd backend && python app/main.py")
        return False

def main():
    print("="*50)
    print("백엔드 서버 연결 테스트")
    print("="*50)
    
    # 서버 실행 확인
    if not check_server_running():
        print("\n[WARNING] 서버가 실행되지 않아 테스트를 중단합니다.")
        return
    
    # 각 테스트 실행
    tests = [
        ("Health Check", test_health_check),
        ("CORS Headers", test_cors_headers),
        ("Router Endpoint", test_router_endpoint),
        ("API Docs", test_api_docs),
        ("Frontend Simulation", test_from_frontend_perspective)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n테스트 실행 중 오류: {e}")
            results.append((name, False))
    
    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약")
    print("="*50)
    for name, result in results:
        status = "[OK] 성공" if result else "[FAIL] 실패"
        print(f"{name}: {status}")
    
    # 디버깅 정보
    print("\n" + "="*50)
    print("디버깅 정보")
    print("="*50)
    print("1. 백엔드 서버 실행 명령:")
    print("   cd backend && python app/main.py")
    print("\n2. 프론트엔드 실행 명령:")
    print("   cd frontend && npm start")
    print("\n3. API 문서 확인:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    main()