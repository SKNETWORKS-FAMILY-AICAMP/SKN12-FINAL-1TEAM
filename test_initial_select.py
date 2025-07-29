"""
초기 화면 에이전트 선택 테스트
"""
import requests
import json

print("=== 초기 화면 에이전트 선택 테스트 ===\n")

session_id = "test_initial_001"
base_url = "http://localhost:8000/api"

# Step 1: 초기 화면에서 에이전트 직접 선택
print("[Step 1] 초기 화면에서 employee_agent 선택")

response = requests.post(
    f"{base_url}/initial-agent-select",
    json={
        "session_id": session_id,
        "selected_agent": "employee_agent",
        "query": ""  # 초기 선택이므로 비어있음
    }
)

if response.status_code == 200:
    data = response.json()
    if data.get("needs_new_question"):
        print("결과: 예시 질문 제공됨")
        print(f"\n메시지:\n{data.get('message', '')}")
        example_questions = data.get('example_questions', [])
        print("\n받은 예시 질문:")
        for i, q in enumerate(example_questions, 1):
            print(f"  {i}. {q}")
    else:
        print("오류: 예시 질문이 제공되지 않음")
else:
    print(f"오류: HTTP {response.status_code}")

# Step 2: 예시 질문으로 실행
print("\n\n[Step 2] 예시 질문으로 에이전트 실행")
if 'example_questions' in locals() and example_questions:
    selected_question = example_questions[0]
    print(f"선택한 질문: {selected_question}")
    
    response = requests.post(
        f"{base_url}/chat",
        json={
            "session_id": session_id,
            "query": selected_question
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"결과: 자동 분류 → {data.get('agent', 'unknown')}")
        print(f"응답: {data.get('response', '')[:150]}...")
    else:
        print(f"오류: HTTP {response.status_code}")

# Step 3: 다른 에이전트도 초기 선택 가능한지 확인
print("\n\n[Step 3] 다른 에이전트들도 테스트")
other_agents = ["client_agent", "search_agent", "create_document_agent"]

for agent in other_agents:
    print(f"\n{agent} 선택:")
    response = requests.post(
        f"{base_url}/initial-agent-select",
        json={
            "session_id": f"test_{agent}",
            "selected_agent": agent,
            "query": ""
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("needs_new_question"):
            print(f"[O] 성공 - 예시 질문 {len(data.get('example_questions', []))}개 제공됨")
        else:
            print("[X] 실패")
    else:
        print(f"[X] 오류: HTTP {response.status_code}")

print("\n=== 테스트 완료 ===")
print("초기 화면에서도 에이전트를 직접 선택할 수 있습니다!")