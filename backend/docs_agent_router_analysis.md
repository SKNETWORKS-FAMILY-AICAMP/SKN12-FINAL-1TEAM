# Docs Agent와 Router 간 호환성 문제 분석

## 1. 주요 문제점

### 1.1 콘솔/API 모드 호환성 문제

**현재 상황:**
- `docs_agent`는 기본적으로 콘솔 모드로 작동하며, 인터럽트 시 `input()` 함수로 사용자 입력을 받음
- `router`는 `NO_INPUT_MODE` 환경변수를 설정하여 API 모드로 실행하려 하지만, `docs_agent`는 이를 인식하지 못함
- 인터럽트 발생 시 `_handle_interactive_mode()`가 호출되어 `input()`을 대기하게 되어 API에서 블로킹됨

**문제 코드 위치:**
- `create_document_agent.py:1336` - 인터럽트 시 무조건 `_handle_interactive_mode()` 호출
- `create_document_agent.py:1358` - `input()` 함수로 사용자 입력 대기

### 1.2 State 전달 메커니즘 문제

**현재 상황:**
- `router`에서 `docs_agent`로 상태 정보가 제대로 전달되지 않음
- 인터럽트 정보(`next_node`, `doc_type`, `state_info`)가 router 레벨에서만 관리되고 있음
- `docs_agent`의 결과가 router로 돌아올 때 필요한 정보가 누락됨

**문제 코드 위치:**
- `router.py:193-224` - docs_agent 실행 시 상태 정보 전달 부족
- `router_api.py:108-119` - 하위 에이전트 결과 처리 시 정보 누락

### 1.3 LangGraph 실행 흐름 문제

**현재 상황:**
- 인터럽트 노드들(`receive_verification_input`, `receive_manual_doc_type_input`, `receive_user_input`)이 콘솔 입력을 기다림
- API 모드에서는 이러한 인터럽트를 처리할 수 있는 메커니즘이 없음
- 인터럽트 발생 시 적절한 정보를 반환하지 않고 블로킹됨

## 2. 세부 이슈 분석

### 2.1 큰 이슈

1. **API/콘솔 모드 분기 로직 부재**
   - docs_agent에 API 모드를 위한 별도 처리 로직이 없음
   - 환경변수나 파라미터로 모드를 구분하는 메커니즘 필요

2. **인터럽트 처리 방식 불일치**
   - 콘솔: 직접 input()으로 입력 받아 처리
   - API: 인터럽트 정보 반환 후 클라이언트가 재개 요청을 보내야 함

3. **상태 정보 손실**
   - router와 docs_agent 간 상태 정보가 유기적으로 전달되지 않음
   
   - 특히 인터럽트 관련 정보(next_node, doc_type 등)가 누락됨

### 2.2 작은 이슈

1. **로깅 및 디버깅 어려움**
   - print문과 logger가 혼재되어 사용됨
   - API 모드에서 print문이 적절하지 않을 수 있음

2. **에러 처리 일관성 부족**
   - 일부 경우 None 반환, 일부는 dict 반환
   - 에러 타입이 명확하지 않음

3. **thread_id 관리**
   - docs_agent는 자체적으로 thread_id를 생성
   - router에서 관리하는 session_id와 연계 필요

## 3. 수정 방향
 
### 3.1 API 모드 지원 추가

1. `CreateDocumentAgent` 클래스에 `api_mode` 파라미터 추가
2. `run()` 메서드에서 API 모드일 때 인터럽트 정보 반환
3. `_handle_api_interrupt()` 메서드 추가하여 API 모드 인터럽트 처리 
### 3.2 상태 정보 전달 개선

1. 인터럽트 시 필요한 모든 정보를 포함한 dict 반환
2. router에서 이 정보를 보존하고 클라이언트에 전달
3. resume 시 상태 정보를 올바르게 복원

### 3.3 에러 처리 표준화

1. 모든 반환값을 표준 형식으로 통일
2. 에러 타입을 명확히 구분 (validation_error, interrupt, success 등)
3. API 응답에 적합한 형태로 구조화

## 4. 구현 우선순위

1. **긴급**: API 모드 지원 추가 (인터럽트 시 블로킹 방지)
2. **높음**: 상태 정보 전달 메커니즘 개선
3. **중간**: 에러 처리 및 로깅 표준화
4. **낮음**: 코드 리팩토링 및 문서화