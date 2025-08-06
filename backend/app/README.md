# Multi-Agent Document Creation API

LangGraph 기반 멀티에이전트 문서 작성 시스템입니다. 자동 에이전트 라우팅과 docs_agent 직접 호출을 모두 지원합니다.

## 🚀 시작하기

### 1. 환경 설정

프로젝트 루트 또는 `backend/app/` 디렉토리에 `.env` 파일을 생성하세요:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### 2. 서버 실행

```bash
cd backend/app
python main.py
```

서버가 실행되면 다음 URL에서 확인할 수 있습니다:
- 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/health

## 📋 API 엔드포인트

### 🔄 멀티에이전트 라우터 API (`/api/v1/`)

사용자 메시지를 분석하여 적절한 에이전트로 자동 라우팅합니다.

#### `POST /api/v1/chat`

**언제 사용하나요?**
- 어떤 에이전트를 사용할지 확실하지 않을 때
- 시스템이 자동으로 적절한 에이전트를 선택하게 하고 싶을 때
- 다양한 종류의 요청을 처리할 때

**요청 예시:**
```json
{
  "message": "영업방문 결과보고서 작성해줘",
  "session_id": "optional-session-id"
}
```

**응답 예시:**
```json
{
  "success": true,
  "session_id": "uuid-session-id",
  "target_agent": "docs_agent",
  "requires_interrupt": true,
  "response": "분류된 문서 타입: 영업방문 결과보고서\n\n위 분류 결과가 올바른가요?",
  "data": {
    "thread_id": "uuid-thread-id",
    "next_node": "process_verification_response",
    "doc_type": "영업방문 결과보고서",
    "interrupt_type": "verification"
  }
}
```

#### `POST /api/v1/resume/{session_id}`

**언제 사용하나요?**
- `requires_interrupt: true` 응답을 받은 후
- 사용자가 추가 정보를 입력했을 때
- 인터럽트된 세션을 계속 진행하고 싶을 때

**요청 예시:**
```json
{
  "user_reply": "네, 맞습니다",
  "reply_type": "verification_reply"
}
```

### 📝 Docs Agent 전용 API (`/api/v1/docs/`)

docs_agent를 직접 호출하여 문서 작성을 처리합니다.

#### `POST /api/v1/docs/chat`

**언제 사용하나요?**
- 문서 작성만 필요할 때
- 라우팅 과정을 건너뛰고 싶을 때
- docs_agent의 성능을 직접 테스트하고 싶을 때

**요청 예시:**
```json
{
  "message": "제품설명회 시행 신청서를 만들어주세요",
  "session_id": "optional-session-id"
}
```

#### `POST /api/v1/docs/resume/{session_id}`

**언제 사용하나요?**
- docs_agent에서 인터럽트가 발생한 후
- 추가 정보 입력이나 선택이 필요할 때

## 🎭 인터럽트 시나리오

### 시나리오 1: 문서 타입 검증

1. **초기 요청**
```bash
POST /api/v1/chat
{
  "message": "영업방문 결과보고서 작성해줘"
}
```

2. **인터럽트 응답**
```json
{
  "requires_interrupt": true,
  "response": "분류된 문서 타입: 영업방문 결과보고서\n\n위 분류 결과가 올바른가요?",
  "data": {
    "interrupt_type": "verification",
    "next_node": "process_verification_response"
  }
}
```

3. **사용자 확인**
```bash
POST /api/v1/resume/{session_id}
{
  "user_reply": "네, 맞습니다",
  "reply_type": "verification_reply"
}
```

### 시나리오 2: 수동 문서 타입 선택

1. **분류 실패 시 인터럽트**
```json
{
  "requires_interrupt": true,
  "response": "문서 타입을 선택해주세요.",
  "data": {
    "prompt_type": "manual_doc_selection",
    "options": [
      {"value": "1", "label": "영업방문 결과보고서"},
      {"value": "2", "label": "제품설명회 시행 신청서"},
      {"value": "3", "label": "제품설명회 시행 결과보고서"},
      {"value": "4", "label": "종료"}
    ]
  }
}
```

2. **사용자 선택**
```bash
POST /api/v1/resume/{session_id}
{
  "user_reply": "1",
  "reply_type": "verification_reply"
}
```

### 시나리오 3: 데이터 입력

1. **필드 입력 요청**
```json
{
  "requires_interrupt": true,
  "response": "다음 항목들을 입력해주세요:\n\n1. 방문날짜\n2. 고객명\n3. 방문목적...",
  "data": {
    "interrupt_type": "data_input",
    "template_content": "필수 입력 필드 안내..."
  }
}
```

2. **사용자 데이터 입력**
```bash
POST /api/v1/resume/{session_id}
{
  "user_reply": "방문날짜: 2024-01-15\n고객명: ABC회사\n방문목적: 신제품 소개...",
  "reply_type": "user_reply"
}
```

3. **최종 완료**
```json
{
  "success": true,
  "response": "문서가 성공적으로 생성되었습니다.",
  "data": {
    "document_path": "/path/to/document.docx",
    "document_type": "영업방문 결과보고서",
    "filled_data": { /* 입력된 데이터 */ }
  }
}
```

## 🔧 응답 형태

### 성공 응답
```json
{
  "success": true,
  "session_id": "session-uuid",
  "response": "처리 완료 메시지",
  "data": {
    "document_path": "/path/to/file.docx",
    "filled_data": { /* 구조화된 데이터 */ }
  }
}
```

### 인터럽트 응답
```json
{
  "success": false,
  "session_id": "session-uuid",
  "requires_interrupt": true,
  "response": "사용자 입력 요청 메시지",
  "data": {
    "thread_id": "thread-uuid",
    "next_node": "노드명",
    "interrupt_type": "verification|manual_selection|data_input"
  }
}
```

### 오류 응답
```json
{
  "success": false,
  "session_id": "session-uuid",
  "error": "오류 메시지"
}
```

## 📊 지원 문서 타입

1. **영업방문 결과보고서**
   - 고객 방문 후 영업 결과 보고
   - 필수 필드: 방문날짜, 고객명, 방문목적, 주요내용, 결과, 후속조치

2. **제품설명회 시행 신청서**
   - 제품설명회 개최 신청
   - 필수 필드: 제품명, 일시, 장소, 참석인원, 목적, 내용

3. **제품설명회 시행 결과보고서**
   - 제품설명회 완료 후 결과 보고
   - 필수 필드: 제품명, 일시, 장소, 참석인원, 진행내용, 결과, 피드백

## 🛡️ 규정 준수

시스템은 입력된 내용에 대해 자동으로 규정 위반 검사를 수행합니다:

- **규정 위반 시**: 분석은 완료되지만 파일 생성이 차단됩니다
- **위반 내용**: 응답에 포함되어 사용자에게 안내됩니다
- **API 모드**: 위반이 있어도 분석 결과는 제공됩니다

## 🔍 디버깅

### 세션 상태 확인
```bash
GET /api/v1/status/{session_id}
GET /api/v1/docs/status/{session_id}
```

### 헬스 체크
```bash
GET /api/v1/health
GET /api/v1/docs/health
```

### 지원 에이전트 확인
```bash
GET /api/v1/agents
```

### 문서 템플릿 확인
```bash
GET /api/v1/docs/templates
```

## ⚠️ 주의사항

1. **세션 관리**: 인터럽트 발생 시 `session_id`를 반드시 저장하고 재사용하세요
2. **reply_type**: 상황에 따라 `verification_reply` 또는 `user_reply` 구분하여 사용
3. **API 키**: `.env` 파일은 버전 관리에 포함하지 마세요
4. **파일 경로**: 생성된 문서는 `services/docs_agent/agent_result_folder/`에 저장됩니다

## 🤝 기여

이슈나 기능 제안이 있으시면 GitHub Issues를 이용해주세요.