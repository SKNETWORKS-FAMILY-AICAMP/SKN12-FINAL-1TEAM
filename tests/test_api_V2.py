import requests
import json
import sqlite3

def test_router_api():
    """Router API 테스트"""
    print("🔍 Router API 테스트 시작...")
    
    url = "http://localhost:8000/api/router/router"
    data = {
        "session_id": "test_session_001",
        "query": "최수아 직원의 실적을 분석해줘"
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"📋 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Router API 응답 성공!")
            print(f"   - Success: {result.get('success')}")
            print(f"   - Agent: {result.get('agent', 'N/A')}")
            if result.get('needs_user_selection'):
                print("   - 사용자 선택 필요")
                print(f"   - 사용 가능 에이전트: {result.get('available_agents')}")
            else:
                print(f"   - Response: {result.get('response', '')[:100]}...")
            return result
        else:
            print(f"❌ Router API 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Router API 호출 실패: {e}")
        return None

def test_select_agent_api():
    """사용자 선택 API 테스트"""
    print("\n🎯 사용자 선택 API 테스트 시작...")
    
    url = "http://localhost:8000/api/router/select-agent"
    data = {
        "session_id": "test_session_001",
        "query": "최수아 직원의 실적을 분석해줘",
        "selected_agent": "employee_agent"
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"📋 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 사용자 선택 API 응답 성공!")
            print(f"   - Success: {result.get('success')}")
            print(f"   - Agent: {result.get('agent')}")
            print(f"   - Response: {result.get('response', '')[:200]}...")
            return result
        else:
            print(f"❌ 사용자 선택 API 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 사용자 선택 API 호출 실패: {e}")
        return None

def check_sqlite_data():
    """SQLite 데이터 확인"""
    print("\n💾 SQLite 데이터 확인...")
    
    try:
        conn = sqlite3.connect('database/history/memory.sqlite')
        c = conn.cursor()
        
        # 세션 개수
        c.execute("SELECT COUNT(*) FROM chat_sessions")
        session_count = c.fetchone()[0]
        print(f"📊 세션 개수: {session_count}")
        
        # 메시지 개수
        c.execute("SELECT COUNT(*) FROM chat_messages")
        message_count = c.fetchone()[0]
        print(f"📊 메시지 개수: {message_count}")
        
        # 최근 세션 확인
        if session_count > 0:
            c.execute("SELECT id, title, created_at FROM chat_sessions ORDER BY created_at DESC LIMIT 3")
            sessions = c.fetchall()
            print("📋 최근 세션들:")
            for session in sessions:
                print(f"   - {session[0]}: {session[1]} ({session[2]})")
        
        # 최근 메시지 확인
        if message_count > 0:
            c.execute("SELECT session_id, role, content, created_at FROM chat_messages ORDER BY created_at DESC LIMIT 5")
            messages = c.fetchall()
            print("📋 최근 메시지들:")
            for msg in messages:
                content_preview = msg[2][:50] + "..." if len(msg[2]) > 50 else msg[2]
                print(f"   - [{msg[1]}] {content_preview} ({msg[3]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ SQLite 확인 실패: {e}")

def test_health():
    """헬스 체크"""
    print("🏥 헬스 체크...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 헬스 체크 성공: {result.get('status')} - {result.get('message')}")
        else:
            print(f"❌ 헬스 체크 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 헬스 체크 오류: {e}")

if __name__ == "__main__":
    print("🚀 API 전체 테스트 시작!")
    print("=" * 50)
    
    # 1. 헬스 체크
    test_health()
    
    # 2. SQLite 초기 상태 확인
    print("\n📊 초기 SQLite 상태:")
    check_sqlite_data()
    
    # 3. Router API 테스트
    router_result = test_router_api()
    
    # 4. 사용자 선택 API 테스트 (Router가 선택을 요구하는 경우)
    if router_result and router_result.get('needs_user_selection'):
        test_select_agent_api()
    
    # 5. SQLite 최종 상태 확인
    print("\n📊 최종 SQLite 상태:")
    check_sqlite_data()
    
    print("\n🎉 테스트 완료!") 