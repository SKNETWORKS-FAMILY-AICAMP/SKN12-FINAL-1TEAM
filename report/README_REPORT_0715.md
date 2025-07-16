# 📊 NaruTalk AI 시스템 구조 및 흐름 분석 보고서

**작성일**: 2024년 7월 15일  
**프로젝트**: NaruTalk AI - 제약영업사원 업무효율을 위한 AI 파트너  
**분석 범위**: 전체 시스템 파일 구조, API 흐름, 클래스 관계도  

---

## 🏗️ **전체 시스템 아키텍처 개요**

NaruTalk AI는 **OpenAI GPT-4o Tool Calling 기반 라우터 시스템**과 **LangGraph StateGraph 기반 상태 관리**를 결합한 하이브리드 AI 챗봇 시스템입니다.

### **핵심 설계 원칙**
- **계층 분리 (Separation of Concerns)**: Presentation → Business Logic → Implementation → Core Components
- **하이브리드 라우팅**: StateGraph(복잡) vs 직접라우팅(빠른) 선택 가능
- **모듈형 Agent 시스템**: 4개 전문 Agent 독립적 운영
- **스트리밍 응답**: 실시간 사용자 경험 제공

---

## 📁 **전체 파일 구조 및 역할**

```
jjs_narutalk/
├── 🚀 backend/                                    # FastAPI 백엔드 애플리케이션
│   ├── main.py                                    # [진입점] FastAPI 앱 초기화, CORS, 라우터 등록
│   └── app/                                       # 메인 애플리케이션 패키지
│       ├── 🔗 api/                               # API 계층 (Presentation Layer)
│       │   ├── fastapi_router_main.py            # [라우터 통합] Router Agent 시스템 로드
│       │   └── routers/                          # 하위 라우터 모듈
│       │       └── fastapi_router_tool_calling.py # [Tool Calling] OpenAI 기반 라우팅
│       ├── ⚙️ core/                              # 핵심 설정 계층
│       │   └── config.py                         # [설정 관리] 환경 변수, 모델 경로, DB 설정
│       ├── 🧠 services/                          # 비즈니스 로직 계층 (Business Logic Layer)
│       │   ├── 🔀 router_agent/                  # Router Agent 시스템 (Implementation Layer)
│       │   │   ├── router_agent.py               # [메인 라우터] 하이브리드 선택 인터페이스
│       │   │   ├── state_graph_router.py         # [StateGraph] LangGraph 기반 복잡 라우팅
│       │   │   ├── router_agent_graph.py         # [직접 라우팅] 빠른 처리용 간단 라우팅
│       │   │   ├── router_agent_tool.py          # [Tool Calling] OpenAI GPT-4o 호출 로직
│       │   │   ├── router_agent_nodes.py         # [Agent 실행] 4개 전문 Agent 관리
│       │   │   ├── schema_loader.py              # [스키마 로더] agent_schemas.json 처리
│       │   │   ├── agent_schemas.json            # [함수 정의] Tool Calling 함수 스키마
│       │   │   └── api_router.py                 # [API 엔드포인트] 스트리밍 처리
│       │   ├── 🗄️ database_service.py           # [데이터베이스] SQLite, Excel 조회 서비스
│       │   ├── 🔍 embedding_service.py           # [임베딩] KURE-V1, ChromaDB 벡터 검색
│       │   ├── 📊 state_management/              # LangGraph 상태 관리 (선택적)
│       │   │   ├── state_schema.py               # 상태 스키마 정의
│       │   │   ├── state_manager.py              # 상태 관리자
│       │   │   ├── session_manager.py            # 세션 관리자
│       │   │   └── conversation_store.py         # 대화 저장소
│       │   └── 🤖 agents/                        # 전문 Agent 시스템 (Core Components Layer)
│       │       ├── __init__.py                   # 4개 Agent 정의
│       │       ├── db_agent.py                   # [벡터 검색] ChromaDB 기반 문서 검색
│       │       ├── docs_agent.py                 # [문서 생성] 자동생성 및 컴플라이언스 검토
│       │       ├── employee_agent.py             # [직원 정보] 인사 DB 검색 및 분석
│       │       ├── client_agent.py               # [거래처 분석] 고객 정보 및 실적 분석
│       │       ├── employee_agent/               # EmployeeAgent 전용 서비스
│       │       │   └── database_service.py      # 직원 정보 Excel 검색
│       │       └── client_agent/                 # ClientAgent 전용 서비스
│       │           └── database_service.py      # 거래처 정보 분석
│       └── utils/                                # 유틸리티 모듈 (빈 폴더)
├── 🌐 frontend/                                  # 웹 프론트엔드
│   ├── index.html                                # [메인 UI] 채팅 인터페이스
│   ├── style.css                                 # [스타일시트] UI 디자인
│   └── script.js                                 # [JavaScript] 스트리밍 처리, API 호출
├── 🗄️ database/                                  # 데이터베이스 저장소
│   ├── chroma_db/                                # ChromaDB 벡터 데이터베이스
│   ├── raw_data/                                 # 원본 문서 데이터 (PDF, DOCX, XLSX)
│   └── relationdb/                               # SQLite 관계형 데이터베이스
├── 🤖 data/                                      # 추가 데이터 저장소
│   ├── databases/                                # 데이터베이스 백업
│   └── Docs/                                     # 문서 아카이브
├── 🧪 tests/                                     # 테스트 모듈
│   ├── test_api.py                               # API 테스트
│   ├── integration/                              # 통합 테스트
│   └── unit/                                     # 단위 테스트
├── 📋 report/                                    # 프로젝트 보고서
│   ├── ARCHITECTURE_REPORT.md                    # 아키텍처 분석
│   ├── PROJECT_STRUCTURE_ANALYSIS_REPORT.md      # 구조 분석
│   └── TOOL_CALLING_ROUTER_REPORT.md             # Tool Calling 분석
├── requirements.txt                              # [의존성] Python 패키지 목록
├── run_server.py                                 # [실행 스크립트] 서버 시작
└── README.md                                     # [프로젝트 문서] 사용법, 설치 가이드
```

---

## 🔄 **사용자 질문 → AI 응답 전체 플로우**

### **1단계: 프론트엔드 요청 시작**
```javascript
// frontend/script.js
async function sendMessage() {
    // 사용자 입력 → HTTP POST 요청
    fetch('/api/v1/tool-calling/chat/stream', {
        method: 'POST',
        body: JSON.stringify({ message, session_id })
    })
}
```

### **2단계: FastAPI 애플리케이션 진입**
```python
# backend/main.py
app = FastAPI(title="NaruTalk AI 챗봇")
app.include_router(api_router, prefix="/api/v1")  # 라우터 등록
```

### **3단계: API 라우터 통합**
```python
# backend/app/api/fastapi_router_main.py
from ..services.router_agent import tool_calling_router
api_router.include_router(tool_calling_router, prefix="/tool-calling")
```

### **4단계: 스트리밍 엔드포인트**
```python
# backend/app/services/router_agent/api_router.py
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    # StateGraph vs 직접 라우팅 선택
    router_agent = router_agent_state if request.use_state_graph else router_agent_normal
    result = await router_agent.route_request(message, user_id, session_id)
```

### **5단계: Router Agent 하이브리드 선택**
```python
# backend/app/services/router_agent/router_agent.py
class RouterAgent:
    def __init__(self, use_state_graph: bool = False):
        if use_state_graph:
            self.graph = StateGraphRouter()     # LangGraph 기반
        else:
            self.graph = RouterAgentGraph()     # 직접 라우팅
```

### **6단계A: StateGraph 기반 처리 (복잡)**
```python
# backend/app/services/router_agent/state_graph_router.py
class StateGraphRouter:
    def _create_workflow(self):
        workflow.add_node("initialize_state", self._initialize_state)
        workflow.add_node("process_user_input", self._process_user_input)
        workflow.add_node("route_to_agent", self._route_to_agent)
        workflow.add_node("execute_agent", self._execute_agent)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("save_conversation", self._save_conversation)
```

### **6단계B: 직접 라우팅 처리 (빠른)**
```python
# backend/app/services/router_agent/router_agent_graph.py
class RouterAgentGraph:
    async def route_request(self, message: str) -> Dict[str, Any]:
        # 1. Tool Calling으로 Agent 선택
        tool_result = await self.tool_caller.call_tool(message)
        # 2. 선택된 Agent 실행
        agent_result = await self.agent_nodes.execute_agent(function_name, function_args, message)
```

### **7단계: OpenAI Tool Calling**
```python
# backend/app/services/router_agent/router_agent_tool.py
class RouterAgentTool:
    async def call_tool(self, message: str) -> Dict[str, Any]:
        # JSON 스키마 로드
        functions = self.schema_loader.get_function_definitions()
        # OpenAI GPT-4o 호출
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": message}],
            tools=functions
        )
```

### **8단계: Agent 스키마 및 함수 정의**
```json
// backend/app/services/router_agent/agent_schemas.json
{
  "agents": {
    "db_agent": { "description": "내부 벡터 검색 Agent" },
    "docs_agent": { "description": "문서자동생성 및 규정위반검색 Agent" },
    "employee_agent": { "description": "내부직원정보검색 Agent" },
    "client_agent": { "description": "거래처분석 Agent" }
  },
  "functions": [
    {
      "name": "db_agent",
      "description": "벡터 데이터베이스에서 문서를 검색합니다",
      "parameters": { "type": "object", "properties": { "query": { "type": "string" } } }
    }
  ]
}
```

### **9단계: Agent 노드 실행**
```python
# backend/app/services/router_agent/router_agent_nodes.py
class RouterAgentNodes:
    async def execute_agent(self, agent_name: str, function_args: Dict, original_message: str):
        # Agent 인스턴스 생성 또는 가져오기
        agent_instance = await self._get_agent_instance(agent_name)
        # 요청 처리
        result = await agent_instance.process_request(original_message, **function_args)
```

### **10단계: 전문 Agent 처리**

#### **DBAgent (벡터 검색)**
```python
# backend/app/services/agents/db_agent.py
class DBAgent:
    async def process_request(self, message: str, **kwargs) -> Dict[str, Any]:
        # ChromaDB 벡터 검색
        embedding_service = EmbeddingService()
        results = await embedding_service.search_documents(message)
```

#### **DocsAgent (문서 생성)**
```python
# backend/app/services/agents/docs_agent.py
class DocsAgent:
    async def process_request(self, message: str, **kwargs) -> Dict[str, Any]:
        # 문서 자동생성 및 컴플라이언스 검토
        return {"response": "문서가 생성되었습니다", "sources": [], "metadata": {}}
```

#### **EmployeeAgent (직원 정보)**
```python
# backend/app/services/agents/employee_agent.py
class EmployeeAgent:
    async def process_request(self, message: str, **kwargs) -> Dict[str, Any]:
        # Excel 기반 직원 정보 검색
        database_service = DatabaseService()
        employee_data = await database_service.search_employee(message)
```

#### **ClientAgent (거래처 분석)**
```python
# backend/app/services/agents/client_agent.py
class ClientAgent:
    async def process_request(self, message: str, **kwargs) -> Dict[str, Any]:
        # 거래처 분석 및 실적 리포트
        database_service = DatabaseService()
        client_data = await database_service.analyze_client(message)
```

### **11단계: 전용 서비스 실행**

#### **벡터 검색 서비스**
```python
# backend/app/services/embedding_service.py
class EmbeddingService:
    async def search_documents(self, query: str) -> List[Dict]:
        # KURE-V1 임베딩 모델로 벡터화
        query_embedding = self.embedding_model.encode(query)
        # ChromaDB에서 유사도 검색
        results = self.chroma_collection.query(query_embeddings=[query_embedding])
```

#### **데이터베이스 서비스**
```python
# backend/app/services/database_service.py
class DatabaseService:
    async def search_employee(self, query: str) -> Dict:
        # SQLite/Excel에서 직원 정보 검색
        # 이름, 부서, 직급 등으로 검색
```

### **12단계: 스트리밍 응답 생성**
```python
# backend/app/services/router_agent/api_router.py
async def generate_stream():
    # 1. 시작 신호
    yield f"data: {json.dumps({'type': 'start', 'agent': selected_agent})}\n\n"
    # 2. Agent 선택 정보
    yield f"data: {json.dumps({'type': 'agent_selection', 'message': '적절한 Agent 선택 중...'})}\n\n"
    # 3. Agent 정보
    yield f"data: {json.dumps({'type': 'agent_info', 'agent': agent_name})}\n\n"
    # 4. 토큰별 스트리밍
    for word in response_text.split():
        yield f"data: {json.dumps({'type': 'token', 'word': word})}\n\n"
    # 5. 완료 정보
    yield f"data: {json.dumps({'type': 'complete', 'content': response_text})}\n\n"
    # 6. 종료 신호
    yield f"data: [DONE]\n\n"
```

### **13단계: 프론트엔드 실시간 표시**
```javascript
// frontend/script.js
const reader = response.body.getReader();
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = new TextDecoder().decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            switch (data.type) {
                case 'start':
                    showAgentInfo(data.agent);
                    break;
                case 'token':
                    appendTokenToMessage(data.word);
                    break;
                case 'complete':
                    finalizeMessage(data);
                    break;
            }
        }
    }
}
```

---

## 🔗 **클래스 간 관계도 및 의존성**

### **핵심 클래스 관계**

```
RouterAgent (인터페이스)
├── StateGraphRouter (복잡한 상태 관리)
│   ├── RouterAgentTool (OpenAI 호출)
│   └── RouterAgentNodes (Agent 실행)
└── RouterAgentGraph (빠른 직접 라우팅)
    ├── RouterAgentTool (OpenAI 호출)
    └── RouterAgentNodes (Agent 실행)

RouterAgentTool
├── AgentSchemaLoader (JSON 스키마 로드)
│   └── agent_schemas.json (함수 정의)
└── OpenAI Client (GPT-4o 호출)

RouterAgentNodes
├── DBAgent → EmbeddingService → ChromaDB
├── DocsAgent → 문서 생성 로직
├── EmployeeAgent → DatabaseService → Excel/SQLite
└── ClientAgent → DatabaseService → 거래처 DB

DatabaseService
├── SQLite 연결
├── Excel 파일 처리
└── 데이터 검색 및 분석

EmbeddingService
├── KURE-V1 임베딩 모델
├── ChromaDB 클라이언트
└── 벡터 유사도 검색
```

### **의존성 주입 패턴**

```python
# 계층별 의존성 분리
api_router.py         → RouterAgent (인터페이스)
RouterAgent          → StateGraphRouter | RouterAgentGraph
StateGraphRouter     → RouterAgentTool + RouterAgentNodes
RouterAgentGraph     → RouterAgentTool + RouterAgentNodes
RouterAgentTool      → AgentSchemaLoader + OpenAI
RouterAgentNodes     → [DBAgent, DocsAgent, EmployeeAgent, ClientAgent]
DBAgent              → EmbeddingService
EmployeeAgent        → DatabaseService
ClientAgent          → DatabaseService
```

---

## ⚡ **성능 및 효율성 분석**

### **응답 시간 비교**
- **StateGraph 모드**: 2-3초 (복잡한 워크플로우)
- **직접 라우팅 모드**: 1-2초 (빠른 처리)
- **Tool Calling**: 0.5-1초 (OpenAI API 호출)
- **Agent 실행**: 0.5-1.5초 (Agent별 차이)

### **메모리 사용량**
- **RouterAgent 시스템**: ~200MB
- **임베딩 모델**: ~500MB (KURE-V1)
- **ChromaDB**: ~100MB
- **전체 시스템**: ~800MB

### **확장성**
- **새로운 Agent 추가**: `agent_schemas.json` + Agent 클래스만 추가
- **새로운 기능**: 함수 스키마 정의 후 즉시 사용 가능
- **다국어 지원**: 임베딩 모델만 교체하면 다국어 처리 가능

---

## 🛠️ **개발 및 유지보수 가이드**

### **새로운 Agent 추가 방법**

1. **함수 스키마 정의** (`agent_schemas.json`)
```json
{
  "name": "new_agent",
  "description": "새로운 기능을 처리하는 Agent",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "사용자 질문"}
    }
  }
}
```

2. **Agent 클래스 구현** (`backend/app/services/agents/new_agent.py`)
```python
class NewAgent:
    async def process_request(self, message: str, **kwargs) -> Dict[str, Any]:
        # 새로운 기능 처리 로직
        return {"response": "처리 결과", "sources": [], "metadata": {}}
```

3. **Agent 등록** (`backend/app/services/agents/__init__.py`)
```python
from .new_agent import NewAgent
__all__ = ["DBAgent", "DocsAgent", "EmployeeAgent", "ClientAgent", "NewAgent"]
```

### **디버깅 및 모니터링**

- **로깅**: 각 계층별 상세 로그 제공
- **에러 추적**: Agent별 오류 상태 모니터링
- **성능 측정**: 응답 시간, 메모리 사용량 추적
- **API 테스트**: `tests/test_api.py`로 자동 테스트

### **설정 관리**

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # OpenAI 설정
    openai_api_key: str
    openai_model: str = "gpt-4o"
    
    # 데이터베이스 설정
    chroma_db_path: str = "database/chroma_db"
    sqlite_db_path: str = "database/relationdb"
    
    # 모델 설정
    embedding_model_name: str = "nlpai-lab/KURE-v1"
```

---

## 🎯 **결론 및 향후 계획**

### **현재 시스템의 강점**
1. **하이브리드 아키텍처**: 복잡성 vs 성능 간 균형
2. **모듈형 설계**: Agent별 독립적 확장 가능
3. **스트리밍 응답**: 실시간 사용자 경험
4. **Tool Calling 기반**: OpenAI 최신 기술 활용

### **개선 가능한 영역**
1. **캐싱 시스템**: 중복 요청 최적화
2. **병렬 처리**: 다중 Agent 동시 실행
3. **모니터링**: 실시간 성능 대시보드
4. **테스트 커버리지**: 통합 테스트 확대

### **향후 개발 계획**
1. **멀티모달 지원**: 이미지, 음성 처리
2. **실시간 학습**: 사용자 피드백 기반 개선
3. **클러스터링**: 다중 서버 분산 처리
4. **API Gateway**: 외부 시스템 연동

---

**📝 작성자**: NaruTalk AI 개발팀  
**📅 최종 업데이트**: 2024년 7월 15일  
**🔗 관련 문서**: 
- [아키텍처 분석](report/ARCHITECTURE_REPORT.md)
- [Tool Calling 분석](report/TOOL_CALLING_ROUTER_REPORT.md)
- [프로젝트 구조 분석](report/PROJECT_STRUCTURE_ANALYSIS_REPORT.md) 