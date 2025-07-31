"""
최소 동작 테스트
백엔드 API가 정말로 작동하는지 단계별로 확인
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("="*60)
print("최소 동작 테스트")
print("="*60)

# 1. 서버 연결 확인
print("\n[1] 서버 연결 테스트")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=2)
    print(f"   결과: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"   실패: {e}")
    print("   → 서버가 실행되지 않았습니다!")
    exit(1)

# 2. 가장 단순한 POST 요청
print("\n[2] 빈 데이터로 POST 테스트")
try:
    response = requests.post(f"{BASE_URL}/api/chat", json={})
    print(f"   상태: {response.status_code}")
    print(f"   응답: {response.text[:200]}...")
except Exception as e:
    print(f"   실패: {e}")

# 3. 필수 필드만 포함한 요청
print("\n[3] 최소 데이터로 POST 테스트")
try:
    data = {
        "session_id": "test123",
        "query": "안녕하세요"
    }
    response = requests.post(f"{BASE_URL}/api/chat", json=data)
    print(f"   상태: {response.status_code}")
    if response.status_code == 200:
        print(f"   성공! 응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:200]}...")
    else:
        print(f"   응답: {response.text[:200]}...")
except Exception as e:
    print(f"   실패: {e}")

# 4. CORS 헤더 확인
print("\n[4] CORS 설정 확인")
try:
    headers = {
        'Origin': 'http://localhost:3000',
        'Content-Type': 'application/json'
    }
    response = requests.post(
        f"{BASE_URL}/api/chat", 
        json={"session_id": "test", "query": "test"},
        headers=headers
    )
    print(f"   상태: {response.status_code}")
    print("   CORS 헤더:")
    for header in ['access-control-allow-origin', 'access-control-allow-credentials']:
        value = response.headers.get(header, 'Not set')
        print(f"     {header}: {value}")
except Exception as e:
    print(f"   실패: {e}")

# 5. 서버 로그 확인 안내
print("\n[5] 서버 로그 확인")
print("   서버 터미널에서 다음을 확인하세요:")
print("   - ImportError나 ModuleNotFoundError가 있는가?")
print("   - router_graph 초기화 오류가 있는가?")
print("   - OPENAI_API_KEY 관련 오류가 있는가?")

print("\n" + "="*60)
print("테스트 완료")
print("="*60)