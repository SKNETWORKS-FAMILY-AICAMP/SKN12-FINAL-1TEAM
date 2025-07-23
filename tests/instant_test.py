import requests
import json

BASE_URL = 'http://localhost:8000'

def test_now():
    print("🧪 라우터 시스템 즉시 테스트\n")
    
    # 1. 헬스 체크
    try:
        health = requests.get(f'{BASE_URL}/health', timeout=3)
        print("✅ 서버 연결 성공!")
        print(f"   상태: {health.status_code}")
        print(f"   응답: {health.json()}\n")
    except:
        print("❌ 서버 연결 실패\n")
        return

    # 2. 직원 분석 테스트
    print("🧪 테스트 1: 직원 분석")
    try:
        response = requests.post(f'{BASE_URL}/api/router/router', 
                               json={'query': '최수아 직원의 실적을 분석해주세요'}, 
                               timeout=10)
        result = response.json()
        print(f"   🎯 에이전트: {result.get('agent')}")
        print(f"   ✅ 성공: {result.get('success')}")
        if result.get('error'):
            print(f"   ❌ 오류: {result.get('error')}")
        else:
            print("   📄 API 호출 완료!")
        print()
    except Exception as e:
        print(f"   ❌ 실패: {str(e)}\n")

    # 3. 거래처 분석 테스트  
    print("🧪 테스트 2: 거래처 분석")
    try:
        response = requests.post(f'{BASE_URL}/api/router/router', 
                               json={'query': '서울의료센터 거래처를 분석해주세요'}, 
                               timeout=10)
        result = response.json()
        print(f"   🎯 에이전트: {result.get('agent')}")
        print(f"   ✅ 성공: {result.get('success')}")
        if result.get('error'):
            print(f"   ❌ 오류: {result.get('error')}")
        else:
            print("   📄 API 호출 완료!")
        print()
    except Exception as e:
        print(f"   ❌ 실패: {str(e)}\n")

    # 4. 문서 생성 테스트
    print("🧪 테스트 3: 문서 생성")
    try:
        response = requests.post(f'{BASE_URL}/api/router/router', 
                               json={'query': '영업 보고서를 작성해주세요'}, 
                               timeout=10)
        result = response.json()
        print(f"   🎯 에이전트: {result.get('agent')}")
        print(f"   ✅ 성공: {result.get('success')}")
        if result.get('error'):
            print(f"   ❌ 오류: {result.get('error')}")
        else:
            print("   📄 API 호출 완료!")
        print()
    except Exception as e:
        print(f"   ❌ 실패: {str(e)}\n")

    # 5. H2H 테스트
    print("🧪 테스트 4: H2H 모드 (애매한 질문)")
    try:
        response = requests.post(f'{BASE_URL}/api/router/router', 
                               json={'query': '안녕하세요 날씨가 좋네요'}, 
                               timeout=10)
        result = response.json()
        print(f"   🎯 에이전트: {result.get('agent')}")
        print(f"   ✅ 성공: {result.get('success')}")
        
        if result.get('needs_user_selection'):
            print("   🤖 H2H 모드로 전환됨!")
            
            # 사용자 선택 테스트
            print("   👤 사용자 선택: client_agent")
            selection = requests.post(f'{BASE_URL}/api/router/select-agent',
                                    json={
                                        'query': '안녕하세요 날씨가 좋네요',
                                        'selected_agent': 'client_agent'
                                    },
                                    timeout=10)
            sel_result = selection.json()
            print(f"   🎯 최종 에이전트: {sel_result.get('agent')}")
            print(f"   ✅ 선택 처리: {sel_result.get('success')}")
        else:
            print(f"   ❌ H2H 전환 실패: {result.get('agent')}")
        print()
    except Exception as e:
        print(f"   ❌ 실패: {str(e)}\n")

    print("🎉 테스트 완료!")

if __name__ == "__main__":
    test_now() 