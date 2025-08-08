#!/usr/bin/env python3
"""
JWT 토큰을 사용한 검색 에이전트 예시
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[ENV] Loaded .env from: {env_path}")
else:
    print(f"[WARNING] .env file not found at: {env_path}")

from search_agent import create_search_agent
from run import run_sync

def example_with_jwt_token():
    """JWT 토큰을 사용한 검색 에이전트 예시"""
    
    # JWT 토큰 설정 (여러 방법)
    api_token = None
    
    # 방법 1: 명령행 인수에서 받기
    if len(sys.argv) > 1:
        api_token = sys.argv[1]
        print(f"✓ JWT 토큰이 명령행 인수로 제공되었습니다.")
    
    # 방법 2: 환경 변수에서 가져오기
    if not api_token:
        api_token = os.getenv("API_TOKEN")
        if api_token:
            print(f"✓ JWT 토큰이 환경 변수에서 로드되었습니다.")
    
    # 방법 3: 직접 설정
    if not api_token:
        # 여기에 실제 JWT 토큰을 입력하세요
        api_token = "your-jwt-token-here"
        print(f"⚠️ JWT 토큰이 직접 설정되었습니다. 실제 토큰으로 변경하세요.")
    
    if not api_token or api_token == "your-jwt-token-here":
        print("❌ 유효한 JWT 토큰이 제공되지 않았습니다.")
        print("사용법:")
        print("1. 명령행 인수: python example_with_token.py 'your-jwt-token'")
        print("2. 환경 변수: export API_TOKEN='your-jwt-token'")
        print("3. 코드 수정: api_token = 'your-jwt-token'")
        return
    
    print(f"🔐 JWT 토큰이 설정되었습니다: {api_token[:20]}...")
    
    # 검색 에이전트 생성
    print("\n=== 검색 에이전트 생성 ===")
    agent = create_search_agent(api_token=api_token)
    
    # 시스템 상태 확인
    health = agent.check_api_health()
    print(f"QA API 상태: {health.get('qa_api', {}).get('status', 'unknown')}")
    print(f"Search API 상태: {health.get('search_api', {}).get('status', 'unknown')}")
    
    # 테스트 질문들
    test_queries = [
        "근무 시간 관련 규정 알려줘",           # TextDocQA 예상
        "최수아 사원의 급여 내역 보여줘",       # HybridDocSearch 예상
        "2024년 상반기 거래처별 매출과 분석 자료", # HybridDocSearch 예상
        "리모트 워크에 대한 사내 공지 어디 있어?", # TextDocQA 예상
        "거래처 중 가장 매출이 높은 곳 알려줘",   # HybridDocSearch 예상
    ]
    
    print("\n=== 검색 테스트 ===")
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 테스트 {i}: {query} ---")
        
        try:
            # 동기식 실행
            result = run_sync(
                query=query,
                session_id=f"test-session-{i}",
                api_token=api_token
            )
            
            if result.get("success"):
                print(f"✅ 성공: {result.get('search_type', 'Unknown')}")
                print(f"📝 응답: {result.get('response', '')[:200]}...")
            else:
                print(f"❌ 실패: {result.get('response', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    print("\n=== 직접 API 호출 테스트 ===")
    
    # QA API 직접 호출
    print("\n--- QA API 테스트 ---")
    try:
        qa_result = agent.call_qa_api("회사 정책에 대해 알려주세요")
        print(f"QA 결과: {qa_result[:200]}...")
    except Exception as e:
        print(f"QA API 오류: {e}")
    
    # Hybrid Search API 직접 호출
    print("\n--- Hybrid Search API 테스트 ---")
    try:
        search_result = agent.call_hybrid_search_api("매출 데이터")
        print(f"Search 결과: {search_result[:200]}...")
    except Exception as e:
        print(f"Hybrid Search API 오류: {e}")

def example_without_token():
    """JWT 토큰 없이 QA API만 테스트"""
    print("\n=== JWT 토큰 없이 QA API만 테스트 ===")
    
    agent = create_search_agent()  # 토큰 없이
    
    try:
        result = agent.call_qa_api("회사 정책에 대해 알려주세요")
        print(f"QA API 결과: {result[:200]}...")
    except Exception as e:
        print(f"QA API 오류: {e}")

if __name__ == "__main__":
    print("🔍 JWT 토큰을 사용한 검색 에이전트 예시")
    print("=" * 50)
    
    # JWT 토큰이 제공되었는지 확인
    api_token = None
    if len(sys.argv) > 1:
        api_token = sys.argv[1]
    else:
        api_token = os.getenv("API_TOKEN")
    
    if api_token and api_token != "your-jwt-token-here":
        example_with_jwt_token()
    else:
        print("⚠️ JWT 토큰이 제공되지 않아 QA API만 테스트합니다.")
        example_without_token()
        print("\n💡 JWT 토큰을 제공하면 Hybrid Search API도 테스트할 수 있습니다.")
        print("사용법: python example_with_token.py 'your-jwt-token'") 