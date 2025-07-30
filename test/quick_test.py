"""
빠른 테스트 스크립트
"""
import requests

print("=== 간단한 API 테스트 ===\n")

# 1. 기본 테스트
print("[1] Simple API 테스트")
try:
    response = requests.get("http://localhost:8000/api/simple-test")
    print(f"상태: {response.status_code}")
    print(f"응답: {response.json()}")
except Exception as e:
    print(f"실패: {e}")

# 2. 채팅 테스트
print("\n[2] Simple Chat 테스트")
try:
    data = {
        "session_id": "test123",
        "query": "안녕하세요"
    }
    response = requests.post("http://localhost:8000/api/simple-chat", json=data)
    print(f"상태: {response.status_code}")
    print(f"응답: {response.json()}")
except Exception as e:
    print(f"실패: {e}")

print("\n테스트 완료!")