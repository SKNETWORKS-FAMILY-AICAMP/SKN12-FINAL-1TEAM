#!/usr/bin/env python3
"""
라우터 시스템 통합 테스트 스크립트
각 에이전트별 분류 및 API 연결, fallback 시나리오 테스트
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = 'http://localhost:8000'

def print_separator(title: str):
    """구분선 출력"""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def test_api_call(url: str, data: Dict[str, Any], test_name: str) -> Dict[str, Any]:
    """API 호출 테스트"""
    print(f"\n📡 요청: {json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        result = response.json()
        
        print(f"✅ 응답 성공 (HTTP {response.status_code})")
        print(f"📄 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return result
        
    except requests.exceptions.ConnectionError:
        print("❌ 연결 실패: 서버가 실행되지 않았습니다")
        return {"error": "connection_failed"}
    except requests.exceptions.Timeout:
        print("❌ 타임아웃: 응답 시간 초과")
        return {"error": "timeout"}
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return {"error": str(e)}

def test_health_check():
    """서버 헬스 체크"""
    print_separator("서버 헬스 체크")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 서버가 정상적으로 실행 중입니다")
            print(f"📄 응답: {response.json()}")
            return True
        else:
            print(f"⚠️ 서버 응답 이상 (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ 서버 연결 실패: {str(e)}")
        return False

def test_employee_agent():
    """직원 분석 에이전트 테스트"""
    print_separator("직원 분석 에이전트 테스트")
    
    test_queries = [
        "최수아 직원의 실적을 분석해주세요",
        "직원 성과 평가를 해주세요",
        "사원 매출 현황을 알려주세요"
    ]
    
    for query in test_queries:
        result = test_api_call(
            f"{BASE_URL}/api/router/router",
            {"query": query},
            f"직원 질문: {query}"
        )
        
        if result.get("agent") == "employee_agent":
            print("✅ employee_agent로 올바르게 분류됨")
        else:
            print(f"❌ 잘못된 분류: {result.get('agent')}")
        
        time.sleep(1)

def test_client_agent():
    """거래처 분석 에이전트 테스트"""
    print_separator("거래처 분석 에이전트 테스트")
    
    test_queries = [
        "서울의료센터 거래처 분석해주세요",
        "고객 매출 현황을 알려주세요",
        "병원 거래 실적을 보여주세요"
    ]
    
    for query in test_queries:
        result = test_api_call(
            f"{BASE_URL}/api/router/router",
            {"query": query},
            f"거래처 질문: {query}"
        )
        
        if result.get("agent") == "client_agent":
            print("✅ client_agent로 올바르게 분류됨")
        else:
            print(f"❌ 잘못된 분류: {result.get('agent')}")
        
        time.sleep(1)

def test_docs_agent():
    """문서 생성/분류 에이전트 테스트"""
    print_separator("문서 생성/분류 에이전트 테스트")
    
    test_queries = [
        "보고서를 작성해주세요",
        "컴플라이언스 위반 여부를 검토해주세요",
        "영업 계획서를 생성해주세요"
    ]
    
    for query in test_queries:
        result = test_api_call(
            f"{BASE_URL}/api/router/router",
            {"query": query},
            f"문서 질문: {query}"
        )
        
        if result.get("agent") == "docs_agent":
            print("✅ docs_agent로 올바르게 분류됨")
        else:
            print(f"❌ 잘못된 분류: {result.get('agent')}")
        
        time.sleep(1)

def test_search_agent():
    """검색 에이전트 테스트"""
    print_separator("검색 에이전트 테스트")
    
    test_queries = [
        "사내 규정을 검색해주세요",
        "제품 정보를 찾아주세요",
        "교육 자료를 검색해주세요"
    ]
    
    for query in test_queries:
        result = test_api_call(
            f"{BASE_URL}/api/router/router",
            {"query": query},
            f"검색 질문: {query}"
        )
        
        if result.get("agent") == "search_agent":
            print("✅ search_agent로 올바르게 분류됨")
        else:
            print(f"❌ 잘못된 분류: {result.get('agent')}")
        
        time.sleep(1)

def test_fallback_and_h2h():
    """Fallback 및 H2H 모드 테스트"""
    print_separator("Fallback 및 H2H 모드 테스트")
    
    # 에이전트와 관련없는 애매한 질문들
    ambiguous_queries = [
        "안녕하세요",
        "날씨가 어때요?",
        "점심 뭐 먹을까요?",
        "오늘 기분이 좋네요",
        "컴퓨터가 느려요"
    ]
    
    for query in ambiguous_queries:
        print(f"\n🤔 애매한 질문 테스트: {query}")
        result = test_api_call(
            f"{BASE_URL}/api/router/router",
            {"query": query},
            f"애매한 질문: {query}"
        )
        
        # H2H 모드로 전환되었는지 확인
        if result.get("needs_user_selection"):
            print("✅ H2H 모드로 올바르게 전환됨")
            print(f"📋 사용 가능한 에이전트: {result.get('available_agents')}")
            
            # 사용자 선택 테스트
            print("\n👤 사용자 선택 시뮬레이션: client_agent 선택")
            selection_result = test_api_call(
                f"{BASE_URL}/api/router/select-agent",
                {
                    "query": query,
                    "selected_agent": "client_agent"
                },
                "사용자 선택"
            )
            
            if selection_result.get("agent") == "client_agent":
                print("✅ 사용자 선택이 올바르게 처리됨")
            else:
                print(f"❌ 사용자 선택 처리 실패: {selection_result.get('agent')}")
                
        else:
            print(f"❌ H2H 모드로 전환되지 않음. 분류 결과: {result.get('agent')}")
        
        time.sleep(1)

def main():
    """메인 테스트 실행"""
    print("🚀 라우터 시스템 통합 테스트 시작")
    
    # 1. 서버 헬스 체크
    if not test_health_check():
        print("\n❌ 서버가 실행되지 않았습니다. 테스트를 중단합니다.")
        print("💡 서버 실행: python run_server.py")
        sys.exit(1)
    
    # 2. 각 에이전트별 테스트
    test_employee_agent()
    test_client_agent() 
    test_docs_agent()
    test_search_agent()
    
    # 3. Fallback 및 H2H 테스트
    test_fallback_and_h2h()
    
    print_separator("테스트 완료")
    print("🎉 모든 테스트가 완료되었습니다!")
    print("📊 결과를 확인하여 시스템 동작 상태를 점검하세요.")

if __name__ == "__main__":
    main() 