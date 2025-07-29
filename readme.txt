폴더구조

```
backend/
└── app/
    ├── main.py # FastAPI 실행
    │
    ├── api/ # API 관리
    │   └── router_api.py
    │
    ├── services/ # agent 관리
    │   ├── router_agent/
    │   │   ├── router_agent.py
    │   │   ├── state_graph_router.py
    │   │   └── memory_store_sqlite.py # 대화 저장/조회 기능 구현
    │   ├── *_agents/                    # *_agent 소스코드

database/
└── history/
    └── memory.sqlite                  # 대화 기록 저장

frontend/
└── react # 실행 : npm start , # 모듈 설치 : npm install 
```