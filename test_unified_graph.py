#!/usr/bin/env python3
"""
통합 에이전트 그래프 테스트 스크립트
"""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# 환경변수 설정
from dotenv import load_dotenv
load_dotenv()

async def test_unified_graph():
    """통합 그래프 테스트"""
    
    print("🚀 통합 에이전트 그래프 테스트 시작")
    print("=" * 50)
    
    try:
        # 통합 그래프 import
        from app.services.router_agent.unified_agent_graph import unified_graph
        
        # 테스트 케이스들
        test_cases = [
            {
                "query": "최수아 직원 실적 분석해줘",
                "expected_agent": "employee_agent",
                "description": "직원 실적 분석 테스트"
            },
            {
                "query": "서울의료센터 고객 분석해줘",
                "expected_agent": "client_agent", 
                "description": "고객 분석 테스트"
            },
            {
                "query": "영업방문 결과보고서 작성해줘",
                "expected_agent": "create_document_agent",
                "description": "문서 작성 테스트"
            },
            {
                "query": "회사 규정 검색해줘",
                "expected_agent": "search_agent",
                "description": "내부 검색 테스트"
            },
            {
                "query": "안녕하세요",
                "expected_agent": "needs_user_selection",
                "description": "모호한 질문 테스트"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 테스트 {i}: {test_case['description']}")
            print(f"   쿼리: '{test_case['query']}'")
            
            try:
                # 세션 ID 생성
                session_id = f"test_session_{i}"
                
                # 통합 그래프 실행
                result = await unified_graph.process_query(
                    query=test_case["query"],
                    session_id=session_id
                )
                
                # 결과 출력
                if result.get("success"):
                    print(f"   ✅ 성공")
                    print(f"   🎯 선택된 에이전트: {result.get('agent')}")
                    print(f"   📊 처리 단계: {result.get('stage')}")
                    print(f"   💬 응답 길이: {len(result.get('response', ''))}")
                    
                    # 예상 에이전트와 비교
                    actual_agent = result.get('agent')
                    expected_agent = test_case['expected_agent']
                    
                    if actual_agent == expected_agent:
                        print(f"   🎉 예상 에이전트 일치: {expected_agent}")
                    else:
                        print(f"   ⚠️  에이전트 불일치 - 예상: {expected_agent}, 실제: {actual_agent}")
                    
                    # 응답 미리보기 (처음 100자)
                    response_preview = result.get('response', '')[:100].replace('\n', ' ')
                    print(f"   📝 응답 미리보기: {response_preview}...")
                    
                else:
                    print(f"   ❌ 실패")
                    print(f"   🚨 오류: {result.get('error')}")
                
            except Exception as e:
                print(f"   💥 예외 발생: {str(e)}")
            
            print("-" * 30)
        
        print(f"\n✅ 통합 그래프 테스트 완료!")
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("💡 backend 디렉토리에서 실행해보세요")
    except Exception as e:
        print(f"❌ 테스트 실행 오류: {e}")

async def test_router_api():
    """Router API 테스트 (간접적)"""
    print("\n🌐 Router API 연동 테스트")
    print("=" * 50)
    
    try:
        import httpx
        
        # FastAPI 서버가 실행 중이라고 가정
        base_url = "http://localhost:8000"
        
        async with httpx.AsyncClient() as client:
            # 시스템 정보 확인
            response = await client.get(f"{base_url}/api/router/system-info")
            
            if response.status_code == 200:
                info = response.json()
                print("✅ 시스템 정보 조회 성공")
                print(f"   📌 시스템: {info.get('system')}")
                print(f"   📌 버전: {info.get('version')}")
                print(f"   📌 아키텍처: {info.get('architecture')}")
                print(f"   📌 통합 그래프: {info.get('unified_graph')}")
            else:
                print(f"❌ 시스템 정보 조회 실패: {response.status_code}")
                
    except Exception as e:
        print(f"⚠️ Router API 테스트 스킵 (서버 미실행?): {e}")

if __name__ == "__main__":
    print("🧪 NaruTalk AI 통합 에이전트 시스템 테스트")
    print("🔧 LangGraph + FastAPI 통합 구조 검증")
    print()
    
    # 환경 변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("💡 .env 파일에 OPENAI_API_KEY=your_key_here 를 추가하세요.")
        print()
    
    # 비동기 테스트 실행
    asyncio.run(test_unified_graph())
    asyncio.run(test_router_api()) 