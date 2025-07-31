"""
H2H 플로우 전체 테스트
"""
import requests
import json
import time

print("=== H2H 플로우 전체 테스트 ===\n")

session_id = "test_h2h_flow_001"
base_url = "http://localhost:8000/api"

# Step 1: 관련 없는 질문으로 H2H 트리거
print("[Step 1] 관련 없는 질문 입력")
query = "오늘 날씨 어때?"
print(f"질문: {query}")

response = requests.post(
    f"{base_url}/chat",
    json={"session_id": session_id, "query": query}
)

if response.status_code == 200:
    data = response.json()
    if data.get("needs_user_selection"):
        print("결과: H2H 활성화됨")
        message = data.get('message', '')
        # 인코딩 문제를 피하기 위해 ASCII 문자만 출력
        clean_message = ''.join(char if ord(char) < 128 else '?' for char in message)
        print(f"메시지: {clean_message[:200]}...")
        available_agents = data.get('available_agents', [])
        print(f"선택 가능한 에이전트: {available_agents}")
    else:
        print("오류: H2H가 활성화되지 않음")
        
# Step 2: 에이전트 선택 (예: employee_agent)
print("\n[Step 2] 에이전트 선택")
selected_agent = "employee_agent"
print(f"선택: {selected_agent}")

response = requests.post(
    f"{base_url}/select-agent",
    json={
        "session_id": session_id,
        "selected_agent": selected_agent,
        "query": ""  # 빈 질문으로 예시 받기
    }
)

if response.status_code == 200:
    data = response.json()
    if data.get("needs_new_question"):
        print("결과: 예시 질문 제공됨")
        print(f"메시지:\n{data.get('message', '')}")
        example_questions = data.get('example_questions', [])
        print("\n예시 질문:")
        for i, q in enumerate(example_questions, 1):
            print(f"  {i}. {q}")
    else:
        print("오류: 예시 질문이 제공되지 않음")

# Step 3: 예시 질문 중 하나 선택하여 실행
print("\n[Step 3] 예시 질문으로 에이전트 실행")
if example_questions:
    selected_question = example_questions[0]  # 첫 번째 예시 선택
    print(f"선택한 질문: {selected_question}")
    
    response = requests.post(
        f"{base_url}/select-agent",
        json={
            "session_id": session_id,
            "selected_agent": selected_agent,
            "query": selected_question
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and not data.get("needs_new_question"):
            print("결과: 에이전트 실행 성공")
            print(f"응답: {data.get('response', '')[:200]}...")
        else:
            print("오류: 에이전트 실행 실패")

# Step 4: 이후 정상 대화 가능한지 확인
print("\n[Step 4] 후속 대화 테스트")
follow_up = "김철수 사원의 작년 실적은?"
print(f"후속 질문: {follow_up}")

response = requests.post(
    f"{base_url}/chat",
    json={"session_id": session_id, "query": follow_up}
)

if response.status_code == 200:
    data = response.json()
    if not data.get("needs_user_selection"):
        print(f"결과: 자동 분류 성공 → {data.get('agent', 'unknown')}")
        print(f"응답: {data.get('response', '')[:100]}...")
    else:
        print("결과: 다시 H2H 필요")

print("\n=== 테스트 완료 ===")
print("H2H 플로우:")
print("1. 관련 없는 질문 → H2H 활성화")
print("2. 에이전트 선택 → 예시 질문 제공")
print("3. 예시 질문 선택 → 에이전트 실행")
print("4. 이후 정상 대화 가능")