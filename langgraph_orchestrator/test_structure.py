"""
QA Medical Agent 구조 테스트
API 키 없이도 기본적인 임포트와 구조를 테스트
"""

import sys
import os
from pathlib import Path

# 환경 변수 설정
exec(open('test_env.py', encoding='utf-8').read())

def test_imports():
    """기본 임포트 테스트"""
    print("📦 임포트 테스트 시작...")
    
    try:
        # LangGraph 관련 임포트
        from langgraph.graph import StateGraph, START, END
        print("✅ LangGraph 임포트 성공")
        
        # LangChain 관련 임포트
        from langchain_core.messages import HumanMessage, AIMessage
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic
        print("✅ LangChain 임포트 성공")
        
        # 프로젝트 모듈 임포트
        from qa_agent.utils.state import AgentState
        from qa_agent.utils.tools import search_medical_documents
        from qa_agent.utils.nodes import extract_user_query
        print("✅ 프로젝트 모듈 임포트 성공")
        
        # 메인 에이전트 임포트
        from qa_agent.agent import create_graph, run_agent
        print("✅ 메인 에이전트 임포트 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 임포트 실패: {e}")
        return False


def test_state_structure():
    """상태 구조 테스트"""
    print("\n🏗️ 상태 구조 테스트 시작...")
    
    try:
        from qa_agent.utils.state import AgentState
        from langchain_core.messages import HumanMessage
        
        # 기본 상태 생성
        state = AgentState(
            messages=[HumanMessage(content="테스트 메시지")],
            user_query="테스트 쿼리",
            intent=None,
            search_results=[],
            enhanced_context=None,
            final_response=None,
            confidence_score=None,
            metadata={"test": True},
            error=None
        )
        
        print("✅ AgentState 생성 성공")
        print(f"✅ 메시지 개수: {len(state['messages'])}")
        print(f"✅ 쿼리: {state['user_query']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 상태 구조 테스트 실패: {e}")
        return False


def test_tools():
    """도구 테스트"""
    print("\n🔧 도구 테스트 시작...")
    
    try:
        from qa_agent.utils.tools import (
            search_medical_documents,
            get_medical_industry_context,
            validate_medical_response,
            format_medical_response
        )
        
        # 의료 문서 검색 테스트
        search_result = search_medical_documents.invoke("의료기기 영업")
        print(f"✅ 검색 결과 개수: {len(search_result)}")
        
        # 업계 컨텍스트 테스트
        context = get_medical_industry_context.invoke({})
        print(f"✅ 업계 컨텍스트 키: {list(context.keys())}")
        
        # 응답 검증 테스트
        validation = validate_medical_response.invoke("의료기기 영업에는 병원과의 신뢰 관계가 중요합니다")
        print(f"✅ 검증 결과: {validation['is_valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 도구 테스트 실패: {e}")
        return False


def test_nodes():
    """노드 테스트"""
    print("\n🎯 노드 테스트 시작...")
    
    try:
        from qa_agent.utils.nodes import extract_user_query
        from qa_agent.utils.state import AgentState
        from langchain_core.messages import HumanMessage
        
        # 쿼리 추출 노드 테스트
        initial_state = AgentState(
            messages=[HumanMessage(content="의료기기 영업 전략을 알려주세요")],
            user_query="",
            intent=None,
            search_results=[],
            enhanced_context=None,
            final_response=None,
            confidence_score=None,
            metadata={},
            error=None
        )
        
        result_state = extract_user_query(initial_state)
        print(f"✅ 추출된 쿼리: {result_state['user_query']}")
        print(f"✅ 메타데이터: {result_state['metadata']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 노드 테스트 실패: {e}")
        return False


def test_graph_creation():
    """그래프 생성 테스트"""
    print("\n🕸️ 그래프 생성 테스트 시작...")
    
    try:
        from qa_agent.agent import create_graph
        
        # 그래프 생성 (컴파일 없이)
        graph = create_graph()
        print("✅ StateGraph 생성 성공")
        print(f"✅ 그래프 타입: {type(graph)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 그래프 생성 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("🚀 QA Medical Agent 구조 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("기본 임포트", test_imports),
        ("상태 구조", test_state_structure),
        ("도구 기능", test_tools),
        ("노드 기능", test_nodes),
        ("그래프 생성", test_graph_creation)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} 테스트 중 예외 발생: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    passed = 0
    for name, success in results:
        status = "✅ 통과" if success else "❌ 실패"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    print(f"\n총 {len(results)}개 테스트 중 {passed}개 통과")
    
    if passed == len(results):
        print("🎉 모든 구조 테스트 통과!")
        return True
    else:
        print("⚠️ 일부 테스트 실패 - 구조 점검 필요")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 