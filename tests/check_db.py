import sqlite3
import os

db_path = 'database/history/memory.sqlite'

print(f"📁 데이터베이스 파일 경로: {db_path}")
print(f"📁 파일 존재 여부: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    print(f"📁 파일 크기: {os.path.getsize(db_path)} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 테이블 목록 확인
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        print(f"📊 테이블 목록: {[t[0] for t in tables]}")
        
        # 각 테이블의 데이터 개수 확인
        for table in tables:
            table_name = table[0]
            c.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = c.fetchone()[0]
            print(f"   - {table_name}: {count}개")
            
            # 테이블 구조 확인
            c.execute(f"PRAGMA table_info({table_name})")
            columns = c.fetchall()
            column_names = [col[1] for col in columns]
            print(f"   - 컬럼: {column_names}")
        
        # 최근 데이터 확인
        if 'chat_sessions' in [t[0] for t in tables]:
            c.execute("SELECT * FROM chat_sessions ORDER BY created_at DESC LIMIT 3")
            sessions = c.fetchall()
            print(f"📋 최근 세션들:")
            for session in sessions:
                print(f"   - {session}")
        
        if 'chat_messages' in [t[0] for t in tables]:
            c.execute("SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 5")
            messages = c.fetchall()
            print(f"📋 최근 메시지들:")
            for msg in messages:
                print(f"   - {msg}")
        
        conn.close()
        print("✅ 데이터베이스 확인 완료")
        
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")
else:
    print("❌ 데이터베이스 파일이 없습니다!") 