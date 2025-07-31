# RouterAgent API 시스템

GPT-4o 기반 4분류 자동 라우팅 시스템을 위한 통합 FastAPI 서버

## 개요

이 시스템은 다음 4가지 기능을 제공합니다:
- 자동 라우팅
- 문서 분류 및 초안 작성
- 직원 실적 분석
- 거래처 분석

## 실행 전 설정

`backend/app/` 디렉토리에서 `.env` 파일을 생성하고 다음 내용을 추가:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## 서버 실행

```bash
cd backend/app
python main.py
```

서버는 `http://0.0.0.0:8000`에서 실행됩니다.

## API 엔드포인트

### 1. 메인 엔드포인트

**GET /**
- **설명**: 서버 상태 확인
- **응답**: `{"message": "🚀 RouterAgent API is running!"}`

### 2. 라우터 API (`/api/route`)

**POST /api/route/router**
- **설명**: 사용자 쿼리를 적절한 에이전트로 라우팅
- **입력**:
  ```json
  {
    "query": "직원 실적을 분석해주세요"
  }
  ```
- **출력**: 라우팅 결과 및 에이전트별 처리 결과

### 3. 문서 API (`/api/docs`)

<<<<<<< HEAD
**POST /api/docs/classify** (레거시)
=======
**POST /api/docs/classify**
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
- **설명**: 문서 분류
- **입력**:
  ```json
  {
    "user_input": "계약서 초안을 작성해주세요"
  }
  ```
- **출력**:
  ```json
  {
    "success": true,
    "state": {
<<<<<<< HEAD
      "doc_type": "영업방문 결과보고서",
      "template_content": "템플릿 내용..."
=======
      "document_type": "contract",
      "category": "legal"
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
    },
    "error": null
  }
  ```

<<<<<<< HEAD
**POST /api/docs/write** (레거시)
=======
**POST /api/docs/write**
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
- **설명**: 문서 초안 작성
- **입력**:
  ```json
  {
    "state": {
<<<<<<< HEAD
      "doc_type": "영업방문 결과보고서"
    },
    "user_input": "방문일시: 2024-01-15, 고객사: ABC회사..."
=======
      "document_type": "contract"
    },
    "user_input": "소프트웨어 개발 계약서 초안 작성"
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
  }
  ```
- **출력**:
  ```json
  {
    "success": true,
    "filled_data": {
<<<<<<< HEAD
      "title": "영업방문 결과보고서",
      "content": "문서 내용..."
=======
      "title": "소프트웨어 개발 계약서",
      "content": "계약서 내용..."
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
    },
    "error": null
  }
  ```

<<<<<<< HEAD
**POST /api/docs/interactive** ⭐ (새로운 상호작용 방식)
- **설명**: 사용자와 상호작용하는 문서 작성 처리
- **초기 요청 (분류)**:
  ```json
  {
    "session_id": "session_123",
    "user_input": "영업방문 결과보고서를 작성해주세요",
    "is_initial": true
  }
  ```
- **초기 응답**:
  ```json
  {
    "success": true,
    "stage": "waiting_input",
    "message": "📄 영업방문 결과보고서 작성을 시작합니다. 다음 정보를 입력해주세요:",
    "doc_type": "영업방문 결과보고서",
    "template": "【기본 정보】\n- 방문 제목:\n- Client(고객사명):\n...",
    "requires_user_input": true
  }
  ```
- **후속 요청 (문서 작성)**:
  ```json
  {
    "session_id": "session_123",
    "user_input": "방문 제목: 신제품 소개\nClient: ABC병원\n담당자: 김의사...",
    "is_initial": false
  }
  ```
- **완료 응답**:
  ```json
  {
    "success": true,
    "stage": "completed",
    "message": "📄 영업방문 결과보고서 작성이 완료되었습니다!",
    "doc_type": "영업방문 결과보고서",
    "document": {
      "방문_제목": "신제품 소개",
      "Client": "ABC병원",
      "담당자": "김의사"
    },
    "session_completed": true
  }
  ```

**GET /api/docs/status/{session_id}**
- **설명**: 문서 작성 세션 상태 조회
- **출력**:
  ```json
  {
    "session_id": "session_123",
    "stage": "waiting_input",
    "doc_type": "영업방문 결과보고서",
    "has_template": true,
    "input_count": 1,
    "is_completed": false,
    "has_error": false,
    "error_message": null
  }
  ```

**POST /api/docs/reset/{session_id}**
- **설명**: 문서 작성 세션 리셋
- **출력**:
  ```json
  {
    "success": true,
    "message": "세션이 초기화되었습니다. 새로운 문서 작성을 시작할 수 있습니다.",
    "session_id": "session_123",
    "stage": "initial"
  }
  ```

### 4. 직원 분석 API (`/api/employee`) ⭐ (대폭 개선)

**GET /api/employee/health**
- **설명**: Employee Agent 헬스 체크 및 시스템 상태 확인
=======
### 4. 직원 분석 API (`/api/employee`)

**GET /api/employee/health**
- **설명**: Employee Agent 헬스 체크
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
- **출력**:
  ```json
  {
    "status": "healthy",
<<<<<<< HEAD
    "agent": "Enhanced Employee Performance Agent",
    "database_status": "connected",
    "available_employees": ["최수아", "조시현"],
    "total_employees": 2,
    "features": [
      "자동 쿼리 분석",
      "SQLite 기반 데이터 처리",
      "고급 통계 분석",
      "LLM 기반 보고서",
      "종합 평가 시스템"
    ]
  }
  ```

**GET /api/employee/employees**
- **설명**: 사용 가능한 직원 목록 조회
=======
    "agent": "Employee Performance Agent",
    "data_status": {
      "performance_data": "loaded",
      "target_data": "loaded"
    }
  }
  ```

**GET /api/employee/performance/summary**
- **설명**: 직원 실적 요약 조회
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
- **출력**:
  ```json
  {
    "success": true,
<<<<<<< HEAD
    "employees": ["최수아", "조시현"],
    "count": 2,
    "message": "2명의 직원 데이터가 있습니다."
  }
  ```

**POST /api/employee/analyze** ⭐ (완전 개선)
- **설명**: 지능형 직원 실적 분석 (자동 쿼리 파싱)
- **입력**:
  ```json
  {
    "session_id": "session_123",
    "query": "최수아의 2023년 12월부터 2024년 3월까지 실적 분석해주세요"
=======
    "summary": {
      "employee_name": "최수아",
      "period": "2023년 12월 ~ 2024년 3월",
      "total_performance": 15000000,
      "total_target": 12000000,
      "achievement_rate": 125.0,
      "status": "급증"
    }
  }
  ```

**POST /api/employee/analyze**
- **설명**: 직원 실적 분석
- **입력**:
  ```json
  {
    "employee_name": "최수아",
    "period": "2024년",
    "save_report": true,
    "filename": "실적분석보고서.docx"
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
  }
  ```
- **출력**:
  ```json
  {
    "success": true,
<<<<<<< HEAD
    "employee_name": "최수아",
    "period": "202312~202403",
    "total_performance": 15000000,
    "achievement_rate": 125.5,
    "evaluation": "우수",
    "report": "📊 직원 실적 분석 보고서\n\n1. 실행 요약\n분석 결과 총 15,000,000원의 실적을 달성하였으며...",
    "analysis_details": {
      "comprehensive_evaluation": {
        "total_score": 85,
        "grade": "A",
        "grade_description": "우수",
        "score_breakdown": {
          "achievement": 40,
          "trend": 25,
          "stability": 16,
          "concentration": 8
        },
        "strengths": ["목표 달성률 우수", "성장 추세 양호"],
        "weaknesses": []
      },
      "detailed_trend": {
        "trend": "상승",
        "slope": 125.5,
        "trend_strength": "강함",
        "prediction": 1650000
      },
      "product_pareto": {
        "total_items": 15,
        "pareto_point": 3,
        "pareto_efficiency": "상위 3개 항목이 전체의 80% 차지"
      },
      "forecast": {
        "method": "가중 평균 (선형회귀 + 이동평균)",
        "forecast": [1650000, 1720000, 1780000],
        "confidence": "높음"
      }
    },
    "message": "실적 분석이 완료되었습니다."
  }
  ```

**POST /api/employee/analyze-detailed**
- **설명**: 상세 파라미터를 지원하는 분석
- **입력**:
  ```json
  {
    "session_id": "session_123",
    "query": "실적 분석해주세요",
    "employee_name": "최수아",
    "period": "202312~202403",
    "analysis_type": "종합분석"
  }
  ```

## 새로운 Employee Agent 주요 기능

### 🔍 **자동 쿼리 분석**
- **자연어 처리**: "최수아의 작년 실적 어떤가요?" → 자동으로 직원명, 기간 추출
- **LLM 기반 파싱**: OpenAI를 활용한 정확한 의도 파악
- **기본값 설정**: 누락된 정보 자동 보완

### 🗄️ **SQLite 기반 데이터 처리**
- **실적 데이터**: `performance_swest_sua.sqlite`에서 월별 실적 조회
- **목표 데이터**: `joonpharma_target.sqlite`에서 목표 정보 조회
- **동적 쿼리**: 조건에 따른 유연한 데이터 필터링

### 📊 **고급 계산 도구**
- **트렌드 분석**: 선형회귀, R² 계산, 예측값 생성
- **파레토 분석**: 80-20 법칙 기반 제품/거래처 집중도 분석
- **분산 분석**: 변동계수(CV), 안정성 평가
- **계절성 분석**: 월별 패턴 및 계절성 지수
- **상관관계 분석**: 피어슨 상관계수
- **예측 분석**: 이동평균 + 선형회귀 결합

### 🎯 **종합 평가 시스템**
- **점수 체계**: 100점 만점 (목표달성 40점, 트렌드 30점, 안정성 20점, 집중도 10점)
- **등급 분류**: S(탁월), A(우수), B(양호), C(보통), D(개선필요)
- **강점/약점 식별**: 자동 분석 및 개선 우선순위 제안

### 📝 **LLM 기반 보고서**
- **지능형 보고서**: GPT를 활용한 전문적이고 실행 가능한 인사이트
- **구조화된 형식**: 실행요약, 성과분석, 트렌드예측, 개선방안
- **폴백 시스템**: LLM 실패시 기본 보고서 자동 생성

### 🔧 **사용 예시**

```python
# 테스트 실행
python backend/app/services/employee_agent/test_enhanced_agent.py

# 다양한 쿼리 예시
"최수아의 실적을 분석해주세요"
"2023년 12월부터 2024년 3월까지 트렌드 분석"
"목표 달성률과 제품별 성과 보고서 만들어줘"
"직원 성과 평가하고 개선 방안 제안해줘"
```

### 📋 **데이터베이스 구조**

**performance_swest_sua.sqlite (실적 데이터)**
```sql
CREATE TABLE sales_performance (
  담당자 TEXT,
  ID TEXT,        -- 거래처명
  품목 TEXT,      -- 제품명
  년월 INTEGER,   -- YYYYMM
  실적금액 REAL   -- 판매금액
);
```

**joonpharma_target.sqlite (목표 데이터)**
```sql
CREATE TABLE monthly_target (
  지점 TEXT,
  담당자 TEXT,
  년월 INTEGER,
  목표 REAL
);
```

=======
    "analysis_result": {
      "performance_metrics": {},
      "trends": {},
      "recommendations": []
    },
    "report": "상세 분석 보고서 텍스트...",
    "message": "분석 완료. 보고서가 저장되었습니다."
  }
  ```

**POST /api/employee/report/generate**
- **설명**: 실적 보고서 생성 및 다운로드
- **입력**: analyze 엔드포인트와 동일
- **출력**:
  ```json
  {
    "success": true,
    "message": "보고서가 성공적으로 저장되었습니다.",
    "filename": "최수아_실적분석보고서.docx",
    "report_preview": "보고서 미리보기 텍스트..."
  }
  ```

>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
### 5. 거래처 분석 API (`/api/client`)

**GET /api/client/health**
- **설명**: Client Agent 헬스 체크
- **출력**:
  ```json
  {
    "status": "healthy",
    "agent": "Client Analysis Agent",
    "service": "running"
  }
  ```

**POST /api/client/analyze**
- **설명**: 거래처 분석
- **입력**:
  ```json
  {
    "name": "ABC 회사",
    "sales": 50000000,
    "visits": 12
  }
  ```
- **출력**:
  ```json
  {
    "success": true,
    "data": {
      "등급": "A",
      "등급 이유": "높은 매출과 안정적인 방문 횟수",
      "영업 전략 보고서": "영업 전략 상세 내용...",
      "성장 요약 보고서": "성장 분석 내용...",
      "통합 보고서": "전체 분석 결과..."
    },
    "message": "클라이언트 분석이 완료되었습니다."
  }
  ```

**POST /api/client/run-report**
- **설명**: 레거시 호환성을 위한 엔드포인트
- **입력**: analyze와 동일
- **출력**: analyze의 data 부분만 반환

## 파일 구조

```
main.py - 모든 FastAPI 실행파일 (통합 서버)
├── /api/client_api.py - 거래처분석 FastAPI 실행파일
├── /api/docs_api.py - 문서초안작성 FastAPI 실행파일  
├── /api/employee_api.py - 실적분석 FastAPI 실행파일
├── /api/router_api.py - 라우터 FastAPI 실행파일
<<<<<<< HEAD
└── /services/ # 라우터 및 3개의 에이전트 소스파일 ( API 연결 )
=======
└── /services/
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
    ├── /client_agent/client_analysis_agent.py - 거래처분석 소스코드
    ├── /docs_agent/
    │   ├── classify_docs.py - 문서 분류 소스코드
    │   ├── test_api.py - 문서 분류부터 초안작성까지 예시 실행 코드
    │   └── write_docs.py - 문서 초안 작성 소스코드
    ├── /employee_agent/employee_agent.py - 실적분석 소스코드
    └── /router_agent/state_graph_router.py - 라우터 스테이트 그래프 소스코드
```

## API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`