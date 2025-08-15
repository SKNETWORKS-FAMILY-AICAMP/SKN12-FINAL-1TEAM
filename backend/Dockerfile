# syntax=docker/dockerfile:1.4

########## 1단계: Builder ##########
FROM python:3.11-slim AS builder
WORKDIR /app

# requirements.txt 복사
COPY requirements.txt .

# 빌드 도구 설치 + uv 설치 + 패키지 설치를 한 번에 처리
RUN --mount=type=cache,target=/root/.cache/uv \
    apt-get update && apt-get install -y gcc g++ curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && /root/.local/bin/uv pip install --system -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

# PATH 설정 (나중에 필요할 수 있으므로 유지)
ENV PATH="/root/.local/bin:${PATH}"

# 앱 소스 복사
COPY app/ ./app/

########## 2단계: Runtime ##########
FROM python:3.11-slim
WORKDIR /app

# builder에서 설치된 Python 패키지 복사
COPY --from=builder /usr/local /usr/local
COPY app/ ./app/

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Seoul

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# agent_server.py 실행
CMD ["python", "app/agent_server.py"]