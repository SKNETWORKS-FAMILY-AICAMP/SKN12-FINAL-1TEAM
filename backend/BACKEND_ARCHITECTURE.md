# Backend Architecture Documentation

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [디렉토리 구조](#디렉토리-구조)
3. [핵심 에이전트](#핵심-에이전트)
4. [API 엔드포인트](#api-엔드포인트)
5. [데이터베이스 구조](#데이터베이스-구조)
6. [기술 스택](#기술-스택)
7. [환경 설정](#환경-설정)
8. [빠른 시작](#빠른-시작)

> 전체 시스템 개요는 [`../PROJECT_ARCHITECTURE.md`](../PROJECT_ARCHITECTURE.md), 엔드포인트 원본 목록은 [`app/README.md`](app/README.md)를 참고하세요 — 아래 표는 요약이며 최신 확인은 코드 또는 `app/README.md` 기준입니다.

## 시스템 개요

제약회사 영업 지원을 위한 **AI 기반 멀티 에이전트 시스템**입니다.

### 주요 특징
- **멀티 에이전트 아키텍처**: 5개의 전문화된 AI 에이전트가 협업 (router/employee/client/docs/search)
- **마이크로서비스 구조**: FastAPI 기반 RESTful API
- **AI 모델**: OpenAI GPT-4 시리즈 (GPT-4o, GPT-4o-mini)
- **실시간 처리**: 비동기 처리로 빠른 응답 속도

### 서버 구성
```
포트 8000: 에이전트 전용 서버 (agent_server.py)
├── /api/v1/chat      → Router Agent
├── /api/v1/docs      → Docs Agent  
├── /api/employee     → Employee Agent
└── 프록시 → 포트 8010 Database API
```

## 디렉토리 구조

```
backend/
├── app/
│   ├── agent_server.py           # 🚀 메인 FastAPI 서버 (포트 8000)
│   ├── models.py                  # 📊 SQLAlchemy 데이터베이스 모델
│   │
│   ├── api/                       # 🌐 API 라우터
│   │   ├── router_api.py         # 라우터 에이전트 API
│   │   ├── docs_agent_api.py     # 문서 작성 에이전트 API
│   │   └── employee_agent_api.py # 직원 실적 분석 API
│   │
│   └── services/                  # 🤖 핵심 에이전트 서비스
│       ├── router_agent/          # 질문 분류 및 라우팅
│       │   ├── router_agent.py   # 메인 라우터 로직
│       │   ├── router.py         # LangGraph 기반 구현
│       │   └── prompts/          # 프롬프트 템플릿
│       │
│       ├── docs_agent/            # 문서 자동 생성
│       │   ├── create_document_agent.py  # LangGraph 워크플로우
│       │   ├── templates.yaml    # 문서 템플릿 정의
│       │   ├── S3/               # 문서 템플릿 파일
│       │   └── agent_result_folder/ # 생성된 문서 저장
│       │
│       ├── employee_agent/        # 직원 실적 분석
│       │   ├── employee_agent.py # LangGraph 분석 파이프라인
│       │   ├── db_manager.py     # PostgreSQL 연동
│       │   └── query_analyzer.py # 자연어 쿼리 파싱
│       │
│       ├── client_agent/          # 거래처 분석
│       │   ├── client_agent.py   # 거래처 분석 로직
│       │   └── 좋은제약_거래처정보.xlsx  # 거래처 데이터
│       │
│       ├── search_agent/          # 정보 검색
│       │   └── search_agent.py   # 검색 API 연동
│       │
│       ├── common/                # 공통 유틸리티
│       │   ├── memory.py         # 세션 관리
│       │   ├── chat_history_manager.py  # 대화 기록
│       │   ├── schemas.py        # 상태 스키마 정의
│       │   └── database_api_client.py   # DB API 클라이언트
│       │
│       └── tools/                 # 공통 도구
│           ├── calculation_tools.py     # 계산 도구
│           ├── client_analysis_tools.py # 거래처 분석 도구
│           └── common_tools.py          # 공통 유틸리티
│
├── alembic/                       # 🔄 데이터베이스 마이그레이션
├── requirements.txt               # 📦 Python 패키지 의존성
└── Dockerfile                     # 🐳 Docker 설정 (BuildKit + Multi-stage)
```

## 핵심 에이전트

### 1. 🧭 Router Agent
**경로**: `services/router_agent/`  
**역할**: 사용자 질문을 분석하여 적절한 에이전트로 라우팅

#### 주요 기능
- OpenAI GPT-4o-mini 기반 의도 분류
- Function Calling으로 정확한 라우팅
- 대화 맥락 고려 (최근 10개 메시지)
- 무관한 질문 필터링

#### 라우팅 대상
```python
AVAILABLE_AGENTS = [
    "employee_agent",  # 직원 실적 관련
    "client_agent",    # 거래처 정보 관련
    "search_agent",    # 정보 검색 관련
    "docs_agent",      # 문서 작성 관련
]
```

### 2. 📄 Docs Agent
**경로**: `services/docs_agent/`  
**역할**: 영업 관련 문서 자동 생성

#### 지원 문서
- 영업방문 결과보고서
- 제품설명회 시행 신청서
- 제품설명회 시행 결과보고서

#### 워크플로우
```
사용자 입력 → 문서 타입 분류 → 템플릿 로드 → 
필드 입력 요청 → 문서 생성 → 정책 검증 → 완료
```

#### 기술적 특징
- LangGraph StateGraph 기반
- YAML 템플릿 시스템
- 단계별 상태 관리
- API 모드/대화형 모드 지원

### 3. 📊 Employee Agent
**경로**: `services/employee_agent/`  
**역할**: 직원 실적 분석 및 보고서 생성

#### 분석 기능
- **실적 조회**: 월별/기간별 판매 실적
- **목표 달성률**: 목표 대비 실적 비교
- **트렌드 분석**: 선형회귀, R² 계산
- **파레토 분석**: 80-20 법칙 기반 분석
- **종합 평가**: S~D 등급 시스템

#### 분석 파이프라인
```
쿼리 분석 → 데이터 로드 → 통계 분석 → 
LLM 보고서 생성 → 결과 반환
```

#### 평가 시스템
- **S등급 (95점 이상)**: 탁월
- **A등급 (85-94점)**: 우수
- **B등급 (75-84점)**: 양호
- **C등급 (65-74점)**: 보통
- **D등급 (65점 미만)**: 개선필요

### 4. 🏢 Client Agent
**경로**: `services/client_agent/`  
**역할**: 거래처/고객사 분석

#### 분석 기능
- 거래처 등급 계산 (A~D)
- 매출 추이 분석
- 영업 전략 제안
- 성장 가능성 평가

#### 데이터 소스
- Excel 파일: `좋은제약_거래처정보.xlsx`
- 월별 거래 데이터
- 제품별 판매 현황

## API 엔드포인트

### Router Agent API
```http
POST /api/v1/chat
  - 사용자 메시지 라우팅
  
POST /api/v1/resume/{session_id}
  - 세션 재개
  
GET /api/v1/status/{session_id}
  - 세션 상태 조회

GET /api/v1/agents
  - 사용 가능한 에이전트 목록

GET /api/v1/chat/history/{session_id}
  - 세션 대화 기록 조회

GET /api/v1/chat/sessions/user/{employee_id}
  - 사용자별 세션 목록 조회
```

### Docs Agent API
```http
POST /api/v1/docs/chat
  - 문서 작성 요청
  
POST /api/v1/docs/resume/{session_id}
  - 문서 작성 재개
  
GET /api/v1/docs/status/{session_id}
  - 세션 상태 조회

GET /api/v1/docs/templates
  - 지원 문서 템플릿 목록

POST /api/v1/docs/create-document
  - 문서 생성
```

### Employee Agent API
```http
POST /api/employee/analyze
  - 직원 실적 분석 (JWT 인증 필요)

GET /api/employee/list
  - 직원 목록 조회
  
POST /api/employee/performance
  - 실적 데이터 조회
  
POST /api/employee/target
  - 목표 달성률 조회

GET /api/employee/dashboard-stats
  - 대시보드 통계 조회
```

### Client Agent API
`client_agent_api.py` 자체가 `APIRouter(prefix="/client")`를 가지고 있어, `agent_server.py`의 `/api/v1` 프리픽스와 합쳐져 최종 경로는 `/api/v1/client/*`입니다.
```http
POST /api/v1/client/analyze
  - 거래처 분석

GET /api/v1/client/health
  - Client Agent 헬스 체크
```

### 공통 엔드포인트
```http
GET /health
  - 서버 상태 확인
  
GET /api-routes
  - 사용 가능한 API 목록
```

## 데이터베이스 구조

### PostgreSQL (메인 DB)

#### employees 테이블
```sql
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### schedules 테이블
```sql
CREATE TABLE schedules (
    schedule_id INTEGER PRIMARY KEY,
    employee_id INTEGER REFERENCES employees,
    schedule_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    schedule_date DATE NOT NULL,
    location VARCHAR,
    client_name VARCHAR,
    status VARCHAR DEFAULT 'scheduled'
);
```

### 채팅 기록 저장

채팅 대화 저장은 `services/common/conversation_storage.py`가 담당합니다. HTTP로 Database API 서버(`/api/chat-history/save-message`, `/api/chat-history/get-history`, 기본 8010)에 저장/조회를 위임하며, `router_api.py`가 이 모듈을 사용합니다.

## 기술 스택

### 핵심 프레임워크
- **FastAPI**: 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **SQLAlchemy**: ORM
- **Alembic**: DB 마이그레이션

### AI/ML
- **LangChain**: AI 에이전트 프레임워크
- **LangGraph**: 상태 머신 기반 워크플로우
- **OpenAI**: GPT-4 모델 API

### 데이터 처리
- **Pandas**: 데이터 분석
- **NumPy**: 수치 계산
- **python-docx**: Word 문서 생성
- **openpyxl**: Excel 파일 처리

### 기타
- **httpx/aiohttp**: 비동기 HTTP 클라이언트
- **pydantic**: 데이터 검증
- **python-dotenv**: 환경 변수 관리
- **PyYAML**: YAML 파일 처리

## 환경 설정

### 1. 환경 변수 (.env)
```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# PostgreSQL
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydatabase
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# API Token (선택사항)
API_TOKEN=your_api_token
```

### 2. Python 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 초기화
```bash
# Alembic 마이그레이션 실행
alembic upgrade head
```

## 빠른 시작

### 로컬 실행
```bash
# 1. 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 서버 실행
python app/agent_server.py
```

### Docker 실행
```bash
# 1. 이미지 빌드 (BuildKit 활성화)
DOCKER_BUILDKIT=1 docker build -t agent-server .

# 2. 컨테이너 실행
docker run -p 8000:8000 --env-file .env agent-server
```

### API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주의사항

1. **OpenAI API 키 필수**: 모든 에이전트가 OpenAI API를 사용합니다
2. **PostgreSQL 연결**: Employee Agent는 PostgreSQL이 필요합니다
3. **파일 경로**: 일부 에이전트는 로컬 파일(Excel, YAML)을 참조합니다
4. **메모리 사용**: 대량의 대화 기록 시 메모리 관리 필요

## 문제 해결

### 포트 충돌
```bash
# 8000 포트가 이미 사용 중인 경우
lsof -i :8000  # 사용 중인 프로세스 확인
kill -9 [PID]  # 프로세스 종료
```

### 데이터베이스 연결 실패
```bash
# PostgreSQL 상태 확인
docker ps | grep postgres
# 연결 테스트
psql -h localhost -U myuser -d mydatabase
```

### OpenAI API 오류
- API 키 확인: `.env` 파일의 `OPENAI_API_KEY`
- 사용량 확인: https://platform.openai.com/usage

---

*최종 업데이트: 2025년 1월*