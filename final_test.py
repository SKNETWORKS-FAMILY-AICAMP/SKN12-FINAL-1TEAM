#!/usr/bin/env python3
"""
🎯 NaruTalk AI 통합 에이전트 시스템 - 최종 검증 테스트
"""

import asyncio
import os
import sys
import requests
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

# 환경변수 설정
from dotenv import load_dotenv
load_dotenv()

def test_file_structure():
    """📁 파일 구조 검증"""
    print("📁 파일 구조 검증...")
    
    required_files = [
        "backend/app/main.py",
        "backend/app/api/router_api.py",
        "backend/app/services/router_agent/unified_agent_graph.py",
        "backend/app/services/router_agent/router_agent.py",
        "backend/app/services/employee_agent/simple_employee_handler.py",
        "backend/app/services/client_agent/simple_client_handler.py",
        "backend/app/services/create_document_agent/document_creator.py",
        "backend/app/services/search_agent/database_searcher.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   ❌ 누락된 파일들: {missing_files}")
        return False
    else:
        print(f"   ✅ 모든 필수 파일 존재 확인 ({len(required_files)}개)")
        return True

def test_removed_files():
    """🗑️ 제거된 파일들 검증"""
    print("🗑️ 제거된 파일들 검증...")
    
    should_not_exist = [
        "backend/app/api/docs_api.py",
        "backend/app/api/employee_api.py", 
        "backend/app/api/client_api.py",
        "backend/app/api/download_api.py",
        "backend/app/services/docs_agent",
        "backend/app/services/router_agent/state_graph_router.py",
        "backend/app/services/unified_agent_graph.py"  # 이동된 파일
    ]
    
    still_exists = []
    for file_path in should_not_exist:
        if (project_root / file_path).exists():
            still_exists.append(file_path)
    
    if still_exists:
        print(f"   ⚠️ 아직 존재하는 파일들: {still_exists}")
        return False
    else:
        print(f"   ✅ 불필요한 파일들 모두 제거 확인")
        return True

async def test_unified_graph():
    """🔗 통합 그래프 테스트"""
    print("🔗 통합 그래프 테스트...")
    
    try:
        from app.services.router_agent.unified_agent_graph import unified_graph
        
        # 간단한 테스트 케이스
        test_case = {
            "query": "최수아 실적 분석해줘",
            "session_id": "final_test_session"
        }
        
        result = await unified_graph.process_query(
            query=test_case["query"],
            session_id=test_case["session_id"]
        )
        
        if result.get("success") and result.get("agent") == "employee_agent":
            print(f"   ✅ 통합 그래프 정상 작동: {result.get('agent')}")
            return True
        else:
            print(f"   ❌ 통합 그래프 오류: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"   💥 통합 그래프 예외: {e}")
        return False

def test_server_connection():
    """🌐 서버 연결 테스트"""
    print("🌐 서버 연결 테스트...")
    
    base_url = "http://localhost:8000"
    
    try:
        # 1. 헬스 체크
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"   ❌ 헬스 체크 실패: {health_response.status_code}")
            return False
        
        # 2. 시스템 정보
        system_response = requests.get(f"{base_url}/api/router/system-info", timeout=5)
        if system_response.status_code != 200:
            print(f"   ❌ 시스템 정보 실패: {system_response.status_code}")
            return False
        
        system_info = system_response.json()
        if not system_info.get("unified_graph"):
            print(f"   ❌ 통합 그래프 플래그 없음")
            return False
        
        print(f"   ✅ 서버 연결 정상: {system_info.get('system')} v{system_info.get('version')}")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️ 서버가 실행되지 않음 (http://localhost:8000)")
        print(f"      'python run_server.py' 또는 'python backend/app/main.py'로 서버를 실행하세요")
        return False
    except Exception as e:
        print(f"   💥 서버 연결 예외: {e}")
        return False

def test_api_endpoints():
    """📡 API 엔드포인트 테스트"""
    print("📡 API 엔드포인트 테스트...")
    
    base_url = "http://localhost:8000"
    
    try:
        # 메인 라우터 테스트
        test_data = {
            "session_id": "final_api_test",
            "query": "직원 실적 확인해줘"
        }
        
        response = requests.post(
            f"{base_url}/api/router/router",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("unified_graph"):
                print(f"   ✅ API 엔드포인트 정상: {result.get('agent')}")
                return True
            else:
                print(f"   ❌ API 응답 오류: {result}")
                return False
        else:
            print(f"   ❌ API 요청 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   💥 API 테스트 예외: {e}")
        return False

async def run_final_test():
    """🎯 최종 종합 테스트 실행"""
    print("🎯 NaruTalk AI 통합 에이전트 시스템 - 최종 검증")
    print("=" * 60)
    
    tests = [
        ("파일 구조", test_file_structure),
        ("제거된 파일", test_removed_files),
        ("통합 그래프", test_unified_graph),
        ("서버 연결", test_server_connection),
        ("API 엔드포인트", test_api_endpoints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 테스트 중...")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   💥 {test_name} 테스트 중 예외: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 최종 테스트 결과")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 전체 결과: {passed}/{total} 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! 시스템이 완벽하게 작동합니다!")
        print("\n✅ 준비 완료:")
        print("   📱 백엔드: python run_server.py")
        print("   🌐 프론트엔드: cd frontend && npm start")
        print("   🧪 테스트: python test_unified_graph.py")
    else:
        print(f"\n⚠️ {total-passed}개 테스트 실패. 위의 오류를 확인하세요.")
        
    return passed == total

if __name__ == "__main__":
    # 환경 변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("💡 .env 파일에 OPENAI_API_KEY=your_key_here 를 추가하세요.")
        print()
    
    # 비동기 테스트 실행
    asyncio.run(run_final_test()) 