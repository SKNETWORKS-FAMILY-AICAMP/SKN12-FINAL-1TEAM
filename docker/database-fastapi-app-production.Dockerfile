# syntax=docker/dockerfile:1.4

########## 1단계: Builder ##########
FROM python:3.11.7-slim AS builder

WORKDIR /app

# 빌드 도구 설치 (프로덕션에 필요한 최소한만)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (빠른 패키지 설치를 위해)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# requirements 복사 및 패키지 설치
COPY requirements/ ./requirements/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements/requirements-base.txt && \
    uv pip install --system -r requirements/requirements-ml.txt

########## 2단계: Production Runtime ##########
FROM python:3.11.7-slim

# 비root 사용자 생성 (보안 강화)
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# 런타임 의존성 설치 (최소한만)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# builder에서 설치된 Python 패키지 복사
COPY --from=builder /usr/local /usr/local

# 애플리케이션 코드 복사
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser migrations/ ./migrations/
COPY --chown=appuser:appuser migrations/alembic.ini .

# 프로덕션용 시작 스크립트 생성
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Starting production application..."\n\
\n\
# PostgreSQL 연결 대기 (최대 30초)\n\
echo "⏳ Waiting for PostgreSQL..."\n\
for i in {1..30}; do\n\
    if python -c "\n\
import os\n\
import psycopg2\n\
try:\n\
    conn = psycopg2.connect(\n\
        host=os.environ.get(\"POSTGRES_HOST\"),\n\
        port=os.environ.get(\"POSTGRES_PORT\", 5432),\n\
        database=os.environ.get(\"POSTGRES_DB\"),\n\
        user=os.environ.get(\"POSTGRES_USER\"),\n\
        password=os.environ.get(\"POSTGRES_PASSWORD\")\n\
    )\n\
    conn.close()\n\
    print(\"✅ PostgreSQL connected\")\n\
    exit(0)\n\
except:\n\
    exit(1)\n\
" 2>/dev/null; then\n\
        break\n\
    fi\n\
    sleep 1\n\
done\n\
\n\
# Uvicorn 실행 (프로덕션 설정)\n\
exec uvicorn app.main:app \\\n\
    --host 0.0.0.0 \\\n\
    --port 8000 \\\n\
    --workers 1 \\\n\
    --access-log \\\n\
    --log-level info' > /app/start-production.sh && \
    chmod +x /app/start-production.sh && \
    chown appuser:appuser /app/start-production.sh

# 캐시 디렉토리 생성 및 권한 설정 (모델 다운로드용)
RUN mkdir -p /app/.cache/huggingface /app/.cache/sentence-transformers && \
    chown -R appuser:appuser /app/.cache && \
    chmod -R 755 /app/.cache

# 환경변수 설정
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Seoul \
    APP_ENV=production \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

# 헬스체크 설정 (Fargate용)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# 비root 사용자로 전환
USER appuser

# 애플리케이션 실행
CMD ["/app/start-production.sh"]