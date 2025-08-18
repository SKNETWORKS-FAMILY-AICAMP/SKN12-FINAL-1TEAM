# Search Router API 명세서

## 개요
검색 API는 Text2SQL과 OpenSearch를 활용한 통합 검색 기능을 제공합니다. 구조화된 데이터베이스 검색과 비정형 문서 검색을 모두 지원합니다.

## 기본 정보
- **Base URL**: `/search`
- **인증**: Bearer Token 필요 (모든 엔드포인트)
- **Content-Type**: `application/json`

## API 엔드포인트

### 1. Text2SQL 검색
자연어 쿼리를 SQL로 변환하여 데이터베이스를 검색합니다.

#### **GET** `/search/text2sql`

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | ✅ | - | 검색 쿼리 (자연어) |
| limit | integer | ❌ | 20 | 결과 개수 제한 (1-100) |

#### Response
```json
{
  "success": true,
  "message": "Text2SQL 검색이 완료되었습니다.",
  "query": "홍길동 직원의 2024년 매출",
  "results": [
    {
      "id": 123,
      "doc_id": 456,
      "table_type": "sales_records",
      "content": {
        "sales_record_id": 123,
        "employee_name": "홍길동",
        "sale_amount": 1000000,
        "sale_date": "2024-01-15",
        "customer_name": "ABC병원",
        "product_name": "의료기기A"
      },
      "created_at": "2024-01-15T10:30:00",
      "similarity_score": 0.95,
      "source": "text2sql"
    }
  ],
  "total_count": 10,
  "search_time": 1.234
}
```

#### 검색 가능한 테이블
- **sales_records**: 매출 기록 (직원, 고객, 제품, 매출액, 날짜)
- **employee_info**: 직원 정보 (이름, 사번, 팀, 직급)
- **customers**: 고객 정보 (고객명, 주소, 담당의사)
- **products**: 제품 정보 (제품명, 설명, 카테고리)

#### 예시 쿼리
- "홍길동 매출"
- "2024년 3월 매출 현황"
- "폭세틴 판매 내역"
- "우리가족의원 거래 내역"

---

### 2. OpenSearch 파이프라인 검색
OpenSearch를 사용한 하이브리드 검색 (키워드 + 벡터 검색)을 수행합니다.

#### **GET** `/search/opensearch`

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | ✅ | - | 검색 쿼리 |
| limit | integer | ❌ | 20 | 결과 개수 제한 (1-100) |
| pipeline_id | string | ❌ | hybrid-minmax-pipeline | 사용할 파이프라인 ID |

#### Response
```json
{
  "success": true,
  "message": "OpenSearch 파이프라인 검색이 완료되었습니다.",
  "query": "거래처 접대 규정",
  "results": [
    {
      "id": "document_123",
      "doc_id": "10df8a93-c59e-4968-80a6-8d65d145042e",
      "doc_title": "내부 규정집",
      "content": "제3장 거래처 관리\n제15조 (접대 규정) 거래처 접대 시 다음 사항을 준수한다...",
      "created_at": "2024-01-10T09:00:00",
      "similarity_score": 0.89,
      "metadata": {
        "chapter_num": "3",
        "chapter_title": "거래처 관리",
        "article_num": "15",
        "article_title": "접대 규정"
      },
      "source": "opensearch"
    }
  ],
  "total_count": 5,
  "search_time": 0.567
}
```

#### 검색 특징
- **하이브리드 검색**: BM25 (30%) + 벡터 검색 (70%) 가중치 조합
- **자동 키워드 추출**: OpenAI를 사용한 지능형 키워드 추출
- **리랭킹**: BGE Reranker를 사용한 결과 재순위화
- **문서 타입**: 규정 문서(regulation), 보고서(report) 지원

---

### 3. 통합 검색
Text2SQL과 OpenSearch를 동시에 검색하여 통합 결과를 반환합니다.

#### **GET** `/search/all`

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | ✅ | - | 검색 쿼리 |
| limit | integer | ❌ | 20 | 각 검색 방식별 결과 개수 제한 (1-100) |

#### Response
```json
{
  "text2sql": {
    "success": true,
    "message": "Text2SQL 검색이 완료되었습니다.",
    "query": "2024년 매출",
    "results": [...],
    "total_count": 15,
    "search_time": 1.234
  },
  "opensearch": {
    "success": true,
    "message": "OpenSearch 파이프라인 검색이 완료되었습니다.",
    "query": "2024년 매출",
    "results": [...],
    "total_count": 8,
    "search_time": 0.567
  }
}
```

#### 특징
- 두 검색 엔진을 병렬로 실행
- 각 검색이 실패해도 다른 검색 결과는 반환
- 통합 검색으로 구조화/비구조화 데이터 모두 검색 가능

---

### 4. 검색 시스템 상태 조회
검색 시스템의 상태와 사용 가능한 인덱스를 확인합니다.

#### **GET** `/search/stats`

#### Response
```json
{
  "success": true,
  "message": "검색 시스템 통계 조회 완료",
  "stats": {
    "text2sql": {
      "available": true,
      "message": "Text2SQL 검색 서비스가 정상 작동 중입니다."
    },
    "opensearch": {
      "available": true,
      "message": "OpenSearch가 정상 작동 중입니다.",
      "indices": [
        "document_chunks",
        "qa_logs",
        "user_activities"
      ]
    }
  }
}
```

---

## 데이터 모델

### Text2SQLSearchResult
```typescript
{
  id: number;                  // 레코드 ID
  doc_id: number;              // 문서 ID
  table_type: string;          // 테이블 유형
  content: object;             // 실제 데이터
  created_at?: string;         // 생성일시
  similarity_score?: number;   // 유사도 점수
  source: "text2sql";         // 검색 소스
}
```

### OpenSearchResult
```typescript
{
  id: string;                          // 문서 ID (문자열)
  doc_id?: number | string;            // 문서 ID (UUID 또는 정수)
  doc_title?: string;                  // 문서 제목
  content: string;                     // 문서 내용
  created_at?: string;                 // 생성일시
  similarity_score: number;            // 유사도 점수
  metadata?: object;                   // 추가 메타데이터
  source: "opensearch";               // 검색 소스
}
```

### SearchResponse
```typescript
{
  success: boolean;           // 성공 여부
  message: string;           // 응답 메시지
  query: string;             // 원본 쿼리
  results: Array<any>;       // 검색 결과 배열
  total_count: number;       // 전체 결과 수
  search_time: number;       // 검색 소요 시간(초)
}
```

---

## 에러 처리

### HTTP Status Codes
| Code | Description |
|------|-------------|
| 200 | 성공 |
| 400 | 잘못된 요청 (파라미터 오류) |
| 401 | 인증 실패 |
| 500 | 서버 내부 오류 |
| 503 | 서비스 사용 불가 (OpenSearch 연결 실패) |

### Error Response
```json
{
  "detail": "검색 중 오류가 발생했습니다: [에러 메시지]"
}
```

---

## 사용 예시

### cURL 예시

#### Text2SQL 검색
```bash
curl -X GET "http://localhost:8000/search/text2sql?query=홍길동%20매출&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### OpenSearch 검색
```bash
curl -X GET "http://localhost:8000/search/opensearch?query=거래처%20규정&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 통합 검색
```bash
curl -X GET "http://localhost:8000/search/all?query=2024년%20실적" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 시스템 상태 확인
```bash
curl -X GET "http://localhost:8000/search/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Python 예시

```python
import requests

# 설정
base_url = "http://localhost:8000"
token = "YOUR_ACCESS_TOKEN"
headers = {"Authorization": f"Bearer {token}"}

# Text2SQL 검색
response = requests.get(
    f"{base_url}/search/text2sql",
    params={"query": "홍길동 2024년 매출", "limit": 20},
    headers=headers
)
text2sql_results = response.json()

# OpenSearch 검색
response = requests.get(
    f"{base_url}/search/opensearch",
    params={"query": "거래처 접대 규정"},
    headers=headers
)
opensearch_results = response.json()

# 통합 검색
response = requests.get(
    f"{base_url}/search/all",
    params={"query": "2024년 판매 실적"},
    headers=headers
)
combined_results = response.json()
```

---

## 주의사항

1. **인증 필수**: 모든 엔드포인트는 유효한 Bearer Token이 필요합니다.

2. **검색 쿼리 최적화**:
   - Text2SQL: 구체적인 테이블 필드명이나 날짜를 포함하면 더 정확한 결과
   - OpenSearch: 핵심 키워드를 포함하되 너무 긴 문장은 피하기

3. **성능 고려사항**:
   - `limit` 파라미터로 결과 수를 제한하여 응답 시간 단축
   - 통합 검색은 두 엔진을 모두 사용하므로 개별 검색보다 시간이 더 소요됨

4. **인덱스 관리**:
   - OpenSearch 검색은 `document_chunks` 인덱스를 사용
   - 인덱스가 없거나 문서가 없으면 빈 결과 반환

5. **에러 처리**:
   - 503 에러 발생 시 OpenSearch 서비스 상태 확인 필요
   - 통합 검색에서 한 엔진이 실패해도 다른 결과는 반환됨

---

## 버전 정보
- **현재 버전**: 1.0.0
- **최종 업데이트**: 2024-12-18
- **작성자**: System Administrator