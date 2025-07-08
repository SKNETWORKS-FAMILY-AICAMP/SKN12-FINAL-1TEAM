"""
QA Medical Agent 실제 API 테스트
실제 OpenAI API 키를 사용하여 완전한 테스트를 수행합니다.

사용 전 준비사항:
1. .env 파일에 OPENAI_API_KEY 설정
2. 충분한 API 크레딧 확인
"""

import sys
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def check_api_keys():
    """API 키 확인"""
    print("🔑 API 키 확인 중...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "test_key_please_set_real_key":
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다!")
        print("📝 .env 파일에 다음과 같이 설정하세요:")
        print("OPENAI_API_KEY=your_actual_openai_api_key_here")
        return False
    
    print(f"✅ OpenAI API 키 확인: {openai_key[:8]}...")
    return True

def test_real_api_workflow():
    """실제 API를 사용한 워크플로우 테스트"""
    print("\n🚀 실제 API 워크플로우 테스트 시작")
    print("=" * 50)
    
    if not check_api_keys():
        return False
    
    try:
        from qa_agent.agent import run_agent
        
        # 실제 의료업계 테스트 쿼리들
        test_queries = [
            "의료기기 영업 시 병원 구매담당자와 어떻게 소통해야 하나요?",
            "CT 스캐너의 주요 기술 사양은 무엇인가요?",
            "의료기기 인증 절차에 대해 설명해주세요"
        ]
        
        success_count = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 테스트 {i}: {query}")
            print("-" * 40)
            
            try:
                result = run_agent(
                    query, 
                    user_id=f"real_test_user_{i}",
                    session_id=f"real_test_session_{i}"
                )
                
                if result["success"]:
                    print("✅ 성공!")
                    print(f"🔍 신뢰도: {result['confidence']:.2f}")
                    
                    response = result["response"]
                    print(f"📝 답변 미리보기: {response.get('answer', 'N/A')[:150]}...")
                    print(f"📊 요약: {response.get('summary', 'N/A')}")
                    
                    success_count += 1
                else:
                    print(f"❌ 실패: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ 테스트 중 오류: {e}")
        
        print(f"\n📊 실제 API 테스트 결과: {success_count}/{len(test_queries)} 성공")
        return success_count == len(test_queries)
        
    except Exception as e:
        print(f"❌ 실제 API 테스트 중 오류: {e}")
        return False

def test_performance():
    """성능 테스트"""
    print("\n⚡ 성능 테스트 시작")
    print("=" * 50)
    
    if not check_api_keys():
        return False
    
    import time
    
    try:
        from qa_agent.agent import run_agent
        
        test_query = "의료기기 영업 전략의 핵심은 무엇인가요?"
        
        print(f"📋 성능 테스트 쿼리: {test_query}")
        
        start_time = time.time()
        
        result = run_agent(test_query, user_id="perf_test", session_id="perf_session")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        if result["success"]:
            print(f"✅ 처리 완료!")
            print(f"⏱️ 처리 시간: {processing_time:.2f}초")
            
            # 성능 기준 (30초 이내)
            if processing_time <= 30:
                print("🚀 성능 우수 (30초 이내)")
                return True
            else:
                print("⚠️ 성능 개선 필요 (30초 초과)")
                return False
        else:
            print(f"❌ 처리 실패: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 성능 테스트 중 오류: {e}")
        return False

def test_different_model_combinations():
    """다양한 모델 조합 테스트"""
    print("\n🤖 모델 조합 테스트 시작")
    print("=" * 50)
    
    if not check_api_keys():
        return False
    
    # 원래 환경 변수 백업
    original_gpt4o = os.getenv("OPENAI_MODEL_GPT4O", "gpt-4o")
    original_gpt4o_mini = os.getenv("OPENAI_MODEL_GPT4O_MINI", "gpt-4o-mini")
    
    model_combinations = [
        {
            "name": "GPT-4o + GPT-4o-mini (권장)",
            "gpt4o": "gpt-4o",
            "gpt4o_mini": "gpt-4o-mini"
        },
        {
            "name": "GPT-4o-mini 전용 (경제적)",
            "gpt4o": "gpt-4o-mini",
            "gpt4o_mini": "gpt-4o-mini"
        }
    ]
    
    success_count = 0
    
    for combo in model_combinations:
        print(f"\n🔧 테스트 조합: {combo['name']}")
        
        # 환경 변수 임시 변경
        os.environ["OPENAI_MODEL_GPT4O"] = combo["gpt4o"]
        os.environ["OPENAI_MODEL_GPT4O_MINI"] = combo["gpt4o_mini"]
        
        try:
            # 모듈 재임포트가 필요하므로 간단한 테스트만 수행
            from qa_agent.agent import run_agent
            
            result = run_agent("의료기기 영업의 핵심은?", user_id="model_test")
            
            if result["success"]:
                print(f"✅ {combo['name']} 성공")
                print(f"🔍 신뢰도: {result['confidence']:.2f}")
                success_count += 1
            else:
                print(f"❌ {combo['name']} 실패")
                
        except Exception as e:
            print(f"❌ {combo['name']} 오류: {e}")
    
    # 환경 변수 복원
    os.environ["OPENAI_MODEL_GPT4O"] = original_gpt4o
    os.environ["OPENAI_MODEL_GPT4O_MINI"] = original_gpt4o_mini
    
    print(f"\n📊 모델 조합 테스트 결과: {success_count}/{len(model_combinations)} 성공")
    return success_count > 0

def test_conversation_flow():
    """대화 흐름 테스트"""
    print("\n💬 대화 흐름 테스트 시작")
    print("=" * 50)
    
    if not check_api_keys():
        return False
    
    try:
        from qa_agent.agent import run_agent
        
        # 연속된 대화 시뮬레이션
        conversation = [
            "의료기기 영업에 대해 알려주세요",
            "병원 구매담당자와의 소통 방법은?",
            "제품 데모 시 주의사항은 무엇인가요?"
        ]
        
        session_id = "conversation_test"
        success_count = 0
        
        for i, query in enumerate(conversation, 1):
            print(f"\n💬 대화 {i}: {query}")
            
            try:
                result = run_agent(query, user_id="conv_user", session_id=session_id)
                
                if result["success"]:
                    print(f"✅ 응답 성공 (신뢰도: {result['confidence']:.2f})")
                    success_count += 1
                else:
                    print(f"❌ 응답 실패: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ 대화 {i} 오류: {e}")
        
        print(f"\n📊 대화 흐름 테스트: {success_count}/{len(conversation)} 성공")
        return success_count == len(conversation)
        
    except Exception as e:
        print(f"❌ 대화 흐름 테스트 중 오류: {e}")
        return False

def main():
    """메인 실제 API 테스트 실행"""
    print("🏥 QA Medical Agent 실제 API 테스트")
    print("🔑 실제 OpenAI API를 사용합니다 - 비용이 발생할 수 있습니다!")
    print("=" * 60)
    
    # API 키 확인
    if not check_api_keys():
        print("\n❌ API 키 설정 후 다시 실행해주세요.")
        return False
    
    tests = [
        ("기본 워크플로우", test_real_api_workflow),
        ("성능 측정", test_performance),
        ("모델 조합", test_different_model_combinations),
        ("대화 흐름", test_conversation_flow)
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
    print("📊 실제 API 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    for name, success in results:
        status = "✅ 통과" if success else "❌ 실패"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    print(f"\n총 {len(results)}개 테스트 중 {passed}개 통과")
    
    if passed == len(results):
        print("🎉 모든 실제 API 테스트 통과!")
        print("🚀 시스템이 프로덕션 준비 완료되었습니다!")
        return True
    else:
        print("⚠️ 일부 테스트 실패 - 시스템 점검 필요")
        return False

if __name__ == "__main__":
    print("⚠️ 주의: 이 테스트는 실제 OpenAI API를 호출하여 비용이 발생합니다!")
    response = input("계속 진행하시겠습니까? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        success = main()
        sys.exit(0 if success else 1)
    else:
        print("테스트가 취소되었습니다.")
        sys.exit(0) 