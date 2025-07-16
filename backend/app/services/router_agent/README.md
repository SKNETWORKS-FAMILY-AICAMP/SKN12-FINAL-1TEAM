# LangGraph 기반 라우터 시스템

NaruTalk AI 챗봇을 위한 LangGraph StateGraph 기반 라우터 시스템입니다.

## 🎯 주요 기능

- **GPT-4o 기반 에이전트 분류**: 사용자 질문을 4개의 전문 에이전트로 자동 분류
- **LangGraph StateGraph**: 상태 기반 흐름 제어 및 조건부 분기
- **재시도 로직**: 최대 3회까지 자동 재시도
- **수동 선택 모드**: 분류 실패 시 H2H(Human-to-Human) 모드로 전환
- **더미 에이전트**: 각 에이전트별 더미 실행 및 테스트

## 🤖 지원 에이전트

1. **employee_agent**: 직원 실적 분석, 인사 정보, 조직도 관련 업무
2. **client_agent**: 거래처 분석, 고객 데이터 분석, 매출 분석
3. **db_agent**: 데이터베이스 검색, 문서 검색, 정보 조회
4. **docs_agent**: 문서 자동생성, 규정 위반 여부 분석, 컴플라이언스 검토

## 📁 파일 구조

```
backend/app/services/router_agent/
├── __init__.py              # 모듈 초기화
├── router_agent.py          # 기본 라우터 에이전트
├── state_graph_router.py    # StateGraph 기반 라우터
└── README.md               # 이 파일
```

## 🚀 사용법

### 1. 기본 라우터 사용

```python
from backend.app.services.router_agent import RouterAgent

router = RouterAgent()
result = router.process_query("김철수 직원의 이번 달 실적을 분석해주세요")
print(result)
```

### 2. StateGraph 라우터 사용

```python
from backend.app.services.router_agent import StateGraphRouter

state_router = StateGraphRouter()
result = state_router.process_query("ABC 거래처의 매출 현황을 알려주세요")
print(result)
```

## 🔄 StateGraph 흐름

```
┌─────────┐
│  START  │ → 초기화 및 사용자 질문 출력
└────┬────┘
     │
     ▼
┌─────────┐
│CLASSIFY │ → GPT-4o를 사용한 에이전트 분류
└────┬────┘
     │
     ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│  ROUTE  │◄───┤DECISION │───►│  RETRY  │
└────┬────┘    └─────────┘    └────┬────┘
     │                             │
     ▼                             ▼
┌─────────┐                   ┌─────────┐
│EXECUTE  │                   │CLASSIFY │
└────┬────┘                   └─────────┘
     │
     ▼
┌─────────┐
│FINALIZE │ → 결과 정리 및 완료
└────┬────┘
     │
     ▼
┌─────────┐
│   END   │
└─────────┘
```

## 📋 출력 형식

시스템은 다음 3단계 형식으로 출력됩니다:

1. **Step 1**: 사용자 질문 출력
2. **Step 2**: LLM 분류 결과 출력
3. **Step 3**: 분기된 에이전트 이름 출력

## 🧪 테스트

```bash
# 테스트 스크립트 실행
python test_router_system.py
```

## ⚙️ 설정

### 환경 변수

```bash
export OPENAI_API_KEY=your_api_key_here
```

### 설정 옵션

- `max_retry_attempts`: 최대 재시도 횟수 (기본값: 3)
- `openai_model`: 사용할 OpenAI 모델 (기본값: "gpt-4o")
- `temperature`: GPT-4o 온도 설정 (기본값: 0.3)

## 📊 상태 관리

### RouterState 클래스

```python
@dataclass
class RouterState:
    query: str = ""                    # 사용자 질문
    selected_agent: Optional[str] = None  # 선택된 에이전트
    routing_attempts: int = 0          # 시도 횟수
    final_response: str = ""           # 최종 응답
    classification_result: str = ""    # 분류 결과
    error_message: str = ""            # 오류 메시지
```

### GraphState 클래스

```python
class GraphState(TypedDict):
    query: str
    selected_agent: Optional[str]
    routing_attempts: int
    final_response: str
    classification_result: str
    error_message: str
    next_action: str
    is_completed: bool
```

## 🔧 확장 가능성

새로운 에이전트를 추가하려면:

1. `available_agents` 리스트에 추가
2. `agent_descriptions`에 설명 추가
3. `execute_dummy_agent` 메서드에 더미 동작 추가

## 📈 성능 최적화

- GPT-4o 모델 사용으로 빠른 분류 성능
- 재시도 로직으로 안정성 향상
- StateGraph를 통한 효율적인 상태 관리
- 로깅 시스템으로 디버깅 지원

## 🛠️ 개발 참고사항

- Python 3.11.9 호환
- LangGraph 0.5+ 지원
- OpenAI API 1.86.0+ 필요
- 비동기 처리 지원 가능 (향후 업데이트) 