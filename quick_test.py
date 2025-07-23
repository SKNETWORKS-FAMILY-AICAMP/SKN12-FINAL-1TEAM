import requests
import time

print("=== 빠른 API 테스트 ===")

# 3초 대기
print("서버 안정화를 위해 3초 대기...")
time.sleep(3)

try:
    # 1. 서버 헬스체크
    print("\n1. 서버 헬스체크...")
    response = requests.get("http://localhost:8000/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ 서버 정상")
    
    # 2. 메인 라우터 API 테스트
    print("\n2. 메인 라우터 API 테스트...")
    response = requests.post(
        "http://localhost:8000/api/router/router",
        json={"query": "직원 실적을 분석해주세요"},
        timeout=15
    )
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("   ✅ 라우터 API 성공!")
        print(f"   - 성공: {result.get('success')}")
        print(f"   - 에이전트: {result.get('agent')}")
        if result.get('needs_user_selection'):
            print("   - 사용자 선택 필요 (H2H 모드)")
            print(f"   - 가능한 에이전트: {result.get('available_agents')}")
        else:
            print(f"   - 응답: {result.get('response', '')[:100]}...")
    elif response.status_code == 404:
        print("   ❌ 404 오류 - 엔드포인트 찾을 수 없음")
    else:
        print(f"   ❌ 오류: {response.status_code}")
        print(f"   내용: {response.text}")

except Exception as e:
    print(f"❌ 연결 오류: {e}")

print("\n=== 테스트 완료 ===") 