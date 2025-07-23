import requests
import time

print("⏰ 서버 시작 대기 중 (10초)...")
time.sleep(10)

try:
    print("🔍 서버 연결 테스트...")
    response = requests.get("http://localhost:8000/health", timeout=10)
    print(f"✅ 서버 연결 성공! 상태: {response.status_code}")
    print(f"응답: {response.json()}")
    
    print("\n🧪 라우터 테스트...")
    router_response = requests.post(
        "http://localhost:8000/api/router/router",
        json={"query": "최수아 직원 실적을 분석해주세요"},
        timeout=15
    )
    print(f"✅ 라우터 응답 성공! 상태: {router_response.status_code}")
    result = router_response.json()
    print(f"분류된 에이전트: {result.get('agent')}")
    print(f"성공 여부: {result.get('success')}")
    
except Exception as e:
    print(f"❌ 오류 발생: {str(e)}") 