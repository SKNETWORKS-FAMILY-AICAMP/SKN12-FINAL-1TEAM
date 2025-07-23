import requests
import json
import time
from datetime import datetime

def run_test():
    results = []
    results.append(f"🧪 라우터 시스템 테스트 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results.append("=" * 60)
    
    BASE_URL = 'http://localhost:8000'
    
    # 1. 서버 헬스 체크
    results.append("\n1️⃣ 서버 헬스 체크")
    try:
        health = requests.get(f'{BASE_URL}/health', timeout=5)
        results.append(f"✅ 서버 연결 성공! (HTTP {health.status_code})")
        results.append(f"   응답: {health.json()}")
        server_running = True
    except Exception as e:
        results.append(f"❌ 서버 연결 실패: {str(e)}")
        server_running = False
    
    if not server_running:
        results.append("\n⚠️ 서버가 실행되지 않아 테스트를 중단합니다.")
        with open("test_result.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        return
    
    # 2. 직원 분석 에이전트 테스트  
    results.append("\n2️⃣ 직원 분석 에이전트 테스트")
    try:
        response = requests.post(f'{BASE_URL}/api/router/router',
                               json={'query': '최수아 직원의 실적을 분석해주세요'},
                               timeout=15)
        result = response.json()
        results.append(f"   📡 요청: 최수아 직원의 실적을 분석해주세요")
        results.append(f"   🎯 분류된 에이전트: {result.get('agent')}")
        results.append(f"   ✅ 성공 여부: {result.get('success')}")
        if result.get('error'):
            results.append(f"   ❌ 오류: {result.get('error')}")
        if result.get('agent') == 'employee_agent':
            results.append("   ✅ 올바른 에이전트로 분류됨")
        else:
            results.append(f"   ❌ 잘못된 분류: {result.get('agent')}")
    except Exception as e:
        results.append(f"   ❌ 테스트 실패: {str(e)}")
    
    # 3. 거래처 분석 에이전트 테스트
    results.append("\n3️⃣ 거래처 분석 에이전트 테스트")
    try:
        response = requests.post(f'{BASE_URL}/api/router/router',
                               json={'query': '서울의료센터 거래처를 분석해주세요'},
                               timeout=15)
        result = response.json()
        results.append(f"   📡 요청: 서울의료센터 거래처를 분석해주세요")
        results.append(f"   🎯 분류된 에이전트: {result.get('agent')}")
        results.append(f"   ✅ 성공 여부: {result.get('success')}")
        if result.get('error'):
            results.append(f"   ❌ 오류: {result.get('error')}")
        if result.get('agent') == 'client_agent':
            results.append("   ✅ 올바른 에이전트로 분류됨")
        else:
            results.append(f"   ❌ 잘못된 분류: {result.get('agent')}")
    except Exception as e:
        results.append(f"   ❌ 테스트 실패: {str(e)}")
    
    # 4. 문서 생성 에이전트 테스트
    results.append("\n4️⃣ 문서 생성 에이전트 테스트")
    try:
        response = requests.post(f'{BASE_URL}/api/router/router',
                               json={'query': '영업 보고서를 작성해주세요'},
                               timeout=15)
        result = response.json()
        results.append(f"   📡 요청: 영업 보고서를 작성해주세요")
        results.append(f"   🎯 분류된 에이전트: {result.get('agent')}")
        results.append(f"   ✅ 성공 여부: {result.get('success')}")
        if result.get('error'):
            results.append(f"   ❌ 오류: {result.get('error')}")
        if result.get('agent') == 'docs_agent':
            results.append("   ✅ 올바른 에이전트로 분류됨")
        else:
            results.append(f"   ❌ 잘못된 분류: {result.get('agent')}")
    except Exception as e:
        results.append(f"   ❌ 테스트 실패: {str(e)}")
    
    # 5. H2H 모드 테스트 (애매한 질문)
    results.append("\n5️⃣ H2H 모드 테스트 (Fallback)")
    try:
        response = requests.post(f'{BASE_URL}/api/router/router',
                               json={'query': '안녕하세요 날씨가 좋네요'},
                               timeout=15)
        result = response.json()
        results.append(f"   📡 요청: 안녕하세요 날씨가 좋네요")
        results.append(f"   🎯 분류된 에이전트: {result.get('agent')}")
        results.append(f"   ✅ 성공 여부: {result.get('success')}")
        
        if result.get('needs_user_selection'):
            results.append("   ✅ H2H 모드로 올바르게 전환됨!")
            results.append(f"   📋 선택 가능한 에이전트: {result.get('available_agents')}")
            
            # 사용자 선택 테스트
            results.append("   👤 사용자 선택 테스트: client_agent 선택")
            selection = requests.post(f'{BASE_URL}/api/router/select-agent',
                                    json={
                                        'query': '안녕하세요 날씨가 좋네요',
                                        'selected_agent': 'client_agent'
                                    },
                                    timeout=15)
            sel_result = selection.json()
            results.append(f"   🎯 최종 선택된 에이전트: {sel_result.get('agent')}")
            results.append(f"   ✅ 선택 처리 성공: {sel_result.get('success')}")
            if sel_result.get('agent') == 'client_agent':
                results.append("   ✅ 사용자 선택이 올바르게 처리됨")
            else:
                results.append(f"   ❌ 사용자 선택 처리 실패: {sel_result.get('agent')}")
        else:
            results.append(f"   ❌ H2H 모드로 전환되지 않음. 분류 결과: {result.get('agent')}")
            results.append(f"   ⚠️ 3회 fallback 후 H2H 전환이 되어야 함")
    except Exception as e:
        results.append(f"   ❌ 테스트 실패: {str(e)}")
    
    # 결과 저장
    results.append(f"\n🎉 테스트 완료 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with open("test_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    
    # 화면 출력
    for line in results:
        print(line)

if __name__ == "__main__":
    run_test() 