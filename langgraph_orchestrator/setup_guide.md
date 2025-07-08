# 🏥 QA Medical Agent 환경 설정 가이드

## 🚀 빠른 시작

### 1. 가상환경 활성화
```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# 또는 CMD
.venv\Scripts\activate.bat
```

### 2. 필수 패키지 설치
```bash
cd langgraph_orchestrator
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# OpenAI API 설정 (필수)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_GPT4O=gpt-4o
OPENAI_MODEL_GPT4O_MINI=gpt-4o-mini

# Anthropic API 설정 (선택사항)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-haiku-20240307

# 데이터베이스 설정
DATABASE_URL=sqlite:///./qa_medical.db

# 개발 모드 설정
DEBUG=true
DEVELOPMENT=true
```

## 🔑 API 키 획득 방법

### OpenAI API 키 (필수)
1. [OpenAI Platform](https://platform.openai.com/) 방문
2. 계정 생성 또는 로그인
3. API Keys 메뉴에서 새 키 생성
4. 생성된 키를 `.env` 파일에 추가

### Anthropic API 키 (선택사항)
1. [Anthropic Console](https://console.anthropic.com/) 방문
2. 계정 생성 또는 로그인
3. API Keys에서 새 키 생성
4. 생성된 키를 `.env` 파일에 추가

## 🧪 테스트 실행

### 1. 기본 구조 테스트 (API 키 불필요)
```bash
python test_structure.py
```

### 2. Mock API 워크플로우 테스트 (API 키 불필요)
```bash
python test_workflow.py
```

### 3. 실제 API 테스트 (API 키 필요, 비용 발생)
```bash
python test_real_api.py
```

## 🛠️ 개발 모드 실행

### QA 에이전트 직접 테스트
```python
from qa_agent.agent import run_agent

# 테스트 쿼리 실행
result = run_agent("의료기기 영업 전략을 알려주세요")
print(result)
```

### 단계별 워크플로우 테스트
```python
from qa_agent.agent import create_graph

# 그래프 생성
app = create_graph()

# 초기 상태 설정
from qa_agent.utils.state import AgentState
from langchain_core.messages import HumanMessage

state = AgentState(
    messages=[HumanMessage(content="테스트 메시지")],
    user_query="테스트 쿼리",
    # ... 기타 필드
)

# 실행
result = app.invoke(state)
```

## 📊 성능 최적화 설정

### 모델 조합 최적화

#### 고품질 + 경제성 (권장)
```env
OPENAI_MODEL_GPT4O=gpt-4o          # 최종 답변 생성
OPENAI_MODEL_GPT4O_MINI=gpt-4o-mini # 의도 분류, 컨텍스트 향상
```

#### 경제적 운영
```env
OPENAI_MODEL_GPT4O=gpt-4o-mini     # 모든 단계에서 mini 사용
OPENAI_MODEL_GPT4O_MINI=gpt-4o-mini
```

#### 최고 품질 (비용 높음)
```env
OPENAI_MODEL_GPT4O=gpt-4o          # 모든 단계에서 4o 사용
OPENAI_MODEL_GPT4O_MINI=gpt-4o
```

## 🚨 문제 해결

### ImportError: No module named 'langchain_core'
```bash
pip install --upgrade langchain langchain-core langgraph
```

### API 키 오류
- `.env` 파일이 올바른 위치에 있는지 확인
- API 키에 공백이나 잘못된 문자가 없는지 확인
- OpenAI 계정에 충분한 크레딧이 있는지 확인

### 느린 응답 속도
- `gpt-4o-mini` 사용 비율 증가
- 타임아웃 설정 조정
- 검색 결과 개수 제한 조정

### 의료업계 컨텍스트 부족
- `qa_agent/utils/tools.py`에서 업계별 데이터 추가
- 검색 알고리즘 튜닝
- 프롬프트 엔지니어링 개선

## 📈 모니터링 및 로깅

### 로그 활성화
```env
LOG_LEVEL=INFO
LOG_FILE=./logs/qa_agent.log
```

### 성능 메트릭 확인
- 응답 시간: 목표 30초 이내
- 신뢰도 점수: 0.7 이상 권장
- API 비용: 쿼리당 약 $0.01-0.05

## 🔒 보안 고려사항

### API 키 보안
- `.env` 파일을 git에 커밋하지 마세요
- 프로덕션에서는 환경 변수 또는 시크릿 관리 도구 사용
- API 키 정기적 교체

### 데이터 보안
- 의료 관련 민감 정보 처리 시 HIPAA 준수
- 사용자 입력 검증 및 필터링
- 로그에 민감 정보 기록 방지

## 🚀 프로덕션 배포

### 환경 분리
```
development/  # 개발 환경
├── .env.development
└── logs/

production/   # 운영 환경  
├── .env.production
└── logs/
```

### 성능 튜닝
- Redis 캐싱 활용
- 동시성 제한 설정
- 비동기 처리 최적화

### 모니터링 설정
- 응답 시간 모니터링
- API 사용량 추적
- 오류율 알림 설정

---

## 🆘 지원

문제가 발생하면 다음을 확인하세요:

1. ✅ 가상환경이 활성화되었는가?
2. ✅ 모든 패키지가 설치되었는가?
3. ✅ `.env` 파일이 올바르게 설정되었는가?
4. ✅ API 키가 유효하고 크레딧이 충분한가?
5. ✅ 인터넷 연결이 안정적인가?

추가 지원이 필요하면 로그 파일과 함께 문의하세요. 