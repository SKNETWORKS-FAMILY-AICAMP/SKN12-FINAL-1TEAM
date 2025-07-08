"""
QA Medical Agent 워크플로우 테스트
Mock API를 사용하여 전체 워크플로우를 테스트합니다.
"""

import sys
import os
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# 환경 변수 설정
exec(open('test_env.py', encoding='utf-8').read())

def create_mock_openai_response(content: str) -> Mock:
    """Mock OpenAI 응답 생성"""
    mock_response = Mock()
    mock_response.content = content
    return mock_response

def test_complete_workflow():
    """전체 워크플로우 테스트"""
    print("🚀 전체 워크플로우 테스트 시작")
    print("=" * 50)
    
    try:
        # Mock API 설정
        with patch('langchain_openai.ChatOpenAI') as mock_openai:
            # Mock GPT-4o-mini 응답 (의도 분류)
            mock_openai.return_value.invoke.side_effect = [
                create_mock_openai_response(
                    '{"intent": "sales_strategy", "confidence": 0.92, "keywords": ["의료기기", "영업", "병원"], "suggested_services": ["search", "analysis"]}'
                ),
                # Mock GPT-4o-mini 응답 (컨텍스트 향상)
                create_mock_openai_response(
                    "의료기기 영업에서는 병원과의 신뢰 관계가 가장 중요합니다. 의료진의 니즈를 정확히 파악하고, 제품의 안전성과 효과를 명확히 입증해야 합니다."
                ),
                # Mock GPT-4o 응답 (최종 답변)
                create_mock_openai_response(
                    '{"answer": "의료기기 영업에서는 다음과 같은 전략이 효과적입니다: 1) 의료진과의 신뢰 관계 구축 2) 제품의 안전성과 효과 입증 3) 맞춤형 솔루션 제공 4) 지속적인 사후 지원", "summary": "의료기기 영업 전략 가이드", "recommendations": ["신뢰 관계 중심 접근", "데이터 기반 제품 설명", "지속적 지원 체계"], "confidence": 0.89, "sources": ["내부 가이드라인", "업계 모범사례"]}'
                )
            ]
            
            # QA 에이전트 테스트
            from qa_agent.agent import run_agent
            
            test_query = "의료기기 영업 시 병원 구매담당자와 어떻게 소통해야 하나요?"
            print(f"📋 테스트 쿼리: {test_query}")
            print("-" * 30)
            
            result = run_agent(test_query, user_id="test_user", session_id="test_session")
            
            if result["success"]:
                print("✅ 워크플로우 성공!")
                print(f"🔍 신뢰도: {result['confidence']:.2f}")
                
                response = result["response"]
                print(f"📝 답변: {response.get('answer', 'N/A')[:200]}...")
                print(f"📊 요약: {response.get('summary', 'N/A')}")
                print(f"💡 권장사항: {response.get('recommendations', [])}")
                
                # 메타데이터 확인
                metadata = result.get("metadata", {})
                print(f"🔧 처리 단계: {metadata.get('step', 'N/A')}")
                
                return True
            else:
                print(f"❌ 워크플로우 실패: {result.get('error', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return False

def test_workflow_with_different_intents():
    """다양한 의도로 워크플로우 테스트"""
    print("\n🎯 다양한 의도 테스트 시작")
    print("=" * 50)
    
    test_cases = [
        {
            "query": "CT 스캐너 제품 사양을 알려주세요",
            "expected_intent": "product_info"
        },
        {
            "query": "의료기기 인증 절차는 어떻게 되나요?",
            "expected_intent": "regulatory"
        },
        {
            "query": "경쟁사 제품과 비교분석 결과를 보여주세요",
            "expected_intent": "market_analysis"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 케이스 {i}: {test_case['query']}")
        print(f"🎯 예상 의도: {test_case['expected_intent']}")
        
        try:
            with patch('langchain_openai.ChatOpenAI') as mock_openai:
                # Mock 응답 설정
                mock_openai.return_value.invoke.side_effect = [
                    create_mock_openai_response(
                        f'{{"intent": "{test_case["expected_intent"]}", "confidence": 0.88, "keywords": ["test"], "suggested_services": ["search"]}}'
                    ),
                    create_mock_openai_response("테스트 컨텍스트 향상 결과"),
                    create_mock_openai_response(
                        '{"answer": "테스트 답변", "summary": "테스트 요약", "recommendations": ["테스트 권장사항"], "confidence": 0.85, "sources": ["테스트 소스"]}'
                    )
                ]
                
                from qa_agent.agent import run_agent
                result = run_agent(test_case["query"])
                
                if result["success"]:
                    print("✅ 성공")
                    success_count += 1
                else:
                    print(f"❌ 실패: {result.get('error', 'Unknown')}")
                    
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    print(f"\n📊 결과: {success_count}/{len(test_cases)} 테스트 케이스 통과")
    return success_count == len(test_cases)

def test_error_handling():
    """오류 처리 테스트"""
    print("\n🛠️ 오류 처리 테스트 시작")
    print("=" * 50)
    
    try:
        # Mock API 오류 시뮬레이션
        with patch('langchain_openai.ChatOpenAI') as mock_openai:
            mock_openai.return_value.invoke.side_effect = Exception("API 연결 오류")
            
            from qa_agent.agent import run_agent
            result = run_agent("테스트 쿼리")
            
            if not result["success"] and result.get("error"):
                print("✅ 오류 처리 성공")
                print(f"🔍 오류 메시지: {result['error']}")
                return True
            else:
                print("❌ 오류 처리 실패")
                return False
                
    except Exception as e:
        print(f"❌ 오류 처리 테스트 중 예외: {e}")
        return False

def test_state_transitions():
    """상태 전이 테스트"""
    print("\n🔄 상태 전이 테스트 시작")
    print("=" * 50)
    
    try:
        from qa_agent.utils.state import AgentState
        from qa_agent.utils.nodes import extract_user_query, classify_intent
        from langchain_core.messages import HumanMessage
        
        # 초기 상태 생성
        initial_state = AgentState(
            messages=[HumanMessage(content="의료기기 영업 전략")],
            user_query="",
            intent=None,
            search_results=[],
            enhanced_context=None,
            final_response=None,
            confidence_score=None,
            metadata={},
            error=None
        )
        
        # 1단계: 쿼리 추출
        state = extract_user_query(initial_state)
        print(f"✅ 1단계 - 쿼리 추출: {state['user_query']}")
        
        # 2단계: 의도 분류 (Mock)
        with patch('langchain_openai.ChatOpenAI') as mock_openai:
            mock_openai.return_value.invoke.return_value = create_mock_openai_response(
                '{"intent": "sales_strategy", "confidence": 0.85, "keywords": ["의료기기", "영업"], "suggested_services": ["search"]}'
            )
            
            state = classify_intent(state)
            print(f"✅ 2단계 - 의도 분류: {state['intent']['intent']}")
        
        print("✅ 상태 전이 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 상태 전이 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🏥 QA Medical Agent 워크플로우 테스트")
    print("=" * 60)
    
    tests = [
        ("전체 워크플로우", test_complete_workflow),
        ("다양한 의도", test_workflow_with_different_intents),
        ("오류 처리", test_error_handling),
        ("상태 전이", test_state_transitions)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} 테스트 중 예외: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 워크플로우 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    for name, success in results:
        status = "✅ 통과" if success else "❌ 실패"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    print(f"\n총 {len(results)}개 테스트 중 {passed}개 통과")
    
    if passed == len(results):
        print("🎉 모든 워크플로우 테스트 통과!")
        return True
    else:
        print("⚠️ 일부 테스트 실패 - 워크플로우 점검 필요")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 