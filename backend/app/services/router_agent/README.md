# Router Agent System

## 개요

Router Agent는 사용자의 자연어 쿼리를 분석하여 적절한 전문 에이전트로 라우팅하는 지능형 멀티 에이전트 시스템입니다. LangChain과 LangGraph를 기반으로 구축되어 동적 도구 생성, 세션 관리, 인터럽트 처리 등의 고급 기능을 제공합니다.

## 주요 특징

- **지능형 라우팅**: GPT-4 기반 자연어 이해로 쿼리를 적절한 에이전트로 자동 분류
- **동적 도구 생성**: 에이전트 설정에서 LangChain 도구를 자동 생성
- **세션 관리**: 대화 상태를 유지하여 연속적인 상호작용 지원
- **인터럽트 처리**: 추가 정보가 필요한 경우 대화 중단 및 재개 가능
- **확장 가능한 구조**: 새로운 에이전트를 쉽게 추가할 수 있는 모듈화된 설계

## 시스템 구조

```
router_agent/
├── router.py          # 메인 RouterAgent 클래스
├── graph.py          # LangGraph 워크플로우 정의
└── ../tools/
    └── router_tools.py  # 동적 도구 생성 유틸리티
```

### 아키텍처 다이어그램

```
사용자 쿼리
    ↓
[Router Agent]
    ├── LLM 분석 (GPT-4)
    ├── 도구 선택
    └── 에이전트 실행
         ├── docs_agent      → 문서 생성
         ├── employee_agent  → 직원 정보
         ├── client_agent    → 고객 분석
         └── search_agent    → 정보 검색
```

### 워크플로우

```
[check_session] → [route/continue] → [tools] → [final] → END
      ↓                    ↓            ↓         ↓
   세션 확인          라우팅 결정    에이전트    결과 처리
                                      실행
```

## 에이전트 설명

### 1. 📄 문서 작성 도우미 (docs_agent)
- **기능**: 영업 관련 문서 자동 생성 및 규정 검토
- **지원 문서**:
  - 영업방문 결과보고서
  - 제품설명회 시행 신청서
  - 제품설명회 시행 결과보고서
- **특징**: 규정 위반 자동 검사, 대화형 입력 지원

### 2. 👥 직원 정보 조회 (employee_agent)
- **기능**: 직원 실적 및 정보 분석
- **지원 기능**:
  - 개인/팀 실적 조회
  - 목표 달성률 분석
  - 성과 트렌드 분석
  - 인사 정보 조회
- **예시**: "최수아 실적 분석해줘", "서부팀 이번달 성과 보여줘"

### 3. 🏢 거래처 분석 (client_agent)
- **기능**: 고객 및 거래처 데이터 분석
- **지원 기능**:
  - 병원별 실적 분석
  - 매출 추이 분석
  - 거래처 간 비교 분석
  - 고객 등급 분류
- **예시**: "미라클신경과 실적 보여줘", "최근 3개월 매출 트렌드"

### 4. 🔍 정보 검색 (search_agent)
- **기능**: 내부 문서 및 정책 검색
- **지원 기능**:
  - 사내 규정 검색
  - 제품 정보 조회
  - 교육 자료 검색
  - 업무 매뉴얼 조회
- **예시**: "영업 규정 찾아줘", "제품 설명서 검색"

## 기술 스택

- **LLM Framework**: LangChain, LangGraph
- **AI Model**: OpenAI GPT-4o-mini
- **Web Framework**: FastAPI
- **Database**: SQLite (실적 데이터)
- **Data Sources**: Excel, SQLite
- **Programming Language**: Python 3.11+

## 설치 및 실행

### 1. 환경 변수 설정
```bash
export OPENAI_API_KEY="your-api-key"
```

### 2. 의존성 설치
```bash
pip install langchain langchain-openai langgraph fastapi uvicorn
```

### 3. 서버 실행
```bash
cd backend
uvicorn app.agent_server:app --reload --port 8000
```

## API 엔드포인트

> 아래 경로는 `agent_server.py`가 `app.include_router(router_api, prefix="/api/v1")`로 마운트하므로 모두 `/api/v1` 프리픽스가 붙습니다.

### 1. 채팅 요청
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "최수아 실적 분석해줘",
  "session_id": "optional-session-id"
}
```

### 2. 세션 재개
```http
POST /api/v1/resume/{session_id}
Content-Type: application/json

{
  "user_reply": "네, 맞습니다",
  "reply_type": "verification_reply"
}
```

### 3. 세션 상태 조회
```http
GET /api/v1/status/{session_id}
```

### 4. 헬스 체크
```http
GET /api/v1/health
```

### 5. 에이전트 목록
```http
GET /api/v1/agents
```

## 사용 예시

### 기본 사용
```python
# 직원 실적 조회
response = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "최수아 이번달 실적 보여줘"
})

# 문서 생성
response = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "영업방문 보고서 작성해줘"
})
```

### 세션 관리
```python
# 첫 번째 요청
response1 = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "미라클신경과 분석해줘"
})
session_id = response1.json()["session_id"]

# 추가 요청 (같은 세션)
response2 = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "작년 대비 성장률은?",
    "session_id": session_id
})
```

### 도움말 처리
```python
# 매칭되지 않는 쿼리
response = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "오늘 날씨 어때?"
})
# 응답: 4개 에이전트(employee/client/search/docs)의 설명과 사용 예시 제공
```

## 개발자 가이드

### 새 에이전트 추가하기

1. **에이전트 구현**
```python
# new_agent.py
class NewAgent:
    def run(self, query: str) -> Dict[str, Any]:
        # 에이전트 로직 구현
        return {"success": True, "result": "..."}
```

2. **router.py에 설정 추가**
```python
self.agents_config["new_agent"] = {
    "instance": NewAgent(),
    "metadata": {
        "description": "새 에이전트 설명",
        "capabilities": ["기능1", "기능2"],
        "examples": ["사용 예시1", "사용 예시2"]
    }
}
```

3. **실행 로직 추가**
```python
# _execute_agent 메서드에 추가
elif agent_name == "new_agent":
    result = agent.run(query)
    current_state["agent_type"] = agent_name
    return result
```

### 라우팅 정확도 향상

1. **메타데이터 개선**: 더 구체적인 설명과 예시 추가
2. **프롬프트 엔지니어링**: LLM 모델 또는 온도 조정
3. **키워드 필터링**: 특정 키워드에 대한 우선 라우팅 규칙 추가

### 테스트

```python
# test_router.py
from app.services.router_agent import RouterAgent

router = RouterAgent()

# 각 에이전트 테스트
test_queries = [
    "최수아 실적 보여줘",      # employee_agent
    "미라클신경과 분석해줘",    # client_agent
    "영업 규정 찾아줘",        # search_agent
    "보고서 작성해줘"          # docs_agent
]

for query in test_queries:
    result = router.run(query)
    print(f"Query: {query}")
    print(f"Agent: {result.get('agent_type')}")
    print("---")
```

## 문제 해결

### 일반적인 문제

1. **API 키 오류**
   - 환경 변수 OPENAI_API_KEY 설정 확인
   - API 키 유효성 확인

2. **라우팅 실패**
   - 쿼리를 더 구체적으로 작성
   - 에이전트 설명의 examples 참고

3. **세션 오류**
   - session_id가 유효한지 확인
   - 세션이 활성 상태인지 확인

### 로깅

```python
import logging
logging.basicConfig(level=logging.INFO)
```

디버그 정보는 로그에서 확인 가능합니다.

## 기여 방법

1. 이슈 등록
2. 기능 브랜치 생성
3. 코드 작성 및 테스트
4. Pull Request 제출

## 라이선스

내부 사용 전용 소프트웨어입니다.