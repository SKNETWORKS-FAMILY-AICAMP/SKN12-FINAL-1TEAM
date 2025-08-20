#!/bin/bash
set -e

echo "🚀 Starting production application..."

# 환경 변수 디버깅
echo "📋 Environment check:"
echo "  - POSTGRES_HOST: ${POSTGRES_HOST}"
echo "  - POSTGRES_PORT: ${POSTGRES_PORT}"
echo "  - POSTGRES_DB: ${POSTGRES_DB}"
echo "  - POSTGRES_USER: ${POSTGRES_USER}"
echo "  - OPENSEARCH_HOST: ${OPENSEARCH_HOST}"
echo "  - Current directory: $(pwd)"
echo "  - Python path: $(which python)"
echo "  - App directory contents:"
ls -la /app/app/ 2>/dev/null || echo "    App directory not found"

# PostgreSQL 연결 대기 (최대 30초)
echo "⏳ Waiting for PostgreSQL..."
MAX_TRIES=30
COUNTER=0

while [ $COUNTER -lt $MAX_TRIES ]; do
    if python -c "
import os
import psycopg2
import sys

host = os.environ.get('POSTGRES_HOST')
port = os.environ.get('POSTGRES_PORT', '5432')
db = os.environ.get('POSTGRES_DB')
user = os.environ.get('POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD')

print(f'Trying to connect to {host}:{port}/{db} as {user}...')

try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=db,
        user=user,
        password=password
    )
    conn.close()
    print('✅ PostgreSQL connected successfully')
    sys.exit(0)
except Exception as e:
    print(f'❌ Connection failed: {e}')
    sys.exit(1)
" 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    
    COUNTER=$((COUNTER+1))
    if [ $COUNTER -eq $MAX_TRIES ]; then
        echo "❌ Failed to connect to PostgreSQL after $MAX_TRIES attempts"
        exit 1
    fi
    
    echo "  Retry $COUNTER/$MAX_TRIES..."
    sleep 1
done

# Alembic 마이그레이션 실행 (프로덕션에서는 선택적)
# echo "🔄 Running database migrations..."
# alembic upgrade head || echo "⚠️ Migration failed, continuing anyway..."

# Uvicorn 실행 (프로덕션 설정)
echo "🚀 Starting Uvicorn server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --access-log \
    --log-level info