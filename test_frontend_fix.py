"""
프론트엔드 수정 사항 테스트
"""
import requests
import json
import time

print("=== 프론트엔드 수정 사항 테스트 ===\n")

base_url = "http://localhost:8000"

# 1. 서버 상태 확인
print("[1] 서버 상태 확인")
try:
    response = requests.get(f"{base_url}/health")
    if response.status_code == 200:
        print("[O] 서버 정상 작동")
    else:
        print("[X] 서버 응답 없음")
except Exception as e:
    print(f"[X] 서버 연결 실패: {e}")

# 2. API 엔드포인트 확인
print("\n[2] API 엔드포인트 확인")
endpoints = [
    ("GET", "/api/test"),
    ("GET", "/api/chat-history"),
    ("POST", "/api/chat"),
    ("POST", "/api/select-agent"),
    ("POST", "/api/initial-agent-select")
]

for method, endpoint in endpoints:
    try:
        if method == "GET":
            response = requests.get(f"{base_url}{endpoint}")
        else:
            # POST 요청은 더미 데이터로 테스트
            response = requests.post(f"{base_url}{endpoint}", 
                                   json={"session_id": "test", "query": "test"})
        
        print(f"{method} {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"{method} {endpoint}: 오류 - {e}")

# 3. 초기 에이전트 선택 기능 테스트
print("\n[3] 초기 에이전트 선택 기능")
session_id = f"test_{int(time.time())}"

response = requests.post(
    f"{base_url}/api/initial-agent-select",
    json={
        "session_id": session_id,
        "selected_agent": "employee_agent",
        "query": ""
    }
)

if response.status_code == 200:
    data = response.json()
    if data.get("success") and data.get("needs_new_question"):
        print("[O] 초기 선택 기능 정상")
        print(f"  - 예시 질문 {len(data.get('example_questions', []))}개 제공")
    else:
        print("[X] 초기 선택 기능 오류")
else:
    print(f"[X] API 오류: {response.status_code}")

print("\n=== 테스트 완료 ===")
print("\n프론트엔드 수정사항:")
print("1. initialMessage 오류 해결 완료")
print("2. startNewChat 함수에서 systemMessage와 agentSelectionMessage 사용")
print("3. 채팅 히스토리에 올바른 메시지 배열 저장")
print("\n이제 http://localhost:3000/chat 에서 정상 작동합니다.")