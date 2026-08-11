# Backend App (Agent Server)

FastAPI 기반 멀티 에이전트 백엔드 서버입니다. 이 문서는 `backend/app/` 디렉토리의 실제 구조와 API를 정리합니다.

> 이 문서가 API 엔드포인트의 1차 출처입니다. 아키텍처 개요는 [`../../PROJECT_ARCHITECTURE.md`](../../PROJECT_ARCHITECTURE.md), [`../BACKEND_ARCHITECTURE.md`](../BACKEND_ARCHITECTURE.md)를 참고하세요.

## 실행

```bash
cd backend
uvicorn app.agent_server:app --reload --port 8000
```

필수 환경 변수(`.env`):
```
OPENAI_API_KEY=your_openai_api_key_here
```

서버 상태 확인:
- Health: `GET /health`
- API 목록: `GET /api-routes`
- Swagger UI: `http://localhost:8000/docs`

## 디렉토리 구조

```
backend/app/
├── agent_server.py          # FastAPI 엔트리포인트
├── models.py                 # SQLAlchemy 모델 (Employee, Schedule)
├── core/
│   └── config.py             # 중앙 설정 (Database API URL, JWT, OpenAI 키)
├── api/                       # API 라우터
│   ├── router_api.py         # 라우터 에이전트 API
│   ├── docs_agent_api.py     # 문서 작성 에이전트 API
│   ├── employee_agent_api.py # 직원 실적 분석 API
│   └── client_agent_api.py   # 거래처 분석 API
└── services/                  # 에이전트 구현
    ├── router_agent/          # 질문 분류 및 라우팅
    ├── employee_agent/        # 직원 실적 분석
    ├── client_agent/          # 거래처 분석
    ├── docs_agent/            # 문서 자동 생성
    ├── search_agent/          # 정보 검색 (router_agent를 통해서만 호출, 독자 API 라우터 없음)
    ├── common/                # 공통 유틸리티 (대화 저장, 컨텍스트 관리 등)
    └── tools/                 # 계산/분석 공통 도구
```

## API 엔드포인트

### Router Agent API (`app.include_router(router_api, prefix="/api/v1")`)
| 메소드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/chat` | 사용자 메시지를 분석해 적절한 에이전트로 라우팅 |
| POST | `/api/v1/resume/{session_id}` | 세션 재개 |
| GET | `/api/v1/status/{session_id}` | 세션 상태 조회 |
| GET | `/api/v1/health` | Router Agent 헬스 체크 |
| GET | `/api/v1/agents` | 사용 가능한 에이전트 목록 |
| GET | `/api/v1/chat/history/{session_id}` | 세션 대화 기록 조회 |
| GET | `/api/v1/chat/sessions/user/{employee_id}` | 사용자별 세션 목록 조회 |

### Docs Agent API (`app.include_router(docs_router, prefix="/api/v1/docs")`)
| 메소드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/docs/chat` | 문서 작성 요청 |
| POST | `/api/v1/docs/resume/{session_id}` | 문서 작성 세션 재개 |
| GET | `/api/v1/docs/status/{session_id}` | 문서 작성 세션 상태 조회 |
| GET | `/api/v1/docs/health` | Docs Agent 헬스 체크 |
| GET | `/api/v1/docs/templates` | 지원 문서 템플릿 목록 |
| POST | `/api/v1/docs/create-document` | 문서 생성 |

### Employee Agent API (`app.include_router(employee_router, prefix="/api/employee")`)
| 메소드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/employee/analyze` | 직원 실적 분석 |
| GET | `/api/employee/list` | 직원 목록 조회 |
| POST | `/api/employee/performance` | 실적 데이터 조회 |
| POST | `/api/employee/target` | 목표 달성률 조회 |
| GET | `/api/employee/dashboard-stats` | 대시보드 통계 조회 |

### Client Agent API (`app.include_router(client_agent_router, prefix="/api/v1")`, 파일 자체가 `APIRouter(prefix="/client")`를 가짐)
| 메소드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/v1/client/analyze` | 거래처 분석 |
| GET | `/api/v1/client/health` | Client Agent 헬스 체크 |

### 공통 (agent_server.py)
| 메소드 | 경로 | 설명 |
|---|---|---|
| GET | `/health` | 서버 상태 확인 |
| GET | `/api-routes` | 등록된 API 목록 조회 |

## 참고

- 채팅 대화 저장은 `services/common/conversation_storage.py`가 담당하며, HTTP로 Database API 서버(`/api/chat-history/*`, 기본 8010)에 위임합니다.
- Database API 서버 자체(PostgreSQL/OpenSearch/MinIO 연동 등)의 소스는 이 레포에 포함되어 있지 않습니다.
