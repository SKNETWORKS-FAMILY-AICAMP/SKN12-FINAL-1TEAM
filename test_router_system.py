"""
LangGraph 기반 라우터 시스템 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# ✅ .env 파일 명확히 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# ✅ 경로 중복 제거
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


from backend.app.services.router_agent import RouterAgent, StateGraphRouter

def test_basic_router():
    """기본 라우터 테스트"""
    print("🧪 기본 라우터 테스트 시작")
    print("="*60)
    
    router = RouterAgent()
    
    test_queries = [
        "김철수 직원의 이번 달 실적을 분석해주세요",
        "ABC 거래처의 매출 현황을 알려주세요", 
        "회사 휴가 규정을 검색해주세요",
        "영업비밀보호서약서를 자동으로 생성해주세요"
    ]
    
    for query in test_queries:
        print(f"\n🔍 테스트 쿼리: {query}")
        result = router.process_query(query)
        print(f"📊 결과: {result}")
        print("-"*60)

def test_state_graph_router():
    """StateGraph 라우터 테스트"""
    print("\n🧪 StateGraph 라우터 테스트 시작")
    print("="*60)
    
    state_router = StateGraphRouter()
    
    # 그래프 시각화 출력
    print(state_router.get_graph_visualization())
    
    test_queries = [
        "김철수 직원의 이번 달 실적을 분석해주세요",
        "ABC 거래처의 매출 현황을 알려주세요"
    ]
    
    for query in test_queries:
        print(f"\n🔍 StateGraph 테스트 쿼리: {query}")
        result = state_router.process_query(query)
        print(f"📊 StateGraph 결과: {result}")
        print("-"*60)

if __name__ == "__main__":
    # OpenAI API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   export OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    print("🚀 LangGraph 기반 라우터 시스템 테스트")
    print("="*60)
    
    try:
        # 기본 라우터 테스트
        test_basic_router()
        
        # StateGraph 라우터 테스트
        test_state_graph_router()
        
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc() 