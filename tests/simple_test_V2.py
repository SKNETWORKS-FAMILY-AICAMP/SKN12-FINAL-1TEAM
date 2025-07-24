import requests
import sqlite3
import time

print("=== 백엔드 API 테스트 ===")

# 1. 헬스 체크
try:
    response = requests.get("http://localhost:8000/health")
    print(f"헬스체크: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"상태: {data.get('status')}")
except Exception as e:
    print(f"헬스체크 실패: {e}")

# 2. SQLite 초기 상태
try:
    conn = sqlite3.connect('database/history/memory.sqlite')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM chat_sessions")
    sessions = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM chat_messages")
    messages = c.fetchone()[0]
    
    print(f"초기 세션: {sessions}개, 메시지: {messages}개")
    conn.close()
except Exception as e:
    print(f"SQLite 확인 실패: {e}")

# 3. Router API 테스트
try:
    data = {
        "session_id": "simple_test_001",
        "query": "최수아 실적 분석"
    }
    
    response = requests.post("http://localhost:8000/api/router/router", json=data)
    print(f"Router API: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"성공: {result.get('success')}")
        if result.get('needs_user_selection'):
            print("사용자 선택 필요")
        else:
            print(f"Agent: {result.get('agent')}")
            
except Exception as e:
    print(f"Router API 실패: {e}")

# 4. SQLite 최종 상태
try:
    conn = sqlite3.connect('database/history/memory.sqlite')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM chat_sessions")
    sessions = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM chat_messages")
    messages = c.fetchone()[0]
    
    print(f"최종 세션: {sessions}개, 메시지: {messages}개")
    
    if sessions > 0:
        c.execute("SELECT id, title FROM chat_sessions ORDER BY created_at DESC LIMIT 1")
        session = c.fetchone()
        print(f"최근 세션: {session[0]} - {session[1]}")
    
    conn.close()
except Exception as e:
    print(f"SQLite 최종 확인 실패: {e}")

print("=== 테스트 완료 ===") 