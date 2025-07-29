"""
Fallback 및 H2H 테스트
"""
import requests
import json

print("=== Fallback 및 H2H 테스트 ===\n")

# 테스트 케이스 - 시스템과 관련 없는 질문들
test_cases = [
    # 정상 케이스
    ("김철수 사원의 실적 보여줘", True),
    ("A병원 정보 조회", True),
    
    # 관련 없는 케이스 (fallback 예상)
    ("안녕하세요", False),
    ("오늘 날씨 어때?", False),
    ("피자 주문하고 싶어", False),
    ("1+1은 뭐야?", False),
    ("ㅁㄴㅇㄹ", False),  # 오타
    ("asdfasdf", False),  # 의미없는 텍스트
]

session_id = "test_fallback_001"

for query, should_classify in test_cases:
    print(f"\n[테스트] {query}")
    print(f"예상: {'분류 성공' if should_classify else 'H2H 필요'}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"session_id": session_id, "query": query}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("needs_user_selection"):
                print("결과: [X] H2H 필요 (수동 선택)")
                print(f"시도 횟수: {data.get('routing_attempts', 0)}")
                print(f"메시지: {data.get('message', '')[:100]}...")
            else:
                agent = data.get('agent', 'unknown')
                print(f"결과: [O] 자동 분류 성공 → {agent}")
                
            # 예상과 실제가 일치하는지 확인
            actual_classified = not data.get("needs_user_selection", False)
            if actual_classified == should_classify:
                print("평가: [정확]")
            else:
                print("평가: [부정확]")
                
        else:
            print(f"오류: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"연결 오류: {e}")

print("\n\n=== 수동 선택 테스트 ===")
# H2H 상황에서 수동으로 에이전트 선택
print("\n질문: '안녕하세요'에 대해 employee_agent를 수동 선택")
try:
    response = requests.post(
        "http://localhost:8000/api/select-agent",
        json={
            "session_id": session_id,
            "query": "안녕하세요",
            "selected_agent": "employee_agent"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"결과: {data.get('success', False)}")
        print(f"응답: {data.get('response', '')[:100]}...")
    else:
        print(f"오류: HTTP {response.status_code}")
        
except Exception as e:
    print(f"연결 오류: {e}")

print("\n=== 테스트 완료 ===")
print("관련 없는 질문들이 H2H로 올바르게 처리되는지 확인하세요.")