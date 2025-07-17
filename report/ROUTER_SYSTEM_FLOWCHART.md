# 라우터 시스템 흐름도

## 1. 전체 시스템 흐름도
사용자 질문부터 최종 응답까지의 전체 흐름을 보여줍니다.

### 주요 구성 요소
- **사용자 입력**: Streamlit UI를 통한 질문 입력
- **FastAPI**: REST API 엔드포인트
- **StateGraphRouter**: LangGraph 기반 상태 관리
- **RouterAgent**: GPT-4o 기반 분류 로직
- **에이전트 실행**: 더미 에이전트 실행

### 흐름 설명
1. 사용자가 Streamlit UI에서 질문 입력
2. FastAPI `/api/v1/route/graph` 엔드포인트 호출
3. StateGraphRouter가 질문을 처리
4. RouterState 객체 생성 및 초기화
5. classify_with_llm 노드에서 GPT-4o 분류 시작
6. 분류 성공 시 해당 에이전트 실행
7. 분류 실패 시 재시도 또는 H2H 모드 진입
8. 최종 결과를 Streamlit UI에 표시

## 2. LangGraph 노드 및 함수 관계도
LangGraph StateGraph의 노드들과 RouterAgent 함수들, RouterState 필드들의 관계를 보여줍니다.

### 노드별 역할
- **classify_with_llm**: GPT-4o를 사용한 질문 분류
- **retry_classification**: 재시도 로직 처리
- **h2h_manual_selection**: 수동 선택 모드
- **route_to_agent**: 선택된 에이전트로 라우팅
- **execute_selected_agent**: 에이전트 실행

### 함수별 역할
- **classify_query**: GPT-4o API 호출 및 분류
- **extract_agent_from_response**: 응답에서 에이전트명 추출
- **execute_dummy_agent**: 더미 에이전트 실행
- **fallback_to_h2h**: H2H 모드 처리

### 상태 필드
- **query**: 사용자 질문
- **selected_agent**: 선택된 에이전트
- **routing_attempts**: 시도 횟수
- **final_response**: 최종 응답
- **classification_result**: 분류 결과
- **error_message**: 오류 메시지

## 3. 에이전트 분류 및 재시도 로직
4가지 에이전트 분류 과정과 재시도 로직을 보여줍니다.

### 4가지 에이전트
1. **employee_agent**: 직원 정보 관련 질문 처리
2. **client_agent**: 고객/거래처 관련 질문 처리
3. **db_agent**: 데이터베이스 검색 관련 질문 처리
4. **docs_agent**: 문서 생성/검토 관련 질문 처리

### 재시도 로직
- 최대 3회 재시도
- 3회 실패 시 H2H 수동 선택 모드
- 사용자 직접 선택 후 에이전트 실행

### 에이전트 실행
- 현재는 더미 구현 (print 문)
- 실제 구현 시 각 에이전트별 실제 기능 수행

## 기술적 특징

### LangGraph 활용
- 상태 기반 그래프 플로우 제어
- 조건부 분기 처리
- 체계적인 상태 관리

### GPT-4o 활용
- 자연어 질문 분류
- 구조화된 응답 파싱
- 에러 처리 및 재시도

### 모듈화 설계
- 각 컴포넌트 독립적 구현
- 테스트 가능한 구조
- 확장 가능한 아키텍처

## 성능 고려사항

### 장점
- 명확한 분류 체계
- 견고한 재시도 로직
- H2H 백업 메커니즘
- 체계적인 상태 관리

### 개선 방향
- 실제 에이전트 구현
- 웹 기반 H2H 인터페이스
- 성능 최적화
- 로깅 및 모니터링 강화

---
*문서 작성일: 2025-01-17*
*시스템 버전: v1.0.0* 