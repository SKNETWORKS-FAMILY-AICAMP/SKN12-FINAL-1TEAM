# Database FastAPI Application

## 프로젝트 개요
FastAPI 기반의 데이터베이스 관리 시스템으로, PostgreSQL, OpenSearch, MinIO를 활용한 통합 데이터 플랫폼입니다.

## 현재 프로젝트 구조

```
database_fastapi_app/
├── app/                          # 메인 애플리케이션
│   ├── main.py                  # FastAPI 앱 진입점
│   ├── config/                  # 설정 관련
│   │   ├── settings.py
│   │   └── table_descriptions.json
│   ├── models/                  # SQLAlchemy 모델
│   │   ├── customers.py
│   │   ├── employees.py
│   │   ├── branches.py
│   │   ├── products.py
│   │   ├── sales_records.py
│   │   ├── documents.py
│   │   ├── schedules.py
│   │   └── ...
│   ├── routers/                 # API 라우터
│   │   ├── user_router.py      # 사용자 인증 (/user)
│   │   ├── admin_router.py     # 관리자 기능 (/admin)
│   │   ├── customer_router.py  # 고객 관리 (/customers)
│   │   ├── branch_router.py    # 지점 관리 (/branches)
│   │   ├── employee_info_router.py  # 직원 정보 (/employee-info)
│   │   ├── employee_performance_router.py  # 직원 성과 (/performance)
│   │   ├── document_router.py  # 문서 관리 (/documents)
│   │   ├── schedule_router.py  # 일정 관리 (/schedules)
│   │   ├── news_router.py      # 뉴스 관리 (/news)
│   │   ├── data_upload_router.py  # 데이터 업로드 (/data)
│   │   ├── search_router.py    # 검색 기능 (/search)
│   │   ├── hybrid_search_router.py  # 하이브리드 검색 (/search - hybrid)
│   │   ├── qa_router.py        # Q&A 기능 (/qa)
│   │   ├── chat_history_router.py  # 채팅 기록 (/chat)
│   │   ├── dashboard_router.py # 대시보드 (/dashboard)
│   │   └── approval_router.py  # 승인 프로세스 (/approval)
│   ├── schemas/                 # Pydantic 스키마
│   │   ├── customers.py
│   │   ├── branches.py
│   │   ├── employee.py
│   │   ├── document.py
│   │   └── ...
│   ├── services/                # 비즈니스 로직
│   │   ├── core/               # 핵심 서비스
│   │   │   ├── data_upload_processor.py
│   │   │   ├── document_analyzer.py
│   │   │   ├── hybrid_search_service.py
│   │   │   ├── text2sql_search.py
│   │   │   └── ...
│   │   ├── external/           # 외부 서비스 연동
│   │   │   ├── opensearch_service.py
│   │   │   ├── postgres_service.py
│   │   │   ├── s3_service.py
│   │   │   └── openai_service.py
│   │   ├── processors/         # 데이터 처리
│   │   │   ├── hr_data_processor.py
│   │   │   ├── customer_info_processor.py
│   │   │   └── query_analyzer.py
│   │   └── utils/             # 유틸리티
│   │       ├── db.py
│   │       └── foreign_key_utils.py
│   └── scripts/                # 초기화 스크립트
│       ├── init_vector_db.py
│       └── update_vector_db.py
├── docker/                      # Docker 설정
│   ├── docker-compose.yml      # 컨테이너 오케스트레이션
│   ├── database-fastapi-app.Dockerfile
│   ├── postgres.Dockerfile
│   ├── start.sh
│   ├── init-scripts/
│   │   └── 01-init-pgvector.sql
│   └── aws/                    # AWS 배포 관련
│       ├── deploy-ecr.sh
│       └── MIGRATION_GUIDE.md
├── migrations/                  # 데이터베이스 마이그레이션
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   └── *.sql                   # SQL 마이그레이션 파일
├── dashboard/                   # 대시보드 애플리케이션
│   ├── main.py
│   └── start_dashboard.py
├── requirements/                # 의존성 관리
│   ├── requirements.txt        # 전체 의존성
│   ├── requirements-base.txt   # 기본 의존성
│   └── requirements-ml.txt     # ML 관련 의존성
├── docs/                       # 문서
│   ├── API_SPECS/             # API 명세서
│   │   ├── CUSTOMER_API_SPEC.md
│   │   ├── EMPLOYEE_API_SPEC.md
│   │   └── ...
│   ├── JWT_SECURITY_GUIDE.md
│   ├── 환경변수_README.md
│   └── database_diagram.dbml
└── util_scripts/               # 유틸리티 스크립트
    └── JWT_KEY_CREATOR.py

```

## 주요 기능

### 1. 사용자 관리 및 인증
- JWT 기반 인증 시스템
- 역할 기반 접근 제어 (RBAC)
- 사용자 등록, 로그인, 프로필 관리

### 2. 데이터 관리
- **고객 관리**: 고객 정보 CRUD, 월별 성과 분석
- **직원 관리**: 직원 정보, 성과 평가, 목표 관리
- **지점 관리**: 지점 정보 조회, 검색
- **문서 관리**: 문서 업로드, 버전 관리, 관계 분석
- **일정 관리**: 캘린더 기능, 이벤트 관리

### 3. 검색 기능
- **하이브리드 검색**: 키워드 + 벡터 검색 결합
- **Text2SQL**: 자연어 쿼리를 SQL로 변환
- **벡터 검색**: OpenSearch를 활용한 시맨틱 검색

### 4. 데이터 분석
- **대시보드**: 실시간 데이터 시각화
- **성과 분석**: 직원/고객 성과 지표
- **리포트 생성**: 자동화된 보고서 생성

### 5. 외부 데이터 통합
- **뉴스 수집**: 외부 뉴스 데이터 수집 및 분석
- **데이터 업로드**: CSV/Excel 파일 일괄 업로드
- **S3 연동**: MinIO를 통한 대용량 파일 저장

## 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL + pgvector
- **Search Engine**: OpenSearch
- **Object Storage**: MinIO (S3 호환)
- **ORM**: SQLAlchemy
- **Migration**: Alembic

### AI/ML
- **LLM**: OpenAI GPT API
- **Embedding**: text-embedding-ada-002
- **Vector DB**: pgvector, OpenSearch

### DevOps
- **Container**: Docker, Docker Compose
- **Cloud**: AWS 지원 (ECR, ECS)
- **Monitoring**: 로깅 시스템 구축

## API 엔드포인트

### 인증 관련
- `POST /user/register` - 사용자 등록
- `POST /user/login` - 로그인
- `GET /user/me` - 현재 사용자 정보

### 데이터 관리
- `/customers/*` - 고객 관리
- `/branches/*` - 지점 관리
- `/employee-info/*` - 직원 정보
- `/performance/*` - 직원 성과
- `/documents/*` - 문서 관리
- `/schedules/*` - 일정 관리

### 검색 및 분석
- `/search/*` - 일반 검색 및 하이브리드 검색
- `/qa/*` - Q&A 시스템
- `/dashboard/*` - 대시보드 데이터

### 관리자 기능
- `/admin/*` - 시스템 관리
- `/approval/*` - 승인 프로세스
- `/data/*` - 데이터 업로드

### 커뮤니케이션
- `/chat/*` - 채팅 기록 관리
- `/news/*` - 뉴스 관리

## 환경 설정

### 필수 환경 변수
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname
POSTGRES_USER=youruser
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=yourdb

# OpenSearch
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# OpenAI
OPENAI_API_KEY=your-api-key

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
```

## 실행 방법

### Docker Compose 사용
```bash
cd docker
docker-compose up -d
```

### 로컬 개발 환경
```bash
# 의존성 설치
pip install -r requirements/requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### 대시보드 실행
```bash
cd dashboard
python start_dashboard.py
```

## 데이터베이스 스키마

주요 테이블:
- `employees` - 직원 정보
- `customers` - 고객 정보
- `branches` - 지점 정보
- `products` - 제품 정보
- `sales_records` - 판매 기록
- `documents` - 문서 메타데이터
- `schedules` - 일정 정보
- `chat_sessions` - 채팅 세션
- `chat_history` - 채팅 기록

## 보안

- JWT 토큰 기반 인증
- 역할 기반 접근 제어
- SQL 인젝션 방지 (SQLAlchemy ORM)
- 환경 변수를 통한 민감 정보 관리

## 문서

자세한 내용은 다음 문서를 참조하세요:
- [API 명세서](./API_SPECS/README.md)
- [환경 변수 가이드](./환경변수_README.md)
- [JWT 보안 가이드](./JWT_SECURITY_GUIDE.md)
- [AWS 마이그레이션 가이드](../docker/aws/MIGRATION_GUIDE.md)