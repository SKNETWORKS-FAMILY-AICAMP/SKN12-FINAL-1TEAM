# Search Agent 아키텍처 및 프론트엔드 통합 가이드

## 📋 개요

Search Agent는 사용자의 자연어 검색 쿼리를 처리하는 LLM 기반 검색 시스템입니다. 프론트엔드 채팅 인터페이스에서 자동으로 호출되며, 데이터베이스와 문서를 동시에 검색하여 통합된 응답을 제공합니다.

## 🏗️ 전체 시스템 아키텍처

```
[Frontend (3000)]
    ↓
[ChatBot.js] → POST /api/v1/chat
    ↓
[Proxy (setupProxy.js)] → 8000 포트로 라우팅
    ↓
[Agent Server (8000)]
    ↓
[Router Agent] → 쿼리 분석 및 에이전트 선택
    ↓
[Search Agent] → LangGraph React Agent
    ↓
[검색 도구 선택]
    ├── Text2SQLSearch → Database API (8010)
    ├── OpenSearchDoc → Database API (8010)
    └── IntegratedSearch → 통합 검색
```

## 🔄 프론트엔드에서 Search Agent 호출 과정

### 1. 사용자 입력 (ChatBot.js)

```javascript
// frontend/src/components/ChatBot.js
const sendMessage = async () => {
    const requestBody = { 
        message: currentQuery,
        session_id: sessionId
    };
    
    // Router Agent로 요청
    const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    });
}
```

### 2. 프록시 라우팅 (setupProxy.js)

```javascript
// frontend/src/setupProxy.js
const agentPaths = [
    '/api/v1',  // Router Agent API
    // ...
];

// /api/v1/* → http://localhost:8000/api/v1/*
```

### 3. Router Agent 처리 (router.py)

Router Agent가 쿼리를 분석하여 4개 에이전트 중 선택:

```python
# backend/app/services/router_agent/router.py
self.agents_config = {
    "search_agent": {
        "metadata": {
            "description": "내부 데이터베이스에서 정보 검색을 수행합니다",
            "capabilities": [
                "문서 검색",
                "사내 규정 및 정책 조회",
                "업무 매뉴얼 검색",
                "제품 정보 조회",
                "교육 자료 검색"
            ],
            "examples": [
                "영업 규정 찾아줘",
                "제품 설명서 검색",
                "교육 자료 조회"
            ]
        }
    },
    # employee_agent, client_agent, docs_agent...
}
```

### 4. Search Agent 실행 트리거

Router가 search_agent를 선택하면:

```python
# backend/app/services/router_agent/router.py
elif agent_name == "search_agent":
    result = asyncio.run(search_agent_run(query, session_id or "default"))
```

## 🤖 Search Agent 내부 동작

### 1. 진입점 (run.py)

```python
# backend/app/services/search_agent/run.py
async def run(query: str, session_id: str, api_token: Optional[str] = None):
    # 1. 에이전트 생성
    agent = create_search_agent(api_token=api_token)
    
    # 2. LangGraph React Agent 생성
    app = agent.create_agent()
    
    # 3. LLM 기반 도구 선택 및 실행
    initial_state = {
        "messages": [{"role": "user", "content": query}],
        "next": "agent"
    }
    result = app.invoke(initial_state)
    
    # 4. 자연어 응답 반환
    return {
        "success": True,
        "response": response,
        "agent": "search_agent",
        "session_id": session_id
    }
```

### 2. 검색 도구 정의 (search_agent.py)

```python
# backend/app/services/search_agent/search_agent.py
def create_tools(self) -> List[Tool]:
    return [
        Tool(
            name="Text2SQLSearch",
            func=self.call_text2sql_api,
            description="""구조화된 데이터베이스 검색:
            - 인사 정보: "최수아 직원 정보", "급여 내역"
            - 매출/실적: "2024년 매출", "분기별 실적"
            - 고객/거래처: "삼성병원 거래내역"
            - 구체적인 수치와 통계"""
        ),
        Tool(
            name="OpenSearchDoc",
            func=self.call_opensearch_api,
            description="""문서 검색 시스템:
            - 계약서/문서: "계약서", "보고서", "공지사항"
            - 규정/정책: "근무 규정", "회사 정책"
            - 관련 내용: "FDA 승인", "신약 개발"
            - 일반 문서 질문: "어떻게", "무엇", "왜""""
        ),
        Tool(
            name="IntegratedSearch",
            func=self.call_all_search_api,
            description="""통합 검색:
            - 포괄적인 정보 요청
            - 여러 소스 필요한 경우
            - 특정 대상의 종합 정보"""
        )
    ]
```

### 3. LLM 기반 도구 선택

LangGraph React Agent가 자동으로:
1. 사용자 쿼리 의도 파악
2. 적절한 검색 도구 선택
3. API 호출 실행
4. 결과를 자연어로 변환

## 🔌 API 엔드포인트 매핑

### Agent Server (포트 8000)
- `/api/v1/chat` - Router Agent 진입점
- `/api/v1/resume/{session_id}` - 대화 재개

### Database API (포트 8010) 
Search Agent가 호출하는 검색 API:
- `/search/text2sql` - SQL 기반 데이터 검색
- `/search/opensearch` - 벡터 기반 문서 검색
- `/search/all` - 통합 검색
- `/search/stats` - 시스템 상태 확인

## 💬 실제 호출 시퀀스 예제

### 사용자: "영업 규정 및 가이드라인을 찾아줘"

1. **Frontend (ChatBot.js)**
   ```javascript
   POST /api/v1/chat
   {
     "message": "영업 규정 및 가이드라인을 찾아줘",
     "session_id": "session_1234"
   }
   ```

2. **Router Agent 분석**
   - LLM이 "규정", "가이드라인" 키워드 인식
   - search_agent 선택

3. **Search Agent 실행**
   - LLM이 "규정 문서" 의도 파악
   - OpenSearchDoc 도구 선택

4. **API 호출**
   ```python
   GET /search/opensearch?query=영업+규정+가이드라인&limit=20
   ```

5. **응답 생성**
   ```json
   {
     "success": true,
     "response": "영업 규정 관련 3개 문서를 찾았습니다:\n1. 영업활동 가이드라인 v2.0...",
     "agent": "search_agent",
     "session_id": "session_1234"
   }
   ```

## 🎯 Search Agent 선택 기준

Router Agent는 다음 경우에 Search Agent를 선택:

### ✅ Search Agent 적합 쿼리
- "규정 찾아줘"
- "계약서 검색"
- "FDA 승인 관련 문서"
- "교육 자료 조회"
- "제품 설명서"

### ❌ 다른 에이전트 선택 쿼리
- "최수아 실적 분석" → employee_agent
- "미라클신경과 매출" → client_agent
- "영업보고서 작성" → docs_agent

## 🔧 주요 특징

### 1. 완전 자동화
- 사용자는 자연어로 질문만 입력
- Router → Search Agent → 도구 선택이 모두 자동

### 2. LLM 기반 지능
- GPT-4가 쿼리 의도 정확히 파악
- 동의어, 복잡한 문장 이해 가능
- 하드코딩 없이 유연한 처리

### 3. 통합 검색
- 구조화된 DB와 비구조화 문서 동시 검색
- 결과를 자연어로 통합하여 제공

### 4. 세션 관리
- session_id로 대화 연속성 유지
- 각 채팅방별 독립적 세션

## 📝 응답 처리 흐름

```python
# Search Agent 응답 생성 과정
def _generate_natural_response_opensearch(self, query, results, total_count):
    # 1. LLM에게 검색 결과 전달
    prompt = f"""
    질문: {query}
    문서 결과: {results[:3]}
    
    요구사항:
    1. 가장 관련성 높은 문서 위주로 설명
    2. 문서 제목과 주요 내용 포함
    3. 간결하고 명확한 설명
    """
    
    # 2. 자연어 응답 생성
    response = self.llm.invoke(prompt)
    return response.content
```

## 🚀 확장 가능성

### 새로운 검색 소스 추가
1. `search_agent.py`에 새 API 호출 메서드 추가
2. `create_tools()`에 새 Tool 등록
3. LLM이 자동으로 새 도구 학습 및 활용

### 검색 정확도 향상
1. Tool description 개선
2. 프롬프트 엔지니어링
3. Few-shot examples 추가

## 🐛 디버깅 팁

### 로그 확인 위치
- Router Agent 선택: `router.py`의 `_execute_agent()` 로그
- Search Agent 실행: `run.py`의 실행 로그
- API 호출: `search_agent.py`의 각 API 메서드 로그

### 일반적인 문제 해결
1. **Search Agent가 선택되지 않음**
   - Router Agent의 agents_config 확인
   - 쿼리가 검색 의도인지 확인

2. **잘못된 도구 선택**
   - Tool description 명확성 확인
   - LLM 모델 버전 확인

3. **API 호출 실패**
   - Database API (8010) 실행 상태 확인
   - JWT 토큰 유효성 확인
   - 네트워크 연결 확인

## 📚 관련 파일

- **Frontend**
  - `/frontend/src/components/ChatBot.js` - 채팅 UI
  - `/frontend/src/setupProxy.js` - 프록시 설정

- **Backend**
  - `/backend/app/services/search_agent/search_agent.py` - 핵심 로직
  - `/backend/app/services/search_agent/run.py` - 실행 진입점
  - `/backend/app/services/router_agent/router.py` - 라우터 통합
  - `/backend/app/agent_server.py` - FastAPI 서버

- **Configuration**
  - `/backend/app/core/config.py` - 중앙 설정
  - `.env` - 환경 변수 (OPENAI_API_KEY 등)

---

이 문서는 Search Agent의 전체 아키텍처와 프론트엔드 통합을 설명합니다. 
다음에 이 코드를 읽을 때 이 문서를 참고하면 시스템을 빠르게 이해할 수 있습니다.