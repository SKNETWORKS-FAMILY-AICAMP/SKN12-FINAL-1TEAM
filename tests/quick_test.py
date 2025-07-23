#!/usr/bin/env python3
"""
라우터 시스템 빠른 테스트
"""

import requests
import json
import time

BASE_URL = 'http://localhost:8000'

def test_quick():
    print('🚀 라우터 시스템 빠른 테스트 시작\n')
    
    # 1. 서버 헬스 체크
    print('🔍 서버 상태 확인...')
    try:
        health = requests.get(f'{BASE_URL}/health', timeout=5)
        print(f'✅ 서버 정상: {health.json()}\n')
    except Exception as e:
        print(f'❌ 서버 연결 실패: {str(e)}')
        return

    # 2. 직원 분석 에이전트 테스트
    print('🧪 Test 1: 직원 분석 에이전트')
    try:
        response = requests.post(f'{BASE_URL}/api/router/router', 
                               json={'query': '최수아 직원의 실적을 분석해주세요'}, 
                               timeout=20)
        result = response.json()
        print(f'📡 요청: 최수아 직원의 실적을 분석해주세요')
        print(f'🎯 분류된 에이전트: {result.get("agent")}')
        print(f'✅ 성공 여부: {result.get("success")}')
        if result.get('response'):
            print(f'📄 응답: {result.get("response")[:200]}...')
        print('---')
    except Exception as e:
        print(f'❌ 테스트 1 실패: {str(e)}')

    # 3. 거래처 분석 에이전트 테스트
    print('\n🧪 Test 2: 거래처 분석 에이전트')
    try:
        response = requests.post(f'{BASE_URL}/api/router/router', 
                               json={'query': '서울의료센터 거래처를 분석해주세요'}, 
                               timeout=20)
        result = response.json()
        print(f'📡 요청: 서울의료센터 거래처를 분석해주세요')
        print(f'🎯 분류된 에이전트: {result.get("agent")}')
        print(f'✅ 성공 여부: {result.get("success")}')
        if result.get('response'):
            print(f'📄 응답: {result.get("response")[:200]}...')
        print('---')
    except Exception as e:
        print(f'❌ 테스트 2 실패: {str(e)}')

    # 4. 문서 분류 에이전트 테스트
    print('\n🧪 Test 3: 문서 분류 에이전트')
    try:
        response = requests.post(f'{BASE_URL}/api/router/router', 
                               json={'query': '영업 보고서를 작성해주세요'}, 
                               timeout=20)
        result = response.json()
        print(f'📡 요청: 영업 보고서를 작성해주세요')
        print(f'🎯 분류된 에이전트: {result.get("agent")}')
        print(f'✅ 성공 여부: {result.get("success")}')
        if result.get('response'):
            print(f'📄 응답: {result.get("response")[:200]}...')
        print('---')
    except Exception as e:
        print(f'❌ 테스트 3 실패: {str(e)}')

    # 5. Fallback 테스트 (애매한 질문)
    print('\n🧪 Test 4: Fallback -> H2H 모드 테스트')
    try:
        response = requests.post(f'{BASE_URL}/api/router/router', 
                               json={'query': '안녕하세요 날씨가 좋네요'}, 
                               timeout=20)
        result = response.json()
        print(f'📡 요청: 안녕하세요 날씨가 좋네요')
        print(f'🎯 분류된 에이전트: {result.get("agent")}')
        print(f'✅ 성공 여부: {result.get("success")}')
        
        if result.get("needs_user_selection"):
            print('🤖 H2H 모드로 전환됨!')
            print(f'📋 선택 가능한 에이전트: {result.get("available_agents")}')
            
            # 사용자 선택 시뮬레이션
            print('\n👤 사용자 선택 시뮬레이션: client_agent 선택')
            selection_response = requests.post(f'{BASE_URL}/api/router/select-agent',
                                             json={
                                                 'query': '안녕하세요 날씨가 좋네요',
                                                 'selected_agent': 'client_agent'
                                             },
                                             timeout=20)
            selection_result = selection_response.json()
            print(f'🎯 선택된 에이전트: {selection_result.get("agent")}')
            print(f'✅ 처리 성공: {selection_result.get("success")}')
        else:
            print(f'❌ H2H 모드로 전환되지 않음: {result.get("agent")}')
        print('---')
    except Exception as e:
        print(f'❌ 테스트 4 실패: {str(e)}')

    print('\n🎉 빠른 테스트 완료!')

if __name__ == "__main__":
    test_quick() 