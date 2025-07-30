"""
동적 에이전트 라우팅 테스트
"""
import requests
import json
import time

print("=== 동적 에이전트 라우팅 테스트 ===\n")

session_id = "test_dynamic_001"
base_url = "http://localhost:8000/api"

# 연속 대화 테스트
conversations = [
    "김철수 사원의 실적을 보여주세요",  # employee_agent 예상
    "그 사원이 담당하는 주요 병원은 어디인가요?",  # client_agent로 전환 예상
    "A병원의 매출 추이는 어떻게 되나요?",  # client_agent 유지 예상
    "월간 보고서 템플릿을 만들어주세요",  # create_document_agent로 전환 예상
    "영업본부 조직도를 보여주세요"  # employee_agent로 전환 예상
]

for i, query in enumerate(conversations, 1):
    print(f"\n[대화 {i}] {query}")
    
    try:
        response = requests.post(
            f"{base_url}/chat",
            json={"session_id": session_id, "query": query}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("needs_user_selection"):
                print("결과: 자동 분류 실패")
                print("사용 가능한 에이전트:", data.get('available_agents', []))
            else:
                agent = data.get('agent', 'unknown')
                print(f"선택된 에이전트: {agent}")
                print(f"응답: {data.get('response', '')[:100]}...")
                
        else:
            print(f"오류: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"연결 오류: {e}")
    
    time.sleep(1)  # API 호출 간격

# 세션 메시지 확인
print("\n\n=== 대화 이력 확인 ===")
try:
    response = requests.get(f"{base_url}/sessions/{session_id}/messages")
    if response.status_code == 200:
        data = response.json()
        print(f"총 메시지 수: {data.get('count', 0)}")
        
        messages = data.get('messages', [])
        # 최근 10개만 표시
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        for msg in recent_messages:
            role = msg.get('role', '')
            if role == 'user':
                print(f"\n👤 User: {msg.get('content', '')}")
            elif role == 'assistant':
                agent = msg.get('agent', 'unknown')
                content = msg.get('content', '')
                print(f"🤖 [{agent}]: {content[:80] if len(content) > 80 else content}...")
                
except Exception as e:
    print(f"이력 조회 오류: {e}")

print("\n=== 테스트 완료 ===")
print("에이전트가 대화 맥락에 따라 동적으로 변경되는지 확인하세요.")