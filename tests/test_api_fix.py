import requests
import json
import time

def test_api_endpoints():
    base_url = "http://localhost:8000"
    
    print("🧪 API 엔드포인트 테스트 시작 (수정된 경로)")
    print("=" * 60)
    
    # 1. 서버 상태 확인
    try:
        print("1. 서버 상태 확인...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ 서버 정상 작동")
            print(f"응답: {response.json()['message']}")
        else:
            print(f"❌ 서버 오류: {response.status_code}")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return
    
    # 2. 헬스 체크
    try:
        print("\n2. 헬스 체크...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ 헬스 체크 통과")
        else:
            print(f"❌ 헬스 체크 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 헬스 체크 연결 실패: {e}")
    
    # 3. 🔥 주요 수정된 라우터 API 테스트
    try:
        print("\n3. 🔥 메인 라우터 API 테스트 (/api/router/router)...")
        test_query = {"query": "직원 실적을 분석해주세요"}
        response = requests.post(
            f"{base_url}/api/router/router", 
            json=test_query,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   요청: POST {base_url}/api/router/router")
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 라우터 API 정상 작동!")
            result = response.json()
            print(f"   선택된 에이전트: {result.get('agent', 'N/A')}")
            print(f"   성공 여부: {result.get('success', 'N/A')}")
            if result.get('needs_user_selection'):
                print("   📋 사용자 선택 필요 - H2H 모드 진입")
                print(f"   가능한 에이전트: {result.get('available_agents', [])}")
            else:
                print(f"   응답 미리보기: {str(result.get('response', 'N/A'))[:100]}...")
        elif response.status_code == 404:
            print("❌ 404 오류 - 엔드포인트를 찾을 수 없음")
            print("   라우터 등록 문제 또는 경로 불일치")
        else:
            print(f"❌ 라우터 API 오류: {response.status_code}")
            print(f"   오류 내용: {response.text}")
    except Exception as e:
        print(f"❌ 라우터 API 연결 실패: {e}")
    
    # 4. 수정된 각 에이전트 API 테스트
    print("\n4. 개별 에이전트 API 테스트 (수정된 경로)...")
    
    # Employee API 테스트
    try:
        print("  - Employee API (/api/employee/analyze)...")
        response = requests.post(
            f"{base_url}/api/employee/analyze",
            json={"query": "김철수 직원의 2023년 실적을 분석해주세요"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"    상태 코드: {response.status_code}")
        if response.status_code == 200:
            print("    ✅ Employee API 정상")
        else:
            print(f"    ❌ Employee API 오류: {response.status_code}")
            print(f"    오류 내용: {response.text[:200]}...")
    except Exception as e:
        print(f"    ❌ Employee API 연결 실패: {e}")
    
    # Client API 테스트
    try:
        print("  - Client API (/api/client/analyze)...")
        response = requests.post(
            f"{base_url}/api/client/analyze",
            json={"query": "서울병원 거래처 분석을 해주세요"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"    상태 코드: {response.status_code}")
        if response.status_code == 200:
            print("    ✅ Client API 정상")
        else:
            print(f"    ❌ Client API 오류: {response.status_code}")
            print(f"    오류 내용: {response.text[:200]}...")
    except Exception as e:
        print(f"    ❌ Client API 연결 실패: {e}")
    
    # Docs API 테스트
    try:
        print("  - Docs API (/api/docs/classify)...")
        response = requests.post(
            f"{base_url}/api/docs/classify",
            json={"text": "영업 방문 보고서를 작성하겠습니다", "file_type": "auto"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"    상태 코드: {response.status_code}")
        if response.status_code == 200:
            print("    ✅ Docs API 정상")
        else:
            print(f"    ❌ Docs API 오류: {response.status_code}")
            print(f"    오류 내용: {response.text[:200]}...")
    except Exception as e:
        print(f"    ❌ Docs API 연결 실패: {e}")
    
    # 5. 에이전트 선택 API 테스트 (사용자 직접 선택)
    try:
        print("\n5. 에이전트 선택 API 테스트 (/api/router/select-agent)...")
        response = requests.post(
            f"{base_url}/api/router/select-agent",
            json={
                "query": "직원 분석을 해주세요",
                "selected_agent": "employee_agent"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            print("    ✅ 에이전트 선택 API 정상")
            result = response.json()
            print(f"    선택된 에이전트: {result.get('agent', 'N/A')}")
        else:
            print(f"    ❌ 에이전트 선택 API 오류: {response.status_code}")
    except Exception as e:
        print(f"    ❌ 에이전트 선택 API 연결 실패: {e}")
    
    print("\n" + "=" * 60)
    print("🧪 API 테스트 완료")
    print("\n📋 수정된 엔드포인트 목록:")
    print("  - /api/router/router (✅ 수정됨)")
    print("  - /api/employee/analyze (✅ 수정됨)")
    print("  - /api/client/analyze (✅ 수정됨)")
    print("  - /api/docs/classify (✅ 기존과 동일)")

if __name__ == "__main__":
    # 서버가 시작될 때까지 잠시 대기
    print("서버 시작까지 3초 대기...")
    time.sleep(3)
    test_api_endpoints() 