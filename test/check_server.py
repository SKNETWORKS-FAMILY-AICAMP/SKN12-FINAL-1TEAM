"""
서버 상태 상세 확인
"""
import requests
import json

print("=== 서버 상태 상세 확인 ===\n")

# 1. 서버 기본 정보
try:
    # OpenAPI 문서에서 정보 추출
    response = requests.get("http://localhost:8000/openapi.json")
    if response.status_code == 200:
        api_info = response.json()
        print(f"서버 타이틀: {api_info['info']['title']}")
        print(f"등록된 경로:")
        for path, methods in api_info['paths'].items():
            for method in methods:
                print(f"  {method.upper()} {path}")
    print()
    
    # 2. 실제 요청 테스트
    print("=== 실제 요청 테스트 ===")
    
    # 간단한 채팅 요청
    data = {
        "session_id": "debug_test",
        "query": "테스트"
    }
    
    response = requests.post(
        "http://localhost:8000/api/chat",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"상태 코드: {response.status_code}")
    print(f"응답 헤더:")
    for key, value in response.headers.items():
        if key.lower() in ['content-type', 'server', 'date', 'access-control-allow-origin']:
            print(f"  {key}: {value}")
    
    print(f"\n응답 본문:")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(response.text)
        
except Exception as e:
    print(f"오류: {e}")

# 3. 디버그 정보
print("\n=== 디버그 정보 ===")
print("서버가 500 에러를 반환하면:")
print("1. 서버 터미널에서 에러 로그 확인")
print("2. router_graph 초기화 문제일 가능성 높음")
print("3. main.py가 최신 코드를 반영하지 않았을 수 있음")