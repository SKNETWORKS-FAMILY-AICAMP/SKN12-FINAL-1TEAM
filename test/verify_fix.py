"""
수정 사항 검증
"""
import requests
import json

print("=== 수정 사항 검증 ===\n")

# 1. 테스트 엔드포인트
print("[1] 테스트 엔드포인트 확인")
try:
    response = requests.get("http://localhost:8000/api/test")
    print(f"상태: {response.status_code}")
    if response.status_code == 200:
        print(f"응답: {response.json()}")
        print("✓ 새로운 라우터가 로드되었습니다!")
    else:
        print("✗ 아직 이전 버전입니다")
except Exception as e:
    print(f"오류: {e}")

# 2. 채팅 테스트
print("\n[2] 채팅 기능 테스트")
test_messages = [
    "안녕하세요",
    "김철수 사원의 실적을 보여주세요",
    "A병원 고객 정보 검색",
    "월간 보고서 작성해줘"
]

for msg in test_messages:
    print(f"\n메시지: {msg}")
    try:
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"session_id": "test_session", "query": msg}
        )
        print(f"상태: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"성공: {data.get('success')}")
            print(f"에이전트: {data.get('agent')}")
            print(f"응답: {data.get('response')[:50]}...")
        else:
            print(f"오류: {response.text}")
    except Exception as e:
        print(f"오류: {e}")

# 3. CORS 확인
print("\n[3] CORS 헤더 확인")
try:
    response = requests.post(
        "http://localhost:8000/api/chat",
        json={"session_id": "cors_test", "query": "CORS 테스트"},
        headers={"Origin": "http://localhost:3000"}
    )
    print(f"상태: {response.status_code}")
    print("CORS 헤더:")
    for header in ['access-control-allow-origin', 'access-control-allow-credentials']:
        value = response.headers.get(header, 'Not set')
        print(f"  {header}: {value}")
        
    if 'access-control-allow-origin' in response.headers:
        print("✓ CORS가 올바르게 설정되었습니다!")
    else:
        print("✗ CORS 설정 문제")
        
except Exception as e:
    print(f"오류: {e}")

print("\n" + "="*50)
print("모든 테스트가 성공하면 프론트엔드도 작동합니다!")
print("브라우저에서 http://localhost:3000/chat 열고 테스트하세요.")
print("="*50)