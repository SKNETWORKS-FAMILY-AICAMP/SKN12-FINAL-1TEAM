# Search Agent 마이그레이션 가이드

## 개요
Search Agent를 기존 QA/Hybrid Search API에서 새로운 Search Router API로 마이그레이션했습니다.
이 문서는 주요 변경 사항과 새로운 기능을 설명합니다.

## 주요 변경 사항

### 1. API 엔드포인트 변경

#### 기존 API
- `POST /qa/question` - QA API
- `POST /search/hybrid` - Hybrid Search API
- `GET /qa/health` - 헬스체크

#### 새로운 API
- `GET /search/text2sql` - 구조화된 데이터 검색
- `GET /search/opensearch` - 문서 검색
- `GET /search/all` - 통합 검색
- `GET /search/stats` - 시스템 통계

### 2. HTTP 메서드 변경
- **기존**: POST 요청 + JSON body
- **새로운**: GET 요청 + Query parameters

### 3. 자연어 응답 생성 기능 추가

#### 새로운 메서드들
```python
# Text2SQL 결과를 자연어로 변환
_generate_natural_response_text2sql(query, results, total_count)

# OpenSearch 결과를 자연어로 변환
_generate_natural_response_opensearch(query, results, total_count)

# 통합 검색 결과를 자연어로 변환
_generate_natural_response_all(query, text2sql_result, opensearch_result)
```

#### 자연어 변환 예시

**입력 (구조화된 데이터)**:
```json
{
  "employee_name": "최수아",
  "department": "영업팀",
  "position": "과장",
  "hire_date": "2020-03-15"
}
```

**출력 (자연어)**:
```
최수아님은 영업팀 소속 과장으로, 2020년 3월 15일에 입사하셨습니다.
```

### 4. Tool 이름 및 설명 업데이트

#### 기존 Tools
- `TextDocQA` - 문서 기반 질문-답변
- `HybridDocSearch` - 구조화된 데이터 검색

#### 새로운 Tools
- `Text2SQLSearch` - 구조화된 데이터베이스 검색 (인사, 매출, 고객 정보)
- `OpenSearchDoc` - 문서 검색 (계약서, 보고서, 공지사항)
- `IntegratedSearch` - 통합 검색 (모든 소스에서 종합 정보)

### 5. 파일별 주요 수정 내용

#### `search_agent.py`
1. **메서드 이름 변경**:
   - `call_qa_api()` → `call_text2sql_api()`
   - `call_hybrid_search_api()` → `call_opensearch_api()`
   - 새로 추가: `call_all_search_api()`

2. **자연어 응답 생성 메서드 추가**:
   - `_generate_natural_response_text2sql()`
   - `_generate_natural_response_opensearch()`
   - `_generate_natural_response_all()`

3. **API 호출 방식 변경**:
   - POST 요청에서 GET 요청으로
   - JSON payload에서 query parameters로

4. **헬스체크 업데이트**:
   - `/qa/health` → `/search/stats`
   - 새로운 응답 포맷 처리

#### `run.py`
1. **설명 업데이트**:
   - 자연어 응답 생성 기능 명시
   - search_type에 "(자연어 응답)" 추가

#### `example_with_token.py`
1. **테스트 시나리오 업데이트**:
   - 새로운 API에 맞는 테스트 쿼리
   - Text2SQL, OpenSearch, 통합 검색 테스트 추가

2. **API 호출 예시 변경**:
   - 새로운 메서드명 사용
   - 응답 출력 길이 증가 (200 → 300자)

## 테스트 시나리오

### 시나리오 1: 인사 정보 조회
- **질문**: "최수아의 인사 정보를 알려줘"
- **사용 API**: Text2SQL
- **예상 응답**: "최수아님은 영업팀 소속 과장으로..."

### 시나리오 2: 매출 통계
- **질문**: "지난달 매출이 가장 높은 고객 3곳을 알려줘"
- **사용 API**: Text2SQL
- **예상 응답**: "지난달 매출 상위 3개 고객사는..."

### 시나리오 3: 문서 검색
- **질문**: "신약 개발 관련 계약서를 찾아줘"
- **사용 API**: OpenSearch
- **예상 응답**: "신약 개발 관련 계약서 3건을 찾았습니다..."

### 시나리오 4: 통합 검색
- **질문**: "삼성병원에 대한 모든 정보를 알려줘"
- **사용 API**: 통합 검색 (Text2SQL + OpenSearch)
- **예상 응답**: 거래 정보 + 관련 문서 종합

### 시나리오 5: 실적 분석
- **질문**: "김철수 직원의 이번 분기 실적은?"
- **사용 API**: Text2SQL
- **예상 응답**: "김철수님의 2024년 1분기 실적은..."

## 사용 방법

### 1. JWT 토큰과 함께 실행
```bash
python example_with_token.py "your-jwt-token"
```

### 2. 환경 변수로 토큰 설정
```bash
export API_TOKEN="your-jwt-token"
python example_with_token.py
```

### 3. 코드에서 직접 사용
```python
from search_agent import create_search_agent

# 에이전트 생성
agent = create_search_agent(api_token="your-jwt-token")

# 자연어 응답 받기
response = agent.call_text2sql_api("최수아의 인사 정보를 알려줘")
print(response)  # 자연어로 변환된 응답 출력
```

## 주의 사항

1. **JWT 토큰 필수**: 모든 Search API는 JWT 토큰 인증이 필요합니다
2. **GET 요청 사용**: 새로운 API는 모두 GET 메서드를 사용합니다
3. **자연어 응답**: 모든 검색 결과는 자동으로 자연어로 변환됩니다
4. **LLM 의존성**: 자연어 변환을 위해 OpenAI API가 필요합니다

## 장점

1. **사용자 친화적**: 구조화된 데이터를 자연스러운 문장으로 제공
2. **통합 검색**: 여러 소스의 정보를 한 번에 검색 가능
3. **확장성**: 새로운 검색 유형 추가 용이
4. **유연한 응답**: LLM을 통한 컨텍스트 기반 응답 생성

## 이전 버전과의 호환성

이전 버전의 코드를 사용 중이라면:
1. API 엔드포인트를 새로운 것으로 변경
2. POST → GET 메서드 변경
3. 메서드명 업데이트 (call_qa_api → call_text2sql_api 등)
4. 응답 포맷이 자연어로 변경되었음을 고려

## 문제 해결

### API 연결 실패
- JWT 토큰 유효성 확인
- API 서버 상태 확인 (`/search/stats`)
- 네트워크 연결 확인

### 자연어 변환 오류
- OpenAI API 키 확인
- LLM 응답 실패 시 기본 포맷팅으로 폴백

### 검색 결과 없음
- 쿼리 내용 확인
- 적절한 검색 유형 선택 (Text2SQL vs OpenSearch)