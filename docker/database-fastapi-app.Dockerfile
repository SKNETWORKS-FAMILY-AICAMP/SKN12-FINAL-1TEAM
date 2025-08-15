# syntax=docker/dockerfile:1.4

########## 1단계: Builder ##########
FROM python:3.11.7-slim AS builder

WORKDIR /app

# 빌드 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (레이어 캐싱을 위해 별도 RUN)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# uv 경로 설정
ENV PATH="/root/.local/bin:${PATH}"

# requirements 복사 (변경 시에만 이후 레이어 재실행)
COPY requirements/ ./requirements/

# 패키지 설치 (기본 패키지와 ML 라이브러리)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements/requirements-base.txt && \
    uv pip install --system -r requirements/requirements-ml.txt

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY migrations/alembic.ini .

########## 2단계: Runtime ##########
FROM python:3.11.7-slim

WORKDIR /app

# 런타임 의존성 설치 (libpq5 for PostgreSQL, curl for healthcheck/uv)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

# uv 설치 (런타임에서 필요한 경우를 위해)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# uv 경로 설정
ENV PATH="/root/.local/bin:${PATH}"

# builder에서 설치된 Python 패키지 복사
COPY --from=builder /usr/local /usr/local

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY requirements/ ./requirements/
COPY migrations/ ./migrations/
COPY migrations/alembic.ini .

# 시작 스크립트 복사 및 라인 엔딩 변환
COPY docker/start.sh /app/start.sh
RUN dos2unix /app/start.sh && \
    chmod +x /app/start.sh

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Seoul

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["/app/start.sh"]