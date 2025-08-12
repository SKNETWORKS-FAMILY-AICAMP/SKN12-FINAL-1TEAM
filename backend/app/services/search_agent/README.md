# Search Agent - 완전한 LLM 기반 아키텍처

문서 검색 에이전트는 QA API와 Hybrid Search API를 통합하여 사용자의 자연어 질문에 대한 답변을 제공하는 LangGraph 기반 에이전트입니다. **하드 코딩된 키워드 로직을 완전히 제거**하고 **LLM의 지능적 판단**에 의존하는 완전한 AI 기반 시스템입니다.

## 주요 기능

### 1. QA API 통합
- 자연어 질문에 대한 답변 생성
- 문서 기반 질문-답변
- 출처 정보 제공

### 2. Hybrid Search API 통합
- 구조화된 데이터 검색
- 테이블과 문서 통합 검색
- 검색 결과 요약

### 3. 완전한 LLM 기반 툴 선택
- 하드 코딩된 키워드 로직 완전 제거
- LLM이 문맥을 이해하여 적절한 툴 자동 선택
- 새로운 질문 패턴도 자동 학습 가능
- 동의어와 복잡한 문장 구조 이해

### 4. LangGraph 기반 에이전트
- React 에이전트 패턴 사용
- 상태 관리 및 워크플로우 제어
- 확장 가능한 아키텍처

## 설치 및 설정

### 1. 의존성 설치
```bash
pip install langchain langgraph langchain-openai requests
```

### 2. 환경 변수 설정
```bash
export OPENAI_API_KEY="your-openai-api-key"
export API_TOKEN="your-jwt-token"  # Hybrid Search API 인증용
```

### 3. API 서버 확인
- QA API: `http://localhost:8010/qa`
- Hybrid Search API: `http://localhost:8010/search`

## 사용법

### 기본 사용법

```python
from search_agent import create_search_agent

# JWT 토큰과 함께 에이전트 생성
api_token = "your-jwt-token"  # Hybrid Search API 인증용
agent = create_search_agent(api_token=api_token)

# 시스템 상태 확인
health = agent.check_api_health()
print(health)

# 에이전트 앱 생성
app = agent.create_agent()

# 사용 예시
# app.invoke({"messages": [{"role": "user", "content": "회사 매출 현황을 알려주세요"}]})
```

### 직접 API 호출

```python
# QA API 직접 호출 (JWT 토큰 불필요)
answer = agent.call_qa_api("회사의 매출 현황은 어떻게 되나요?")
print(answer)

# Hybrid Search API 직접 호출 (JWT 토큰 필요)
search_result = agent.call_hybrid_search_api("매출 데이터")
print(search_result)
```

## API 명세

### QA API
- **엔드포인트**: `POST /qa/question`
- **기능**: 자연어 질문에 대한 답변 생성
- **파라미터**:
  - `question`: 질문 (1-1000자)
  - `top_k`: 검색할 문서 수 (1-20, 기본값: 5)
  - `include_summary`: 요약 포함 여부
  - `include_sources`: 원본 문서 정보 포함 여부

### Hybrid Search API
- **엔드포인트**: `POST /search/hybrid`
- **기능**: 테이블과 텍스트 문서 통합 검색
- **파라미터**:
  - `query`: 검색 쿼리
  - `limit`: 결과 개수 제한 (기본값: 20)

## LLM 기반 아키텍처의 장점

### 1. 하드 코딩 vs LLM 기반 비교

| 방식 | 하드 코딩 | LLM 기반 |
|------|-----------|----------|
| **확장성** | ❌ 제한적 | ✅ 무제한 |
| **정확도** | ❌ 낮음 | ✅ 높음 |
| **유지보수** | ❌ 어려움 | ✅ 쉬움 |
| **컨텍스트 이해** | ❌ 불가 | ✅ 가능 |
| **동의어 처리** | ❌ 불가 | ✅ 가능 |

### 2. 시나리오별 LLM 판단 예시

**시나리오 1: "근무 시간 관련 규정 알려줘"**
- LLM 분석: "규정" → 문서 기반 → TextDocQA 선택

**시나리오 2: "최수아 사원의 급여 내역 보여줘"**
- LLM 분석: "사원", "급여", "최수아" → 구조화된 데이터 → HybridDocSearch 선택

**시나리오 3: "2024년 상반기 거래처별 매출과 분석 자료"**
- LLM 분석: "거래처별", "매출", "분석" → 복합 데이터 → HybridDocSearch 선택

**시나리오 6: "거래 정보 좀 알려줘"**
- LLM 분석: 너무 애매함 → 툴 선택 안함 → Clarification 요청

## 툴 설명
- **용도**: 문서 기반 질문-답변
- **적합한 질문**: 
  - 규정/정책 관련: "근무시간 규정", "회사 정책", "복리후생"
  - 공지사항/보고서: "리모트워크 공지", "분기별 보고서"
  - 매뉴얼/가이드: "업무 매뉴얼", "시스템 사용법"
  - 일반 질문 형태: "어떻게", "무엇", "왜", "언제", "어디서"
- **반환**: 상세한 답변과 출처 정보

### HybridDocSearch
- **용도**: 구조화된 데이터 검색
- **적합한 검색**:
  - 사원 정보: "최수아 사원 급여", "김영수 부서", "직원 목록"
  - 거래처 정보: "삼성메디텍 거래내역", "거래처별 매출", "최고 매출 거래처"
  - 매출/실적 데이터: "2024년 매출", "분기별 실적", "월별 거래량"
  - 구체적인 수치/기간 포함: "최근 3개월", "상위 5개", "2024년 상반기"
- **반환**: 검색 결과 요약

## 에러 처리

### 네트워크 오류
- API 서버 연결 실패 시 적절한 오류 메시지 반환
- 타임아웃 설정 (30초)

### API 오류
- HTTP 상태 코드별 오류 처리
- JSON 파싱 오류 처리

### 시스템 오류
- 로깅을 통한 디버깅 지원
- 사용자 친화적 오류 메시지

## 테스트

### 테스트 실행

#### 기본 테스트 (JWT 토큰 없이)
```bash
cd backend/app/services/search_agent
python test_agent.py
```

#### JWT 토큰과 함께 테스트
```bash
# 방법 1: 명령행 인수로 JWT 토큰 제공
python test_agent.py "your-jwt-token"

# 방법 2: 환경 변수로 JWT 토큰 설정
export API_TOKEN="your-jwt-token"
python test_agent.py
```

#### JWT 토큰 예시 스크립트
```bash
# JWT 토큰과 함께 전체 기능 테스트
python example_with_token.py "your-jwt-token"

# JWT 토큰 없이 QA API만 테스트
python example_with_token.py
```

### 테스트 항목
1. 에이전트 생성 테스트
2. QA API 테스트
3. Hybrid Search API 테스트
4. 통합 에이전트 테스트

## 성능 최적화

### 검색 파라미터 조정
- `top_k`: 높을수록 정확도 향상, 속도 저하
- `limit`: 필요한 만큼만 설정
- `include_summary`: 처리 시간 단축

### 권장 설정
```python
# QA API
{
    "top_k": 5,
    "include_summary": True,
    "include_sources": True
}

# Hybrid Search API
{
    "limit": 20
}
```

## 모니터링

### 시스템 상태 확인
```python
health = agent.check_api_health()
print(json.dumps(health, indent=2, ensure_ascii=False))
```

### 로그 확인
```bash
# 에이전트 로그 확인
tail -f logs/search_agent.log
```

## 주의사항

1. **API 서버 상태**: 사용 전 시스템 상태 확인
2. **JWT 토큰**: Hybrid Search API 사용 시 유효한 JWT 토큰 필요
3. **인증**: QA API는 토큰 불필요, Hybrid Search API는 토큰 필수
4. **네트워크**: 안정적인 네트워크 연결 필요
5. **리소스**: 메모리 및 CPU 사용량 모니터링
6. **보안**: API 키와 JWT 토큰 보안 유지

## 확장 가능성

### 새로운 툴 추가
```python
def new_tool_function(query: str) -> str:
    # 새로운 툴 로직
    pass

tools.append(Tool(
    name="NewTool",
    func=new_tool_function,
    description="새로운 툴 설명"
))
```

### 커스텀 에이전트
```python
class CustomSearchAgent(SearchAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 커스텀 초기화
    
    def custom_method(self):
        # 커스텀 메서드
        pass
```

## 문제 해결

### 일반적인 문제

1. **API 연결 실패**
   - 서버 상태 확인
   - 네트워크 연결 확인
   - URL 및 포트 확인

2. **인증 오류**
   - JWT 토큰 유효성 확인
   - 토큰 만료 확인
   - 권한 확인

3. **메모리 부족**
   - `top_k` 및 `limit` 값 조정
   - 동시 요청 수 제한
   - 리소스 모니터링

### 디버깅

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 상세 로그 확인
logger = logging.getLogger(__name__)
logger.debug("디버그 정보")
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 