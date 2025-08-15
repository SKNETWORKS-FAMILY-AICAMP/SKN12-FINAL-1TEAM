# 🏗️ SKN_FinalProject - 프로젝트 아키텍처 문서

## 📌 프로젝트 개요

**나루톡 (NaruTalk)** - AI 기반 제약 영업 지원 시스템
- **목적**: 제약회사 영업팀을 위한 종합 디지털 어시스턴트
- **핵심 기술**: Multi-Agent LLM 시스템 (GPT-4 기반)
- **아키텍처**: 3-Tier 마이크로서비스 아키텍처

---

## 🏛️ 시스템 아키텍처

### 전체 구조도
```
┌─────────────────────────────────────────────────┐
│         Frontend (React - Port 3000)            │
│  - 사용자 인터페이스                               │
│  - JWT 기반 인증                                  │
│  - 실시간 프로세스 바                              │
└────────────────────┬────────────────────────────┘
                     │ HTTP/SSE
┌────────────────────▼────────────────────────────┐
│      Agent Server (FastAPI - Port 8000)         │
│  - Multi-Agent 오케스트레이션                      │
│  - AI 에이전트 실행                                │
│  - 프록시 서버 역할                                │
└────────────────────┬────────────────────────────┘
                     │ HTTP Proxy
┌────────────────────▼────────────────────────────┐
│    Database API Server (FastAPI - Port 8010)    │
│  - 데이터베이스 관리                               │
│  - 문서 업로드 처리                                │
│  - 사용자 인증                                    │
└────────────────────┬────────────────────────────┘
                     │
┌─────────────────────────────────────────────────┐
│           Infrastructure Services               │
│  - PostgreSQL (메인 DB)                          │
│  - OpenSearch (문서 검색)                         │
│  - MinIO (파일 저장소)                            │
│  - SQLite (채팅 기록)                             │
└─────────────────────────────────────────────────┘
```

---

## 🤖 Multi-Agent 시스템

### 4개의 전문 AI 에이전트

#### 1. **Router Agent** (오케스트레이터)
- **위치**: `backend/app/services/router_agent/`
- **역할**: 사용자 요청 분석 및 작업 라우팅
- **기능**:
  ```python
  # 작업 분해 예시
  입력: "미라클의원 분석하고 방문보고서 작성해줘"
  출력: [
    {agent: "client_agent", task: "미라클의원 분석"},
    {agent: "docs_agent", task: "방문보고서 작성", depends_on: [0]}
  ]
  ```

#### 2. **Employee Agent** (직원 실적 분석)
- **위치**: `backend/app/services/employee_agent/`
- **기능**:
  - 자연어 → SQL 변환
  - 통계 분석 (선형 회귀, 파레토 분석)
  - 실적 등급 산정 (S-A-B-C-D)
  - 전문 보고서 생성

#### 3. **Documents Agent** (문서 자동화)
- **위치**: `backend/app/services/docs_agent/`
- **지원 문서**:
  - 영업방문 결과보고서
  - 제품설명회 시행 신청서/결과보고서
- **워크플로우**: LangGraph StateGraph 기반

#### 4. **Client Agent** (거래처 분석)
- **위치**: `backend/app/services/client_agent/`
- **기능**:
  - 거래처 등급 평가 (A-D)
  - 매출 트렌드 분석
  - 성장 잠재력 평가

---

## 📁 프로젝트 디렉토리 구조

```
SKN_FinalProject/
├── frontend/                  # React 프론트엔드
│   ├── src/
│   │   ├── components/       # UI 컴포넌트
│   │   │   ├── Admin.js     # 관리자 콘솔
│   │   │   ├── ChatBot.js   # AI 채팅 인터페이스
│   │   │   ├── ProcessProgressBar.js  # 신규 프로세스 바
│   │   │   └── BatchProcessProgressBar.js
│   │   ├── services/         # API 서비스
│   │   │   └── api.js       # API 통신 모듈
│   │   └── App.js           # 메인 라우터
│   └── package.json
│
├── backend/                   # FastAPI 백엔드
│   ├── app/
│   │   ├── api/             # API 라우트
│   │   │   ├── router_api.py
│   │   │   ├── docs_agent_api.py
│   │   │   └── employee_agent_api.py
│   │   ├── services/        # 에이전트 구현
│   │   │   ├── router_agent/
│   │   │   ├── employee_agent/
│   │   │   ├── docs_agent/
│   │   │   └── client_agent/
│   │   └── agent_server.py  # 메인 서버
│   └── requirements.txt
│
├── database/                  # 데이터베이스 API
│   ├── docker/              # Docker 설정
│   └── docs/                # API 명세서
│       └── API_SPECS/
│
└── docker-compose.yml        # Docker 오케스트레이션
```

---

## 🔄 주요 워크플로우

### 1. 문서 업로드 프로세스 (SSE 기반)

```javascript
// Frontend (Admin.js)
uploadDocumentWithSSE(file, title, onProgress)
    ↓ SSE Stream
// Backend Processing Steps
1. validating     → 파일 검증
2. detecting      → 문서 타입 감지
3. classifying    → Text2SQL 분류 (테이블 문서)
4. analyzing      → 문서 분석 (텍스트 문서)
5. summarizing    → 요약 생성
6. uploading      → S3 업로드
7. saving         → DB 저장
8. completed      → 완료
```

### 2. Multi-Agent 작업 처리

```python
# 1. 작업 수신 (router_api.py)
POST /api/v1/chat
{
  "session_id": "xxx",
  "message": "거래처 분석하고 보고서 작성해줘"
}

# 2. 작업 분해 (router_agent.py)
tasks = decompose_tasks(message)
dependency_graph = build_dependency_graph(tasks)

# 3. 병렬/순차 실행
parallel_groups = get_parallel_groups(dependency_graph)
for group in parallel_groups:
    execute_parallel(group)

# 4. 결과 통합
final_result = aggregate_results(task_results)
```

### 3. 실시간 프로세스 바 업데이트

```javascript
// 단일 파일 업로드
<ProcessProgressBar
  currentStep={currentStep}        // 현재 처리 단계
  documentType={documentType}      // table/text
  fileName={fileName}
  isCompleted={isUploadCompleted}
  onConfirm={handleConfirmUpload}
/>

// 배치 업로드
<BatchProcessProgressBar
  totalFiles={totalFiles}
  currentFileIndex={currentIndex}
  successCount={successCount}
  failCount={failCount}
  currentStep={currentStep}
  isCompleted={isCompleted}
  onConfirm={handleConfirm}
/>
```

---

## 🛠️ 기술 스택 상세

### Backend
| 기술 | 용도 | 버전/세부사항 |
|------|------|--------------|
| FastAPI | 웹 프레임워크 | Uvicorn ASGI 서버 |
| OpenAI | LLM 엔진 | GPT-4o, GPT-4o-mini |
| LangChain | AI 오케스트레이션 | 에이전트 체인 구성 |
| LangGraph | 워크플로우 관리 | StateGraph 기반 |
| PostgreSQL | 메인 데이터베이스 | 사용자, 문서 관리 |
| OpenSearch | 검색 엔진 | 3-node 클러스터 |
| MinIO | 파일 저장소 | S3 호환 스토리지 |

### Frontend
| 기술 | 용도 | 버전/세부사항 |
|------|------|--------------|
| React | UI 프레임워크 | v19.1.0 |
| React Router | 라우팅 | v7.x |
| Axios | HTTP 클라이언트 | API 통신 |
| CSS | 스타일링 | 커스텀 애니메이션 |

---

## 🔐 인증 및 보안

### JWT 토큰 기반 인증
```javascript
// 로그인 플로우
1. POST /user/login
   → credentials 전송
   
2. 서버 응답
   → JWT access_token 발급
   
3. 토큰 저장
   → localStorage('narutalk_token')
   
4. API 요청 시
   → Authorization: Bearer ${token}
   
5. 토큰 검증
   → 서버 측 자동 검증
```

### 역할 기반 접근 제어 (RBAC)
- **Admin**: 전체 시스템 관리, 직원 등록
- **User**: 개인 데이터 접근, 문서 업로드

---

## 📊 데이터베이스 스키마

### PostgreSQL 주요 테이블
```sql
-- 직원 정보
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    name VARCHAR(100),
    role VARCHAR(50),
    is_active BOOLEAN DEFAULT true
);

-- 문서 관리
CREATE TABLE documents (
    doc_id SERIAL PRIMARY KEY,
    doc_title VARCHAR(255),
    doc_type VARCHAR(50),
    file_path TEXT,
    uploader_id INTEGER REFERENCES employees,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 채팅 세션
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY,
    employee_id INTEGER REFERENCES employees,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_archived BOOLEAN DEFAULT false
);
```

---

## 🚀 Docker 컨테이너 구성

```yaml
services:
  # 프론트엔드
  frontend:
    ports: "3000:3000"
    volumes: ./frontend/src:/app/src  # 핫 리로드
    
  # 에이전트 서버
  backend:
    ports: "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_API_URL=http://fastapi-app:8000
      
  # 데이터베이스 API
  fastapi-app:
    ports: "8010:8000"
    depends_on:
      - postgres
      - opensearch-node1
      - minio
```

---

## 📈 주요 기능 구현

### 1. 프로세스 바 시스템 (신규 구현)
- **위치**: `frontend/src/components/ProcessProgressBar.js`
- **특징**:
  - 문서 타입별 동적 단계 표시
  - 노란색 → 초록색 그라디언트 전환
  - 실시간 스피너 애니메이션
  - 완료 시 확인 버튼 오버레이

### 2. SSE 기반 실시간 업데이트
- **엔드포인트**: `/documents/upload-sse`
- **이벤트 스트림**:
  ```javascript
  data: {"step": "validating", "message": "파일 검증 중"}
  data: {"step": "classified", "target_table": "sales_records"}
  data: {"step": "completed", "result": {...}}
  ```

### 3. Multi-Agent 병렬 처리
- **동시 실행**: 독립적인 작업 병렬 처리
- **의존성 관리**: 작업 간 종속성 자동 해결
- **결과 통합**: 마크다운 형식 통합 보고서

---

## 🔧 개발 환경 설정

### 필수 환경 변수 (.env)
```bash
# OpenAI
OPENAI_API_KEY=sk-xxx

# Database
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=narutalk

# JWT
JWT_SECRET_KEY=your-secret-key

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# OpenSearch
OPENSEARCH_INITIAL_ADMIN_PASSWORD=admin123
```

### 실행 명령어
```bash
# Docker 환경 실행
docker-compose up -d

# 개발 서버 실행 (로컬)
# Backend
cd backend && uvicorn app.agent_server:app --reload --port 8000

# Frontend
cd frontend && npm start
```

---

## 📝 API 엔드포인트 요약

### Agent Server (8000)
| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/api/v1/chat` | POST | Multi-Agent 처리 |
| `/api/v1/docs/chat` | POST | 문서 생성 |
| `/api/employee/analyze` | POST | 직원 분석 |
| `/health` | GET | 헬스 체크 |

### Database API (8010)
| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/user/login` | POST | 로그인 |
| `/documents/upload-sse` | POST | SSE 업로드 |
| `/documents/upload-batch-sse` | POST | 배치 업로드 |
| `/search/hybrid` | POST | 하이브리드 검색 |

---

## 🎯 비즈니스 도메인

### 제약 영업 특화 기능
1. **영업방문 보고서 자동화**
2. **제품설명회 관리 시스템**
3. **거래처 등급 평가 (A-D)**
4. **직원 실적 분석 (S-A-B-C-D 등급)**
5. **컴플라이언스 검토 시스템**

---

## 📚 참고 문서
- [API 명세서](database/docs/API_SPECS/)
- [백엔드 아키텍처](backend/BACKEND_ARCHITECTURE.md)
- [Docker 설정](database/docker/docker-compose.yml)

---

*Last Updated: 2025-01-15*