# 무한루프 문제 해결 보고서

## 문제 상황
- **증상**: 4개 에이전트와 관련 없는 질문이 들어올 때 무한루프 발생
- **원인**: 재시도 로직에서 3회 제한이 제대로 작동하지 않음
- **예상 동작**: 3회 재시도 후 H2H 모드로 전환

## 문제 분석

### 1. 원인 분석
1. **조건 분기 로직 문제**: `selected_agent`가 `None`일 때 조건 처리 불완전
2. **시도 횟수 관리 문제**: `routing_attempts` 업데이트가 불안정
3. **안전장치 부재**: 무한루프 방지 메커니즘 부족

### 2. 발생 시나리오
```
사용자 질문: "안녕하세요" (분류 불가능)
↓
GPT-4o 분류: "AGENT: none" 
↓
selected_agent: None
↓
조건 분기: routing_attempts < 3 → retry
↓
무한 반복...
```

## 해결 방안

### 1. classify_with_llm 함수 개선
**파일**: `backend/app/services/router_agent/state_graph_router.py`

#### 안전장치 추가
```python
# 3회 이상 시도한 경우 강제로 None 반환 (안전장치)
if current_attempts >= 3:
    logger.warning("⚠️ 3회 이상 시도 - 강제로 None 반환")
    return {
        "query": state['query'],
        "selected_agent": None,
        "routing_attempts": current_attempts,
        "final_response": state.get('final_response', ''),
        "classification_result": "MAX_ATTEMPTS_REACHED",
        "error_message": "최대 시도 횟수 초과"
    }
```

#### 시도 횟수 관리 개선
```python
# 수정 전
state_obj.routing_attempts += 1

# 수정 후
current_attempts = state.get('routing_attempts', 0)
new_attempts = current_attempts + 1
```

### 2. 조건 분기 함수 강화
```python
def classify_condition(state: GraphState) -> str:
    selected_agent = state.get('selected_agent')
    routing_attempts = state.get('routing_attempts', 0)
    
    # 에이전트가 성공적으로 선택된 경우
    if selected_agent is not None and selected_agent != "none" and selected_agent in router.available_agents:
        return "has_agent"
    # 3회 미만 시도한 경우 재시도
    elif routing_attempts < 3:
        return "retry"
    # 3회 이상 실패한 경우 H2H 모드
    else:
        return "h2h"
```

### 3. 로깅 강화
- 각 단계별 상세 로그 추가
- 시도 횟수 추적 강화
- 조건 분기 과정 시각화

## 수정된 로직 플로우

### 정상 동작 시나리오
```
1. 사용자 질문: "안녕하세요"
2. classify_with_llm: attempts=0 → 1
3. GPT-4o 분류: "AGENT: none"
4. selected_agent: None
5. 조건 분기: attempts=1 < 3 → retry
6. classify_with_llm: attempts=1 → 2
7. GPT-4o 분류: "AGENT: none"
8. selected_agent: None
9. 조건 분기: attempts=2 < 3 → retry
10. classify_with_llm: attempts=2 → 3
11. GPT-4o 분류: "AGENT: none"
12. selected_agent: None
13. 조건 분기: attempts=3 >= 3 → h2h
14. H2H 모드 진입
```

### 안전장치 동작
```
classify_with_llm 진입 시:
if current_attempts >= 3:
    강제로 None 반환 및 에러 메시지 설정
```

## 추가 개선사항

### 1. 타임아웃 메커니즘
```python
import time
from datetime import datetime, timedelta

class StateGraphRouter:
    def __init__(self):
        self.app = build_router_graph()
        self.timeout = 30  # 30초 타임아웃
    
    def process_query(self, query: str) -> dict:
        start_time = datetime.now()
        # ... 기존 로직 ...
        
        if datetime.now() - start_time > timedelta(seconds=self.timeout):
            raise TimeoutError("처리 시간 초과")
```

### 2. 재시도 간격 조정
```python
import time

def retry_classification(state: GraphState) -> GraphState:
    # 재시도 간 0.5초 대기
    time.sleep(0.5)
    return state
```

### 3. 상태 검증 강화
```python
def validate_state(state: GraphState) -> bool:
    required_fields = ['query', 'selected_agent', 'routing_attempts']
    return all(field in state for field in required_fields)
```

## 테스트 시나리오

### 1. 분류 불가능한 질문들
- "안녕하세요"
- "날씨가 어때요?"
- "점심 뭐 먹을까요?"
- "asdfasdf"

### 2. 예상 결과
- 3회 재시도 후 H2H 모드 진입
- 무한루프 발생 없음
- 적절한 에러 메시지 제공

## 현재 상태

### ✅ 해결된 문제
- 무한루프 방지 안전장치 추가
- 시도 횟수 관리 개선
- 조건 분기 로직 강화
- 상세 로깅 추가

### 🔧 개선된 기능
- 강제 종료 메커니즘
- 명확한 조건 분기
- 안전한 상태 관리
- 디버깅 용이성

### 📋 향후 개선사항
- 타임아웃 메커니즘 추가
- 재시도 간격 조정
- 상태 검증 강화
- 웹 기반 H2H 인터페이스

## 실행 방법

### 1. 서버 실행
```bash
python run_server.py
```

### 2. 테스트 실행
```bash
streamlit run streamlit_app.py
```

### 3. 분류 불가능한 질문 테스트
- "안녕하세요" 입력
- 3회 재시도 후 H2H 모드 확인

---
*보고서 작성일: 2025-01-17*
*수정 완료 시간: 오후 8:15* 