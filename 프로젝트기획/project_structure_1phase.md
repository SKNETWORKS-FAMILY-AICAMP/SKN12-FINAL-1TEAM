# 🏗️ QA 챗봇 시스템 프로젝트 구조 - Phase 1 (ML 포함)

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

## 🚀 새로운 ML 서비스 구성

### 8. ML 성과 예측 서비스 (Port: 8008)
```python
# 08_ml_performance_prediction/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from services.model_trainer import ModelTrainer
from services.prediction_service import PredictionService
from utils.model_utils import ModelUtils
import logging

app = FastAPI(title="ML Performance Prediction Service")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(router, prefix="/api/v1")

# 시작 시 모델 로드
@app.on_event("startup")
async def startup_event():
    # MLflow 모델 로드
    await ModelUtils.load_models()
    logging.info("ML Performance Prediction Service started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
```

### MLflow 환경 설정
```yaml
# docker-compose.ml.yml
version: '3.8'

services:
  mlflow-server:
    image: mlflow/mlflow:latest
    container_name: mlflow-server
    ports:
      - "5000:5000"
    volumes:
      - ./mlflow:/mlflow
      - ./data/ml_data:/data
    environment:
      - MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow/mlflow.db
      - MLFLOW_DEFAULT_ARTIFACT_ROOT=/mlflow/artifacts
    command: mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow/mlflow.db --default-artifact-root /mlflow/artifacts

  ml-prediction-service:
    build: ./backend/fastapi_services/08_ml_performance_prediction
    container_name: ml-prediction-service
    ports:
      - "8008:8008"
    depends_on:
      - mlflow-server
      - redis
    volumes:
      - ./data:/app/data
      - ./mlflow:/app/mlflow
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow-server:5000
      - REDIS_URL=redis://redis:6379
```

## 🔧 개발 환경 설정

### 1. 의존성 설치
```bash
# ML 서비스 의존성
pip install -r backend/fastapi_services/08_ml_performance_prediction/requirements.txt

# 주요 ML 라이브러리
pip install scikit-learn==1.3.0
pip install xgboost==2.0.0
pip install prophet==1.1.4
pip install tensorflow==2.13.0
pip install mlflow==2.8.1
pip install pandas==2.0.3
pip install numpy==1.24.3
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=performance_prediction
REDIS_URL=redis://localhost:6379
SQLITE_DB_PATH=./data/sqlite/
```

### 3. 서비스 실행
```bash
# 전체 서비스 실행
docker-compose -f docker-compose.yml -f docker-compose.ml.yml up -d

# 개별 ML 서비스 실행
cd backend/fastapi_services/08_ml_performance_prediction
python main.py
```

## 📊 ML 데이터 파이프라인

### 데이터 수집 → 전처리 → 모델 학습 → 예측
```python
# 데이터 파이프라인 예시
class MLDataPipeline:
    def __init__(self):
        self.data_collector = DataCollector()
        self.preprocessor = DataPreprocessor()
        self.model_trainer = ModelTrainer()
        self.prediction_service = PredictionService()
    
    async def run_pipeline(self):
        # 1. 데이터 수집
        raw_data = await self.data_collector.collect_sales_data()
        
        # 2. 데이터 전처리
        processed_data = await self.preprocessor.preprocess(raw_data)
        
        # 3. 모델 학습
        model = await self.model_trainer.train_model(processed_data)
        
        # 4. 모델 평가 및 등록
        metrics = await self.model_trainer.evaluate_model(model)
        await self.model_trainer.register_model(model, metrics)
        
        # 5. 예측 준비
        await self.prediction_service.load_model(model)
```

## 🚀 배포 및 운영

### 1. 개발 환경 (Development)
```bash
docker-compose -f docker-compose.dev.yml -f docker-compose.ml.yml up -d
```

### 2. 프로덕션 환경 (Production)
```bash
docker-compose -f docker-compose.prod.yml -f docker-compose.ml.yml up -d
```

### 3. ML 모델 배포
```bash
# 모델 학습 스크립트 실행
python scripts/ml/train_models.py

# 모델 평가
python scripts/ml/evaluate_models.py

# 모델 배포
python scripts/ml/deploy_models.py
```

## 📈 모니터링 및 로깅

### ML 성능 모니터링
- **MLflow UI**: http://localhost:5000
- **모델 성능 대시보드**: Grafana 연동
- **데이터 드리프트 감지**: Evidently AI
- **실시간 예측 모니터링**: Prometheus + Grafana

### 로그 관리
```
monitoring/logs/ml/
├── model_training.log          # 모델 학습 로그
├── prediction_requests.log     # 예측 요청 로그
├── model_performance.log       # 모델 성능 로그
└── data_pipeline.log          # 데이터 파이프라인 로그
```

## 🔒 보안 고려사항

### ML 모델 보안
- **MLflow 인증**: 사용자 기반 접근 제어
- **모델 암호화**: 민감한 모델 파라미터 암호화
- **API 보안**: 예측 API 인증 및 Rate Limiting
- **데이터 보안**: 학습 데이터 개인정보 보호

---

### 📝 Phase 1 개발 순서

1. **기본 인프라 구축** (1-2주)
   - Docker 환경 설정
   - 데이터베이스 초기화
   - 기본 API Gateway 구축

2. **핵심 서비스 개발** (3-6주)
   - 통합 검색 서비스
   - 실적 분석 서비스
   - 거래처 분석 서비스

3. **🆕 ML 서비스 개발** (7-10주)
   - MLflow 환경 구축
   - 데이터 파이프라인 구축
   - 모델 학습 및 평가
   - 예측 서비스 개발

4. **UI 및 통합 테스트** (11-12주)
   - React 프론트엔드 개발
   - 전체 시스템 통합
   - 성능 테스트 및 최적화

이 구조는 머신러닝 기반 실적 예측 기능을 완전히 통합한 확장 가능한 아키텍처로, Phase 1에서 모든 핵심 기능을 구현할 수 있도록 설계되었습니다. 