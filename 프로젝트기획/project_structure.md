# 🏗️ QA 챗봇 시스템 프로젝트 구조

```
medical_qa_chatbot/
├── 📁 backend/                              # 백엔드 서비스
│   ├── 📁 django_gateway/                   # Django API Gateway
│   │   ├── 📁 config/
│   │   │   ├── settings.py                 # Django 설정
│   │   │   ├── urls.py                     # URL 라우팅
│   │   │   ├── wsgi.py
│   │   │   └── asgi.py
│   │   ├── 📁 apps/
│   │   │   ├── 📁 authentication/          # 사용자 인증
│   │   │   ├── 📁 gateway/                 # API 게이트웨이 로직
│   │   │   └── 📁 monitoring/              # 모니터링
│   │   ├── 📁 middleware/
│   │   │   ├── auth_middleware.py
│   │   │   └── logging_middleware.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── manage.py
│   │
│   ├── 📁 fastapi_services/                # FastAPI 마이크로서비스
│   │   ├── 📁 shared/                      # 공통 모듈
│   │   │   ├── 📁 database/
│   │   │   │   ├── opensearch_client.py   # OpenSearch 연결
│   │   │   │   ├── redis_client.py        # Redis 연결
│   │   │   │   └── sqlite_client.py       # SQLite 연결 (초기)
│   │   │   ├── 📁 ai_models/
│   │   │   │   ├── openai_client.py       # OpenAI API
│   │   │   │   ├── bge_reranker.py        # BGE-Reranker
│   │   │   │   └── kure_embedding.py      # KURE-v1
│   │   │   ├── 📁 utils/
│   │   │   │   ├── logger.py
│   │   │   │   ├── exceptions.py
│   │   │   │   └── validators.py
│   │   │   └── 📁 schemas/
│   │   │       ├── common.py
│   │   │       └── responses.py
│   │   │
│   │   ├── 📁 01_integrated_search/        # 통합 데이터 검색
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   │   ├── routes.py
│   │   │   │   └── dependencies.py
│   │   │   ├── 📁 services/
│   │   │   │   ├── hybrid_search.py       # 하이브리드 검색
│   │   │   │   ├── keyword_search.py      # 키워드 검색
│   │   │   │   └── vector_search.py       # 벡터 검색
│   │   │   ├── 📁 models/
│   │   │   │   └── search_models.py
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   ├── 📁 02_performance_analytics/    # 실적 보고서 생성
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 services/
│   │   │   │   ├── data_analysis.py       # ML 기반 분석
│   │   │   │   ├── report_generator.py    # 보고서 생성
│   │   │   │   └── chart_generator.py     # 차트 생성
│   │   │   ├── 📁 models/
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   ├── 📁 03_client_analysis/          # 거래처 분석
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 services/
│   │   │   │   ├── client_classifier.py   # 등급 분류
│   │   │   │   ├── risk_analyzer.py       # 위험 분석
│   │   │   │   └── recommendation.py      # 추천 시스템
│   │   │   ├── 📁 ml_models/
│   │   │   │   └── classification_model.py
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   ├── 📁 04_document_automation/      # 문서 자동화
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 services/
│   │   │   │   ├── document_generator.py  # 문서 생성
│   │   │   │   ├── compliance_checker.py  # 규정 검토
│   │   │   │   └── template_manager.py    # 템플릿 관리
│   │   │   ├── 📁 templates/
│   │   │   │   ├── contract_template.py
│   │   │   │   └── report_template.py
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   ├── 📁 05_conversation_analysis/    # 대화 분석
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 services/
│   │   │   │   ├── sentiment_analyzer.py  # 감정 분석
│   │   │   │   ├── legal_risk_checker.py  # 법적 위험 분석
│   │   │   │   └── transcription.py       # 음성 변환
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   ├── 📁 06_data_wiki/                # 데이터 위키
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 services/
│   │   │   │   ├── wiki_search.py         # 위키 검색
│   │   │   │   ├── knowledge_manager.py   # 지식 관리
│   │   │   │   └── version_control.py     # 버전 관리
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   └── 📁 07_news_recommendation/      # 뉴스 추천
│   │       ├── main.py
│   │       ├── 📁 api/
│   │       ├── 📁 services/
│   │       │   ├── naver_api_client.py    # 네이버 API
│   │       │   ├── news_analyzer.py       # 뉴스 분석
│   │       │   └── recommendation_engine.py # 추천 엔진
│   │       ├── requirements.txt
│   │       └── Dockerfile
│   │
│   └── 📁 langgraph_workflows/             # LangGraph 워크플로우
│       ├── 📁 core/
│       │   ├── state_graph.py             # StateGraph 정의
│       │   ├── intent_classifier.py       # 의도 분류
│       │   └── workflow_orchestrator.py   # 워크플로우 관리
│       ├── 📁 nodes/
│       │   ├── search_node.py
│       │   ├── analysis_node.py
│       │   └── generation_node.py
│       └── 📁 pipelines/
│           ├── qa_pipeline.py
│           └── automation_pipeline.py
│
├── 📁 frontend/                            # React 프론트엔드
│   ├── 📁 public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   │   ├── 📁 common/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Footer.tsx
│   │   │   ├── 📁 search/
│   │   │   │   ├── SearchBox.tsx
│   │   │   │   ├── SearchResults.tsx
│   │   │   │   └── FilterPanel.tsx
│   │   │   ├── 📁 dashboard/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── AnalyticsCard.tsx
│   │   │   │   └── ChartComponent.tsx
│   │   │   ├── 📁 chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   └── ChatInput.tsx
│   │   │   └── 📁 reports/
│   │   │       ├── ReportViewer.tsx
│   │   │       └── ReportGenerator.tsx
│   │   ├── 📁 pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── SearchPage.tsx
│   │   │   ├── AnalyticsPage.tsx
│   │   │   ├── DocumentsPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   ├── 📁 services/
│   │   │   ├── api.ts                     # API 클라이언트
│   │   │   ├── auth.ts                    # 인증 서비스
│   │   │   └── websocket.ts               # 실시간 통신
│   │   ├── 📁 utils/
│   │   │   ├── helpers.ts
│   │   │   └── constants.ts
│   │   ├── 📁 styles/
│   │   │   ├── global.css
│   │   │   └── components.css
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── Dockerfile
│   └── nginx.conf
│
├── 📁 data/                               # 데이터 저장
│   ├── 📁 phase1/                         # Phase 1 데이터
│   │   ├── 📁 sqlite/
│   │   │   ├── app.db                     # SQLite 메인 DB
│   │   │   ├── users.db                   # 사용자 DB
│   │   │   └── cache.db                   # 캐시 DB
│   │   ├── 📁 files/
│   │   │   ├── 📁 documents/              # 문서 파일
│   │   │   ├── 📁 uploads/                # 업로드 파일
│   │   │   └── 📁 processed/              # 처리된 파일
│   │   └── 📁 vectors/
│   │       ├── faiss_index/               # FAISS 인덱스
│   │       ├── embeddings.pkl             # 임베딩 벡터
│   │       └── metadata.json              # 메타데이터
│   │
│   ├── 📁 opensearch/                     # OpenSearch 데이터
│   │   ├── 📁 indices/
│   │   │   ├── unified_search_index/      # 통합 검색 인덱스
│   │   │   ├── documents_index/           # 문서 인덱스
│   │   │   └── vectors_index/             # 벡터 인덱스
│   │   └── 📁 mappings/
│   │       ├── search_mapping.json
│   │       └── vector_mapping.json
│   │
│   └── 📁 external/                       # 외부 데이터
│       ├── 📁 naver_news/                 # 네이버 뉴스 데이터
│       ├── 📁 public_data/                # 공공데이터
│       └── 📁 erp_sync/                   # ERP 동기화 데이터
│
├── 📁 infrastructure/                     # 인프라 구성
│   ├── 📁 docker/
│   │   ├── docker-compose.yml             # 전체 서비스 구성
│   │   ├── docker-compose.dev.yml         # 개발환경
│   │   ├── docker-compose.prod.yml        # 프로덕션
│   │   └── 📁 configs/
│   │       ├── nginx.conf
│   │       ├── redis.conf
│   │       └── opensearch.yml
│   │
│   ├── 📁 aws/
│   │   ├── 📁 cloudformation/
│   │   │   ├── main-stack.yaml            # 메인 스택
│   │   │   ├── ecs-stack.yaml             # ECS 구성
│   │   │   └── opensearch-stack.yaml      # OpenSearch 구성
│   │   ├── 📁 terraform/                  # Terraform 설정
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── 📁 scripts/
│   │       ├── deploy.sh                  # 배포 스크립트
│   │       └── setup.sh                   # 초기 설정
│   │
│   └── 📁 monitoring/
│       ├── 📁 prometheus/
│       │   └── prometheus.yml
│       ├── 📁 grafana/
│       │   └── dashboards/
│       └── 📁 logs/
│           └── logstash.conf
│
├── 📁 airflow/                           # Airflow 자동화
│   ├── 📁 dags/
│   │   ├── data_collection_dag.py         # 데이터 수집
│   │   ├── vector_update_dag.py           # 벡터 업데이트
│   │   ├── backup_dag.py                  # 백업 작업
│   │   └── news_crawling_dag.py           # 뉴스 크롤링
│   ├── 📁 operators/
│   │   ├── opensearch_operator.py
│   │   └── api_operator.py
│   ├── 📁 hooks/
│   │   ├── opensearch_hook.py
│   │   └── naver_api_hook.py
│   ├── airflow.cfg
│   └── requirements.txt
│
├── 📁 tests/                             # 테스트
│   ├── 📁 unit/
│   │   ├── 📁 backend/
│   │   ├── 📁 frontend/
│   │   └── 📁 ai_models/
│   ├── 📁 integration/
│   │   ├── test_api_integration.py
│   │   ├── test_opensearch_integration.py
│   │   └── test_workflow_integration.py
│   ├── 📁 e2e/
│   │   ├── test_user_journey.py
│   │   └── test_search_flow.py
│   └── 📁 load/
│       ├── test_performance.py
│       └── test_scalability.py
│
├── 📁 docs/                              # 문서
│   ├── 📁 api/
│   │   ├── openapi.yaml                   # API 스펙
│   │   └── postman_collection.json
│   ├── 📁 architecture/
│   │   ├── system_design.md
│   │   ├── database_schema.md
│   │   └── deployment_guide.md
│   ├── 📁 user_guide/
│   │   ├── user_manual.md
│   │   └── admin_guide.md
│   └── README.md
│
├── 📁 scripts/                           # 유틸리티 스크립트
│   ├── 📁 setup/
│   │   ├── init_project.sh                # 프로젝트 초기화
│   │   ├── setup_opensearch.py            # OpenSearch 설정
│   │   └── create_indices.py              # 인덱스 생성
│   ├── 📁 data_migration/
│   │   ├── sqlite_to_opensearch.py        # SQLite → OpenSearch
│   │   ├── faiss_to_opensearch.py         # FAISS → OpenSearch
│   │   └── backup_restore.py              # 백업/복원
│   ├── 📁 maintenance/
│   │   ├── health_check.py                # 상태 체크
│   │   ├── performance_monitor.py         # 성능 모니터링
│   │   └── cleanup.py                     # 정리 작업
│   └── 📁 development/
│       ├── generate_test_data.py          # 테스트 데이터 생성
│       └── load_sample_data.py            # 샘플 데이터 로드
│
├── 📁 config/                            # 설정 파일
│   ├── 📁 environments/
│   │   ├── development.env
│   │   ├── staging.env
│   │   └── production.env
│   ├── 📁 ai_models/
│   │   ├── openai_config.yaml
│   │   ├── bge_config.yaml
│   │   └── kure_config.yaml
│   ├── 📁 databases/
│   │   ├── opensearch_config.yaml
│   │   ├── redis_config.yaml
│   │   └── sqlite_config.yaml
│   └── 📁 external_apis/
│       ├── naver_api_config.yaml
│       └── public_data_api_config.yaml
│
├── .env                                  # 환경변수 (개발용)
├── .env.example                          # 환경변수 예시
├── .gitignore
├── .dockerignore
├── requirements.txt                      # 프로젝트 전체 의존성
├── pyproject.toml                        # Python 프로젝트 설정
├── Makefile                             # 빌드/배포 명령어
├── docker-compose.yml                   # 기본 개발환경
└── README.md                            # 프로젝트 개요
```

## 🔧 주요 디렉토리 설명

### **📁 backend/**
- **django_gateway/**: 메인 API 게이트웨이, 인증, 라우팅
- **fastapi_services/**: 7개 마이크로서비스 독립 운영
- **langgraph_workflows/**: LangGraph StateGraph 워크플로우

### **📁 data/**
- **phase1/**: SQLite + FAISS 초기 구성
- **opensearch/**: OpenSearch 통합 구성
- **external/**: 외부 API 데이터

### **📁 infrastructure/**
- **docker/**: 컨테이너 구성
- **aws/**: 클라우드 배포 설정
- **monitoring/**: 모니터링 및 로깅

### **📁 airflow/**
- 데이터 수집, 벡터 업데이트, 백업 등 자동화 작업

## 🚀 개발 시작 명령어

```bash
# 프로젝트 초기화
make init

# 개발환경 실행
docker-compose up -d

# OpenSearch 설정
python scripts/setup/setup_opensearch.py

# 테스트 데이터 로드
python scripts/development/load_sample_data.py
``` 