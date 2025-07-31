"""
최종 테스트 스크립트
"""
import requests
import json

print("=== NaruTalk 최종 테스트 ===\n")

# 테스트 케이스
test_cases = [
    ("김철수 사원의 실적을 보여주세요", "employee_agent"),
    ("A병원 고객 정보를 조회해주세요", "client_agent"),
    ("지난달 판매 데이터를 검색해줘", "search_agent"),
    ("월간 보고서를 작성해주세요", "create_document_agent"),
    ("안녕하세요", None)  # 분류 실패 예상
]

session_id = "test_session_001"

for query, expected_agent in test_cases:
    print(f"\n[테스트] {query}")
    print(f"예상 에이전트: {expected_agent or '분류 실패'}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"session_id": session_id, "query": query}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("needs_user_selection"):
                print("결과: 자동 분류 실패 - 수동 선택 필요")
                print(f"시도 횟수: {data.get('routing_attempts', 0)}")
                print("선택 가능한 에이전트:")
                for agent in data.get('available_agents', []):
                    print(f"  - {agent}: {data.get('agent_display_names', {}).get(agent, '')}")
            else:
                print(f"결과: 성공")
                print(f"선택된 에이전트: {data.get('agent', 'unknown')}")
                print(f"응답: {data.get('response', '')[:100]}...")
                
        else:
            print(f"오류: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"연결 오류: {e}")

print("\n=== 테스트 완료 ===")
print("\n프론트엔드에서 http://localhost:3000/chat 접속하여 확인하세요.")