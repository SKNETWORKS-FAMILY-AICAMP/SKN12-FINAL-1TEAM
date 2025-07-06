## 제약영업사원 업무효율을 위한 문서검색 및 업무자동화 AI partner - llm기반 QA 챗봇 - Phase 1
### "LLM을 활용한 사내 문서 검색 및 업무지원형 디지털 비서 시스템"
##### 내 생각을 이해하고, 내 일을 함께하는 디지털 분신- 나루톡 <br/>
##### 모든 문서와 대화를 하나로 연결하는 스마트 허브 챗봇 - 나투록 <br/>
###### 나루톡 ( 모든 기능의 허브라는 뜻의 순우리말 '나룻터' 와 대화를 주고받는 talk의 합성어로,사용자의 모든 생각과 행동을 연결해주는 디지털 분신 챗봇 )

---

</div>


## 👥 팀 소개

<table>
  <tr>
    <td align="center">
      <img src="./team/1.png" width="120px"><br/>
      <b>김도윤</b><br/><span style="font-size:14px;">시스템 팀장</sub>
    </td>
    <td align="center">
      <img src="./team/2.png" width="120px"><br/>
      <b>손현성</b><br/><span style="font-size:14px;">백앤드/인프라팀장</sub>
    </td>
    <td align="center">
      <img src="./team/3.png" width="120px"><br/>
      <b>이용규</b><br/><span style="font-size:14px;">QC 팀장</sub>
    </td>
    <td align="center">
      <img src="./team/4.png" width="120px"><br/>
      <b>최문영</b><br/><span style="font-size:14px;">프론트 팀장</sub>
    </td>
    <td align="center">
      <img src="./team/5.png" width="120px"><br/>
      <b>허한결</b><br/><span style="font-size:14px;">DB 팀장</sub>
    </td>
  </tr>
</table>


## 폴더 구조
```
medical_qa_chatbot_phase1/
├── 📁 backend/                              # 백엔드 서비스
│   ├── 📁 django_gateway/                   # Django API Gateway
│   │   ├── 📁 config/
│   │   │   ├── settings.py                 # Django 설정
│   │   │   ├── urls.py                     # URL 라우팅
│   │   │   ├── wsgi.py
│   │   │   └── asgi.py
│   │   ├── 📁 apps/
│   │   │   ├── 📁 authentication/          # 사용자 인증
│   │   │   │   ├── models.py
│   │   │   │   ├── views.py
│   │   │   │   ├── serializers.py
│   │   │   │   └── urls.py
│   │   │   ├── 📁 gateway/                 # API 게이트웨이 로직
│   │   │   │   ├── views.py
│   │   │   │   ├── routing.py
│   │   │   │   └── middleware.py
│   │   │   └── 📁 monitoring/              # 모니터링
│   │   │       ├── health_check.py
│   │   │       └── metrics.py
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
│   │   │   │   ├── sqlite_client.py       # SQLite 연결
│   │   │   │   ├── redis_client.py        # Redis 연결
│   │   │   │   ├── faiss_client.py        # FAISS 연결
│   │   │   │   └── file_manager.py        # 파일 시스템 관리
│   │   │   ├── 📁 ai_models/
│   │   │   │   ├── openai_client.py       # OpenAI API
│   │   │   │   ├── bge_reranker.py        # BGE-Reranker
│   │   │   │   ├── kure_embedding.py      # KURE-v1 임베딩
│   │   │   │   └── embedding_manager.py   # 임베딩 관리
│   │   │   ├── 📁 🆕 ml_common/           # ML 공통 모듈
│   │   │   │   ├── mlflow_client.py       # MLflow 연결
│   │   │   │   ├── model_manager.py       # 모델 관리
│   │   │   │   ├── feature_engineering.py # 특성 엔지니어링
│   │   │   │   ├── data_preprocessor.py   # 데이터 전처리
│   │   │   │   └── model_evaluator.py     # 모델 평가
│   │   │   ├── 📁 utils/
│   │   │   │   ├── logger.py
│   │   │   │   ├── exceptions.py
│   │   │   │   ├── validators.py
│   │   │   │   └── file_processor.py      # 파일 처리
│   │   │   └── 📁 schemas/
│   │   │       ├── common.py
│   │   │       ├── responses.py
│   │   │       ├── database_models.py
│   │   │       └── 🆕 ml_models.py        # ML 모델 스키마
│   │   │
│   │   ├── 📁 01_integrated_search/        # 통합 데이터 검색
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   │   ├── routes.py
│   │   │   │   └── dependencies.py
│   │   │   ├── 📁 services/
│   │   │   │   ├── sqlite_search.py       # SQLite 검색
│   │   │   │   ├── file_search.py         # 파일 검색
│   │   │   │   ├── vector_search.py       # FAISS 벡터 검색
│   │   │   │   ├── hybrid_search.py       # 하이브리드 검색
│   │   │   │   └── result_merger.py       # 결과 통합
│   │   │   ├── 📁 models/
│   │   │   │   └── search_models.py
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   ├── 📁 02_performance_analytics/    # 실적 보고서 생성
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 services/
│   │   │   │   ├── sqlite_analytics.py    # SQLite 데이터 분석
│   │   │   │   ├── data_analysis.py       # 데이터 분석
│   │   │   │   ├── report_generator.py    # 보고서 생성
│   │   │   │   ├── chart_generator.py     # 차트 생성
│   │   │   │   └── 🆕 ml_integration.py   # ML 예측 결과 통합
│   │   │   ├── 📁 models/
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   ├── 📁 03_client_analysis/          # 거래처 분석
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 services/
│   │   │   │   ├── client_data_loader.py  # SQLite에서 고객 데이터 로드
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
│   │   │   │   ├── document_loader.py     # 파일에서 문서 로드
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
│   │   │   │   ├── file_processor.py      # 대화 파일 처리
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
│   │   │   │   ├── wiki_file_manager.py   # 위키 파일 관리
│   │   │   │   ├── wiki_search.py         # 위키 검색 (파일+벡터)
│   │   │   │   ├── knowledge_manager.py   # 지식 관리
│   │   │   │   └── version_control.py     # 버전 관리
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   ├── 📁 07_news_recommendation/      # 뉴스 추천
│   │   │   ├── main.py
│   │   │   ├── 📁 api/
│   │   │   ├── 📁 services/
│   │   │   │   ├── naver_api_client.py    # 네이버 API
│   │   │   │   ├── news_storage.py        # 뉴스 SQLite 저장
│   │   │   │   ├── news_analyzer.py       # 뉴스 분석
│   │   │   │   └── recommendation_engine.py # 추천 엔진
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   │
│   │   └── 📁 🆕 08_ml_performance_prediction/ # ML 성과 예측
│   │       ├── main.py
│   │       ├── 📁 api/
│   │       │   ├── routes.py
│   │       │   ├── dependencies.py
│   │       │   └── ml_endpoints.py        # ML 전용 엔드포인트
│   │       ├── 📁 services/
│   │       │   ├── data_collector.py      # 과거 실적 데이터 수집
│   │       │   ├── feature_engineer.py    # 특성 엔지니어링
│   │       │   ├── model_trainer.py       # 모델 학습
│   │       │   ├── prediction_service.py  # 예측 서비스
│   │       │   ├── anomaly_detector.py    # 이상 탐지
│   │       │   └── recommendation_engine.py # 개선 방안 추천
│   │       ├── 📁 models/
│   │       │   ├── time_series_models.py  # 시계열 모델
│   │       │   ├── classification_models.py # 분류 모델
│   │       │   ├── anomaly_models.py      # 이상 탐지 모델
│   │       │   └── ensemble_models.py     # 앙상블 모델
│   │       ├── 📁 ml_pipeline/
│   │       │   ├── data_pipeline.py       # 데이터 파이프라인
│   │       │   ├── training_pipeline.py   # 학습 파이프라인
│   │       │   ├── inference_pipeline.py  # 추론 파이프라인
│   │       │   └── evaluation_pipeline.py # 평가 파이프라인
│   │       ├── 📁 utils/
│   │       │   ├── model_utils.py         # 모델 유틸리티
│   │       │   ├── data_utils.py          # 데이터 유틸리티
│   │       │   ├── visualization.py       # 시각화
│   │       │   └── metrics.py             # 성능 지표
│   │       ├── 📁 config/
│   │       │   ├── model_config.py        # 모델 설정
│   │       │   ├── training_config.py     # 학습 설정
│   │       │   └── inference_config.py    # 추론 설정
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
│       │   ├── generation_node.py
│       │   └── 🆕 ml_prediction_node.py   # ML 예측 노드
│       └── 📁 pipelines/
│           ├── qa_pipeline.py
│           ├── automation_pipeline.py
│           └── 🆕 ml_pipeline.py          # ML 파이프라인
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
│   │   │   ├── 📁 reports/
│   │   │   │   ├── ReportViewer.tsx
│   │   │   │   └── ReportGenerator.tsx
│   │   │   └── 📁 🆕 prediction/          # ML 예측 컴포넌트
│   │   │       ├── PredictionDashboard.tsx
│   │   │       ├── PredictionChart.tsx
│   │   │       ├── ConfidenceIndicator.tsx
│   │   │       ├── RecommendationCard.tsx
│   │   │       └── AnomalyAlert.tsx
│   │   ├── 📁 pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── SearchPage.tsx
│   │   │   ├── AnalyticsPage.tsx
│   │   │   ├── DocumentsPage.tsx
│   │   │   ├── SettingsPage.tsx
│   │   │   └── 🆕 PredictionPage.tsx      # ML 예측 페이지
│   │   ├── 📁 services/
│   │   │   ├── api.ts                     # API 클라이언트
│   │   │   ├── auth.ts                    # 인증 서비스
│   │   │   ├── websocket.ts               # 실시간 통신
│   │   │   └── 🆕 ml_service.ts           # ML 서비스
│   │   ├── 📁 utils/
│   │   │   ├── helpers.ts
│   │   │   ├── constants.ts
│   │   │   └── 🆕 ml_utils.ts             # ML 유틸리티
│   │   ├── 📁 styles/
│   │   │   ├── global.css
│   │   │   └── components.css
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── Dockerfile
│   └── 🆕 .env.example                    # 환경 변수 예시
│
├── 📁 data/                               # 데이터 저장소
│   ├── 📁 sqlite/                         # SQLite 데이터베이스
│   │   ├── main.db                        # 메인 데이터베이스
│   │   ├── users.db                       # 사용자 데이터베이스
│   │   ├── sales.db                       # 실적 데이터베이스
│   │   ├── clients.db                     # 거래처 데이터베이스
│   │   ├── news.db                        # 뉴스 데이터베이스
│   │   └── cache.db                       # 캐시 데이터베이스
│   ├── 📁 files/                          # 파일 저장소
│   │   ├── 📁 documents/                  # 문서 파일
│   │   ├── 📁 uploads/                    # 업로드 파일
│   │   ├── 📁 conversations/              # 대화 파일
│   │   └── 📁 wiki/                       # 위키 파일
│   ├── 📁 faiss_indexes/                  # FAISS 벡터 인덱스
│   │   ├── documents_index.faiss
│   │   ├── wiki_index.faiss
│   │   └── conversations_index.faiss
│   └── 📁 🆕 ml_data/                     # ML 데이터
│       ├── 📁 raw/                        # 원시 데이터
│       ├── 📁 processed/                  # 전처리된 데이터
│       ├── 📁 features/                   # 특성 데이터
│       └── 📁 predictions/                # 예측 결과
│
├── 📁 🆕 mlflow/                          # MLflow 관리
│   ├── 📁 artifacts/                      # 모델 아티팩트
│   ├── 📁 experiments/                    # 실험 데이터
│   ├── 📁 models/                         # 모델 레지스트리
│   ├── 📁 runs/                           # 실행 기록
│   └── mlflow.db                          # MLflow 데이터베이스
│
├── 📁 config/                             # 설정 파일
│   ├── 📁 nginx/                          # Nginx 설정
│   │   └── nginx.conf
│   ├── 📁 redis/                          # Redis 설정
│   │   └── redis.conf
│   └── 📁 🆕 ml/                          # ML 설정
│       ├── model_config.yaml              # 모델 설정
│       ├── training_config.yaml           # 학습 설정
│       └── inference_config.yaml          # 추론 설정
│
├── 📁 scripts/                            # 스크립트
│   ├── 📁 database/                       # DB 스크립트
│   │   ├── init_databases.py              # DB 초기화
│   │   ├── migrate_data.py                # 데이터 마이그레이션
│   │   └── backup_restore.py              # 백업/복원
│   ├── 📁 deployment/                     # 배포 스크립트
│   │   ├── deploy.sh                      # 배포 스크립트
│   │   ├── start_services.sh              # 서비스 시작
│   │   └── stop_services.sh               # 서비스 중단
│   └── 📁 🆕 ml/                          # ML 스크립트
│       ├── train_models.py                # 모델 학습
│       ├── evaluate_models.py             # 모델 평가
│       ├── deploy_models.py               # 모델 배포
│       └── data_pipeline.py               # 데이터 파이프라인
│
├── 📁 tests/                              # 테스트 코드
│   ├── 📁 unit/                           # 단위 테스트
│   │   ├── 📁 backend/
│   │   │   ├── test_search.py
│   │   │   ├── test_analytics.py
│   │   │   └── 🆕 test_ml_prediction.py   # ML 예측 테스트
│   │   └── 📁 frontend/
│   │       ├── test_components.py
│   │       └── 🆕 test_ml_components.py   # ML 컴포넌트 테스트
│   ├── 📁 integration/                    # 통합 테스트
│   │   ├── test_api_integration.py
│   │   └── 🆕 test_ml_integration.py      # ML 통합 테스트
│   ├── 📁 🆕 ml/                          # ML 테스트
│   │   ├── test_models.py                 # 모델 테스트
│   │   ├── test_pipelines.py              # 파이프라인 테스트
│   │   └── test_data_quality.py           # 데이터 품질 테스트
│   └── 📁 performance/                    # 성능 테스트
│       ├── test_load.py
│       └── 🆕 test_ml_performance.py      # ML 성능 테스트
│
├── 📁 docs/                               # 문서
│   ├── 📁 project_management/             # 프로젝트 관리 문서
│   │   ├── 01_requirements_specification.md
│   │   ├── 02_functional_specification.md
│   │   ├── 03_system_design.md
│   │   ├── 04_database_design.md
│   │   ├── 05_api_specification.md
│   │   ├── 06_development_plan.md
│   │   └── 07_test_plan.md
│   ├── 📁 technical/                      # 기술 문서
│   │   ├── setup_guide.md
│   │   ├── deployment_guide.md
│   │   └── 🆕 ml_guide.md                 # ML 가이드
│   ├── 📁 user/                           # 사용자 문서
│   │   ├── user_manual.md
│   │   └── 🆕 ml_user_guide.md           # ML 사용자 가이드
│   └── 📁 🆕 ml/                          # ML 문서
│       ├── model_documentation.md         # 모델 문서
│       ├── data_documentation.md          # 데이터 문서
│       ├── pipeline_documentation.md      # 파이프라인 문서
│       └── performance_metrics.md         # 성능 지표 문서
│
├── 📁 monitoring/                         # 모니터링
│   ├── 📁 logs/                           # 로그 파일
│   │   ├── 📁 application/
│   │   ├── 📁 database/
│   │   └── 📁 🆕 ml/                      # ML 로그
│   ├── 📁 metrics/                        # 메트릭 데이터
│   │   ├── 📁 system/
│   │   ├── 📁 application/
│   │   └── 📁 🆕 ml/                      # ML 메트릭
│   └── 📁 alerts/                         # 알림 설정
│       ├── system_alerts.yaml
│       └── 🆕 ml_alerts.yaml              # ML 알림 설정
│
├── 📁 🆕 notebooks/                       # Jupyter 노트북
│   ├── 📁 exploratory/                    # 탐색적 데이터 분석
│   │   ├── data_exploration.ipynb
│   │   └── sales_analysis.ipynb
│   ├── 📁 modeling/                       # 모델링
│   │   ├── time_series_modeling.ipynb
│   │   ├── classification_modeling.ipynb
│   │   └── anomaly_detection.ipynb
│   └── 📁 evaluation/                     # 평가
│       ├── model_evaluation.ipynb
│       └── performance_analysis.ipynb
│
├── docker-compose.yml                     # Docker Compose 설정
├── docker-compose.dev.yml                 # 개발 환경 Docker Compose
├── docker-compose.prod.yml                # 프로덕션 환경 Docker Compose
├── 🆕 docker-compose.ml.yml               # ML 환경 Docker Compose
├── .env.example                           # 환경 변수 예시
├── .gitignore
├── README.md
└── requirements.txt                       # 공통 의존성
```

# 🏥 Narutalk - 의료업계 QA 챗봇 시스템

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18.2+-blue.svg)](https://reactjs.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Narutalk**은 의료업계 전용 AI 기반 QA 챗봇 시스템입니다. GPT-4o와 LangGraph를 활용하여 의료진이 빠르고 정확한 정보를 얻을 수 있도록 설계되었습니다.

![Narutalk 시스템 아키텍처](https://via.placeholder.com/800x400?text=Narutalk+System+Architecture)

## 🚀 **주요 기능**

### 💬 **AI 챗봇**
- GPT-4o 기반 의료 전문 답변
- 실시간 채팅 (WebSocket)
- 다중 세션 관리
- 의료 카테고리별 분류

### 🔐 **사용자 관리**
- 역할 기반 접근 제어 (의사, 간호사, 관리자)
- JWT 기반 인증
- 의료진 전용 기능

### 🎨 **현대적 UI**
- Material-UI 기반 반응형 디자인
- 다크/라이트 테마 지원
- 모바일 친화적 인터페이스

### 📊 **데이터 분석**
- 의료 문서 검색 및 분석
- 실시간 차트 및 통계
- 성능 모니터링

## 🏗️ **시스템 아키텍처**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   Django API    │    │   FastAPI       │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Port 8001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   Database      │    │   LangGraph     │
│   (Real-time)   │    │   (SQLite)      │    │   (AI Flow)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 **시스템 요구사항**

### 필수 소프트웨어
- **Python**: 3.10 이상
- **Node.js**: 18.x 이상 (LTS 권장)
- **npm**: 9.x 이상

### 권장 사양
- **RAM**: 8GB 이상
- **Storage**: 2GB 이상 여유 공간
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+

## 🛠️ **설치 방법**

### 📥 **자동 설치 (Windows)**
```bash
# 1. 저장소 클론
git clone https://github.com/your-username/narutalk.git
cd narutalk

# 2. 자동 설치 실행
install.bat
```

### 🔧 **수동 설치**
```bash
# 1. 가상환경 생성
python -m venv .venv

# 2. 가상환경 활성화
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Python 패키지 설치
pip install -r requirements/development.txt

# 4. Node.js 패키지 설치
npm install

# 5. 데이터베이스 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 6. 환경 변수 설정
cp config/env.example .env
# .env 파일을 편집하여 API 키 등을 설정
```

### 🔑 **환경 변수 설정**
```env
# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic API 키 (선택)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# Django 비밀키
DJANGO_SECRET_KEY=your-secret-key-here
```

## 🚀 **실행 방법**

### 🎯 **간단한 실행 (권장)**
```bash
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File start_narutalk.ps1

# 또는 배치 파일
start_narutalk.bat

# 또는 Python 스크립트
python run_narutalk.py
```

### 🔄 **수동 실행**
```bash
# 터미널 1: Django 백엔드
.\.venv\Scripts\activate
python manage.py runserver

# 터미널 2: React 프론트엔드
npm run dev

# 터미널 3: FastAPI 서비스 (선택사항)
.\.venv\Scripts\activate
cd service_8001_search
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### 🌐 **접속 URL**
- **메인 웹사이트**: http://localhost:3000
- **Django 관리자**: http://localhost:8000/admin
- **FastAPI 문서**: http://localhost:8001/docs

## 📚 **API 문서**

### Django REST API
- **인증**: `/api/auth/`
- **채팅**: `/api/chat/`
- **사용자**: `/api/users/`
- **관리자**: `/api/admin/`

### FastAPI 마이크로서비스
- **검색**: `/search/`
- **분석**: `/analyze/`
- **예측**: `/predict/`

### WebSocket
- **실시간 채팅**: `ws://localhost:8000/ws/chat/`

## 🧪 **테스트**

### 단위 테스트
```bash
# Django 테스트
python manage.py test

# Pytest 실행
pytest

# 커버리지 포함
pytest --cov=apps --cov-report=html
```

### 통합 테스트
```bash
# 전체 시스템 테스트
python test_workflow.py

# LangGraph 테스트
python langgraph_orchestrator/test_workflow.py
```

## 📦 **배포**

### 🐳 **Docker 배포**
```bash
# Docker 이미지 빌드
docker build -t narutalk:latest .

# 컨테이너 실행
docker run -p 3000:3000 -p 8000:8000 narutalk:latest
```

### 🌐 **프로덕션 배포**
```bash
# 프로덕션 패키지 설치
pip install -r requirements/production.txt

# 정적 파일 수집
python manage.py collectstatic

# Gunicorn으로 실행
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## 🔧 **개발**

### 🎨 **코드 스타일**
```bash
# 코드 포매팅
black .
isort .

# 린팅
flake8 .
eslint src/
```

### 📝 **커밋 규칙**
```bash
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 업데이트
style: 코드 스타일 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드 프로세스 또는 보조 도구 변경
```
📄 문서 목록
1. PROJECT_STRUCTURE.md - 📂 프로젝트 구조 분석 문서
전체 파일 구조를 시각적으로 분석
각 디렉토리와 파일의 역할 상세 설명
아키텍처 계층 구조 (프레젠테이션, API, 마이크로서비스, AI, 데이터)
데이터 흐름도 및 보안 인증 흐름
확장 포인트 가이드
2. DEVELOPMENT_GUIDE.md - 🛠️ 개발 가이드 문서
새로운 기능 추가 방법 (Django 앱, React 컴포넌트, AI 기능, FastAPI 서비스)
데이터베이스 관리 및 마이그레이션
테스트 작성 방법 (Django, React)
배포 준비 (Docker, 프로덕션 설정)
코딩 규칙 및 Git 워크플로우
문제 해결 가이드
3. DJANGO_API_ARCHITECTURE.md - 🏗️ Django API 아키텍처 문서
Django 설정 구조 (config/settings/)
인증 시스템 상세 구현 (커스텀 User 모델, JWT, 권한 관리)
채팅 시스템 구조 (WebSocket, 실시간 통신)
API 게이트웨이 및 미들웨어
REST Framework 설정
전체 API 엔드포인트 매핑
4. README_UPDATED.md - 📖 업데이트된 README 문서
프로젝트 전체 개요 및 주요 기능
시스템 아키텍처 다이어그램
설치 및 실행 방법 (자동/수동)
API 문서 및 엔드포인트 목록
테스트 및 배포 가이드
문제 해결 FAQ




## 🤝 **기여하기**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 **라이선스**

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🆘 **문제 해결**

### 자주 묻는 질문 (FAQ)

**Q: 'vite' 명령어를 찾을 수 없다는 오류가 발생합니다.**
```bash
# 전역 설치
npm install -g vite

# 또는 npx 사용
npx vite
```

**Q: Django 마이그레이션 오류가 발생합니다.**
```bash
# 마이그레이션 파일 삭제 후 재생성
python manage.py makemigrations --empty your_app_name
python manage.py migrate
```

**Q: React 프론트엔드가 로드되지 않습니다.**
```bash
# 캐시 삭제 후 재설치
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 🐛 **버그 리포트**
버그를 발견하셨나요? [Issues](https://github.com/your-username/narutalk/issues)에 리포트해주세요.

### 💬 **지원**
- 📧 Email: support@narutalk.com
- 💬 Discord: [Narutalk Community](https://discord.gg/narutalk)
- 📖 Wiki: [Documentation](https://github.com/your-username/narutalk/wiki)

---

<p align="center">
  <b>🏥 의료업계를 위한 AI 솔루션 - Narutalk</b><br>
  Made with ❤️ by the Narutalk Team
</p> 
### 📝 Phase 1

1. **기본 인프라 구축**
   - Docker 환경 설정
   - 데이터베이스 초기화
   - 기본 API Gateway 구축

2. **핵심 서비스 개발**
   - 통합 검색 서비스
   - 실적 분석 서비스
   - 거래처 분석 서비스

3. **🆕 ML 서비스 개발**
   - MLflow 환경 구축
   - 데이터 파이프라인 구축
   - 모델 학습 및 평가
   - 예측 서비스 개발

4. **UI 및 통합 테스트**
   - React 프론트엔드 개발
   - 전체 시스템 통합
   - 성능 테스트 및 최적화
