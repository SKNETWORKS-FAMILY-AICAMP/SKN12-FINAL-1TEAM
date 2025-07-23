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

**POST /api/docs/classify**
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
      "document_type": "contract",
      "category": "legal"
    },
    "error": null
  }
  ```

**POST /api/docs/write**
- **설명**: 문서 초안 작성
- **입력**:
  ```json
  {
    "state": {
      "document_type": "contract"
    },
    "user_input": "소프트웨어 개발 계약서 초안 작성"
  }
  ```
- **출력**:
  ```json
  {
    "success": true,
    "filled_data": {
      "title": "소프트웨어 개발 계약서",
      "content": "계약서 내용..."
    },
    "error": null
  }
  ```

### 4. 직원 분석 API (`/api/employee`)

**GET /api/employee/health**
- **설명**: Employee Agent 헬스 체크
- **출력**:
  ```json
  {
    "status": "healthy",
    "agent": "Employee Performance Agent",
    "data_status": {
      "performance_data": "loaded",
      "target_data": "loaded"
    }
  }
  ```

**GET /api/employee/performance/summary**
- **설명**: 직원 실적 요약 조회
- **출력**:
  ```json
  {
    "success": true,
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
  }
  ```
- **출력**:
  ```json
  {
    "success": true,
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
└── /services/ # 라우터 및 3개의 에이전트 소스파일 ( API 연결 )
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