"""
최종 테스트 - 수정된 서버 확인
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("="*60)
print("최종 연결 테스트")
print("="*60)

# 1. 헬스 체크
print("\n[1] 서버 상태 확인")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   상태: {response.status_code}")
    print(f"   응답: {response.json()}")
except Exception as e:
    print(f"   실패: {e}")
    print("   → 서버가 실행되지 않았습니다!")
    exit(1)

# 2. API 라우트 확인
print("\n[2] API 경로 확인")
try:
    response = requests.get(f"{BASE_URL}/api/test")
    print(f"   /api/test 상태: {response.status_code}")
    if response.status_code == 200:
        print(f"   응답: {response.json()}")
except:
    print("   /api/test 없음 (정상)")

# 3. 채팅 API 테스트
print("\n[3] 채팅 API 테스트")
test_cases = [
    {"query": "안녕하세요", "expected": "일반"},
    {"query": "김철수 사원의 실적을 알려줘", "expected": "employee_agent"},
    {"query": "A병원 고객 정보 조회", "expected": "client_agent"},
    {"query": "아스피린 검색", "expected": "search_agent"},
    {"query": "보고서 문서 작성", "expected": "create_document_agent"}
]

for i, test in enumerate(test_cases):
    print(f"\n   테스트 {i+1}: {test['query']}")
    try:
        data = {
            "session_id": f"test_{i}",
            "query": test["query"]
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=data)
        print(f"   상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   성공: {result.get('success', False)}")
            print(f"   에이전트: {result.get('agent', 'N/A')}")
            print(f"   응답: {result.get('response', 'N/A')[:50]}...")
        else:
            print(f"   오류: {response.text}")
    except Exception as e:
        print(f"   실패: {e}")

# 4. CORS 확인
print("\n[4] CORS 설정 확인")
try:
    headers = {
        'Origin': 'http://localhost:3000',
        'Content-Type': 'application/json'
    }
    data = {"session_id": "cors_test", "query": "CORS 테스트"}
    response = requests.post(f"{BASE_URL}/api/chat", json=data, headers=headers)
    
    print(f"   상태: {response.status_code}")
    cors_headers = ['access-control-allow-origin', 'access-control-allow-credentials']
    for header in cors_headers:
        value = response.headers.get(header, 'Not set')
        print(f"   {header}: {value}")
except Exception as e:
    print(f"   실패: {e}")

print("\n" + "="*60)
print("테스트 완료!")
print("모든 테스트가 성공하면 프론트엔드에서도 작동합니다.")
print("="*60)