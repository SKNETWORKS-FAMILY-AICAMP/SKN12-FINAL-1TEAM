#!/usr/bin/env python3
"""
NaruTalk AI 통합 에이전트 시스템 - 정상작동 테스트
"""

import asyncio
import sys
import requests
import time
from pathlib import Path

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

class SystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        
    async def test_individual_agents(self):
        """개별 에이전트 LangGraph 테스트"""
        print("🤖 개별 에이전트 LangGraph 테스트")
        print("=" * 50)
        
        agents = [
            ("employee_agent", "최수아 직원 실적 분석해줘"),
            ("client_agent", "서울의료센터 고객 분석해줘"),
            ("search_agent", "회사 규정 검색해줘"),
            ("create_document_agent", "영업방문 결과보고서 작성해줘")
        ]
        
        for agent_name, test_query in agents:
            try:
                print(f"\n📋 {agent_name} 테스트 중...")
                
                # 동적 import
                module_name = f"app.services.{agent_name}.run"
                run_module = __import__(module_name, fromlist=['run'])
                
                # 테스트 실행
                result = await run_module.run({
                    "query": test_query,
                    "session_id": f"test_{agent_name}"
                })
                
                # 결과 검증
                success = result.get("success", False)
                agent = result.get("agent", "")
                langraph = result.get("langraph", False)
                
                if success and agent == agent_name and langraph:
                    print(f"   ✅ {agent_name} 성공")
                    print(f"   🎯 에이전트: {agent}")
                    print(f"   📊 LangGraph: {langraph}")
                    self.test_results.append((agent_name, True))
                else:
                    print(f"   ❌ {agent_name} 실패")
                    print(f"   🎯 에이전트: {agent}")
                    print(f"   📊 LangGraph: {langraph}")
                    self.test_results.append((agent_name, False))
                    
            except Exception as e:
                print(f"   💥 {agent_name} 오류: {e}")
                self.test_results.append((agent_name, False))
        
        # 결과 요약
        success_count = sum(1 for _, success in self.test_results if success)
        total_count = len(self.test_results)
        success_rate = (success_count / total_count) * 100
        
        print(f"\n🎯 전체 결과: {success_count}/{total_count} 통과 ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 모든 테스트 통과! 시스템이 완벽하게 작동합니다!")
        else:
            print("⚠️ 일부 테스트 실패. 문제를 확인해주세요.")
            
        return success_rate == 100

    def test_api_endpoints(self):
        """API 엔드포인트 테스트"""
        print("\n🌐 API 엔드포인트 테스트")
        print("=" * 50)
        
        # 헬스 체크
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ 헬스 체크 성공")
            else:
                print(f"❌ 헬스 체크 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 서버 연결 실패: {e}")
            return False
        
        # 채팅 API 테스트
        test_cases = [
            ("employee_agent", "최수아 직원 실적 분석해줘"),
            ("client_agent", "서울의료센터 고객 분석해줘"),
            ("search_agent", "회사 규정 검색해줘"),
            ("create_document_agent", "영업방문 결과보고서 작성해줘")
        ]
        
        api_success = True
        for expected_agent, query in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/api/router/chat",
                    json={
                        "session_id": f"api_test_{expected_agent}",
                        "query": query
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    actual_agent = result.get('agent', '')
                    success = result.get('success', False)
                    
                    if actual_agent == expected_agent and success:
                        print(f"✅ {expected_agent} API 성공")
                    else:
                        print(f"⚠️ {expected_agent} API 분류 불일치 (예상: {expected_agent}, 실제: {actual_agent})")
                        api_success = False
                else:
                    print(f"❌ {expected_agent} API 오류: {response.status_code}")
                    api_success = False
                    
            except Exception as e:
                print(f"💥 {expected_agent} API 요청 실패: {e}")
                api_success = False
        
        return api_success

    async def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("🎯 NaruTalk AI 통합 에이전트 시스템 - 정상작동 테스트")
        print("🔧 LangGraph + FastAPI + Router Agent 통합 검증")
        print("=" * 80)
        
        # 1단계: 개별 에이전트 테스트
        print("\n🔥 1단계: 개별 에이전트 LangGraph 테스트")
        agent_success = await self.test_individual_agents()
        
        # 2단계: API 테스트
        print("\n🔥 2단계: API 엔드포인트 테스트")
        api_success = self.test_api_endpoints()
        
        # 최종 결과
        print("\n" + "=" * 80)
        print("📊 최종 테스트 결과")
        print("=" * 80)
        
        if agent_success and api_success:
            print("🎉 모든 테스트 통과! 시스템이 정상 작동합니다!")
            return True
        else:
            print("⚠️ 일부 테스트 실패. 문제를 확인해주세요.")
            if not agent_success:
                print("   - 개별 에이전트 테스트 실패")
            if not api_success:
                print("   - API 엔드포인트 테스트 실패")
            return False

async def main():
    """메인 테스트 실행"""
    tester = SystemTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        print("\n✅ 시스템 정상작동 확인 완료!")
        print("🚀 프로덕션 환경에서 사용 가능합니다.")
    else:
        print("\n❌ 시스템 문제 발견!")
        print("🔧 문제 수정 후 재테스트가 필요합니다.")
    
    return success

if __name__ == "__main__":
    """
    시스템 정상작동 테스트 실행
    
    사용법:
    python test/test_system.py
    
    테스트 항목:
    1. 개별 에이전트 LangGraph 실행 테스트
    2. API 엔드포인트 연결 테스트
    3. 라우터 분류 정확도 테스트
    
    결과:
    - 모든 테스트 통과 시: 시스템 정상작동
    - 일부 실패 시: 문제점 표시 및 수정 필요
    """
    success = asyncio.run(main())
    exit(0 if success else 1) 