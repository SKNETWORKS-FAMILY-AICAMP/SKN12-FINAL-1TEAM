import psycopg2
import sys

try:
    # PostgreSQL 연결
    conn = psycopg2.connect(
        host='database-api-db.c1eg2quewkk0.ap-northeast-2.rds.amazonaws.com',
        port=5432,
        user='dbadmin',
        password='zXW#hDSLjqasGBpMQd2U',
        database='postgres'
    )
    
    cur = conn.cursor()
    
    # pgvector 확장 확인
    cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
    result = cur.fetchone()
    
    if result:
        print("✅ pgvector is already installed")
    else:
        print("⚠️ pgvector not found, installing...")
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
            print("✅ pgvector installed successfully")
        except Exception as e:
            print(f"❌ Error installing pgvector: {e}")
            sys.exit(1)
    
    # 확인
    cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
    result = cur.fetchone()
    if result:
        print(f"📦 pgvector version: {result[1]}")
    
    cur.close()
    conn.close()
    print("✅ Database connection successful")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)