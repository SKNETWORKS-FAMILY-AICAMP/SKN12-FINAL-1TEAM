# Search Router API 명세서

## 개요
검색 API는 두 가지 검색 방식을 제공하여 구조화된 데이터와 비구조화된 문서를 모두 검색할 수 있습니다.

- **Text2SQL**: 자연어 쿼리를 SQL로 변환하여 데이터베이스 테이블 검색
- **OpenSearch**: 벡터 임베딩과 키워드를 활용한 문서 전문 검색

## 기본 정보
- **Base URL**: `/search`
- **인증**: JWT 토큰 기반 (Bearer Token)
- **Content-Type**: `application/json`

## 데이터 모델

### Text2SQLSearchResult
```json
{
  "id": 1,
  "doc_id": 100,
  "table_type": "customers",
  "content": {
    "customer_name": "삼성병원",
    "monthly_sales": 5000000
  },
  "created_at": "2024-01-15T10:00:00",
  "similarity_score": 0.95,
  "source": "text2sql"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| id | integer | 레코드 ID |
| doc_id | integer | 문서 ID |
| table_type | string | 테이블 유형 |
| content | object | 검색된 데이터 내용 |
| created_at | string | 생성 일시 |
| similarity_score | float | 유사도 점수 |
| source | string | 검색 출처 (항상 "text2sql") |

### OpenSearchResult
```json
{
  "id": "doc-123",
  "doc_id": 123,
  "doc_title": "계약서_2024",
  "content": "계약 내용...",
  "created_at": "2024-01-15T10:00:00",
  "similarity_score": 0.89,
  "metadata": {
    "doc_type": "contract"
  },
  "source": "opensearch"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| id | string | 문서 ID |
| doc_id | integer | 문서 번호 |
| doc_title | string | 문서 제목 |
| content | string | 문서 내용 |
| created_at | string | 생성 일시 |
| similarity_score | float | 유사도 점수 |
| metadata | object | 추가 메타데이터 |
| source | string | 검색 출처 (항상 "opensearch") |

### SearchResponse
```json
{
  "success": true,
  "message": "검색이 완료되었습니다.",
  "query": "삼성병원 매출",
  "results": [...],
  "total_count": 10,
  "search_time": 0.245
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| success | boolean | 성공 여부 |
| message | string | 응답 메시지 |
| query | string | 원본 검색 쿼리 |
| results | array | 검색 결과 배열 |
| total_count | integer | 전체 결과 수 |
| search_time | float | 검색 소요 시간(초) |

## API 엔드포인트

### 1. Text2SQL 검색
**GET** `/search/text2sql`

#### 설명
자연어 쿼리를 SQL로 변환하여 데이터베이스 테이블에서 정형 데이터를 검색합니다.

#### 요청 파라미터
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|--------|
| query | string | Y | 검색 쿼리 | - |
| limit | integer | N | 결과 개수 제한 (1-100) | 20 |

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 응답
```json
{
  "success": true,
  "message": "Text2SQL 검색이 완료되었습니다.",
  "query": "지난달 매출이 가장 높은 고객",
  "results": [
    {
      "id": 1,
      "doc_id": 100,
      "table_type": "customer_monthly_performance",
      "content": {
        "customer_name": "삼성병원",
        "monthly_sales": 15000000,
        "year_month": "2024-01"
      },
      "created_at": "2024-01-31T23:59:59",
      "similarity_score": 0.98,
      "source": "text2sql"
    }
  ],
  "total_count": 1,
  "search_time": 0.123
}
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/search/text2sql?query=지난달%20매출이%20가장%20높은%20고객&limit=10" \
  -H "Authorization: Bearer <access_token>"
```

#### 활용 시나리오
- 매출 통계 조회: "이번달 전체 매출"
- 고객 정보 검색: "A등급 고객 목록"
- 직원 실적 조회: "김직원의 분기 실적"
- 제품 분석: "가장 많이 판매된 제품"

---

### 2. OpenSearch 검색
**GET** `/search/opensearch`

#### 설명
OpenSearch 파이프라인을 사용하여 문서를 벡터 검색과 키워드 검색으로 조회합니다.

#### 요청 파라미터
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|--------|
| query | string | Y | 검색 쿼리 | - |
| limit | integer | N | 결과 개수 제한 (1-100) | 20 |
| pipeline_id | string | N | 사용할 파이프라인 ID | hybrid-minmax-pipeline |

#### 파이프라인 옵션
- `hybrid-minmax-pipeline`: 벡터와 키워드 검색 조합 (기본값)
- `keyword-only`: 키워드 검색만 사용
- `vector-only`: 벡터 유사도 검색만 사용

#### 응답
```json
{
  "success": true,
  "message": "OpenSearch 파이프라인 검색이 완료되었습니다.",
  "query": "신약 개발 계약서",
  "results": [
    {
      "id": "doc-456",
      "doc_id": 456,
      "doc_title": "신약개발_계약서_2024",
      "content": "본 계약은 신약 개발에 관한...",
      "created_at": "2024-01-10T14:30:00",
      "similarity_score": 0.92,
      "metadata": {
        "doc_type": "contract",
        "department": "R&D"
      },
      "source": "opensearch"
    }
  ],
  "total_count": 5,
  "search_time": 0.087
}
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/search/opensearch?query=신약%20개발%20계약서&limit=10&pipeline_id=hybrid-minmax-pipeline" \
  -H "Authorization: Bearer <access_token>"
```

#### 활용 시나리오
- 문서 내용 검색: "FDA 승인 관련 문서"
- 계약서 조회: "2024년 공급 계약"
- 보고서 검색: "분기별 실적 보고서"
- 메모 검색: "회의록 중 예산 관련"

---

### 3. 통합 검색
**GET** `/search/all`

#### 설명
Text2SQL과 OpenSearch를 동시에 사용하여 모든 데이터 소스에서 검색합니다.

#### 요청 파라미터
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|--------|
| query | string | Y | 검색 쿼리 | - |
| limit | integer | N | 각 검색별 결과 개수 제한 (1-100) | 20 |

#### 응답
```json
{
  "text2sql": {
    "success": true,
    "message": "Text2SQL 검색이 완료되었습니다.",
    "query": "삼성병원",
    "results": [...],
    "total_count": 3,
    "search_time": 0.145
  },
  "opensearch": {
    "success": true,
    "message": "OpenSearch 파이프라인 검색이 완료되었습니다.",
    "query": "삼성병원",
    "results": [...],
    "total_count": 7,
    "search_time": 0.098
  }
}
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/search/all?query=삼성병원&limit=10" \
  -H "Authorization: Bearer <access_token>"
```

#### 장점
- **포괄적 검색**: 구조화된 데이터와 문서 모두 검색
- **실패 격리**: 한 검색이 실패해도 다른 검색 결과는 제공
- **다양한 관점**: 동일 쿼리에 대한 다각도 결과

#### 활용 시나리오
- 고객 종합 정보: 매출 데이터 + 관련 문서
- 프로젝트 현황: 진행 상태 + 관련 보고서
- 직원 정보: 인사 데이터 + 평가 문서

---

### 4. 검색 시스템 통계
**GET** `/search/stats`

#### 설명
검색 시스템의 상태와 통계 정보를 조회합니다.

#### 응답
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
        "documents",
        "news",
        "contracts"
      ]
    }
  }
}
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/search/stats" \
  -H "Authorization: Bearer <access_token>"
```

## 검색 방식 비교

| 구분 | Text2SQL | OpenSearch |
|------|----------|------------|
| **검색 대상** | 구조화된 테이블 데이터 | 비구조화된 문서 |
| **검색 방식** | 자연어 → SQL 변환 | 벡터 + 키워드 하이브리드 |
| **강점** | 정확한 수치 데이터 조회 | 의미 기반 유사도 검색 |
| **속도** | 빠름 (인덱스 활용) | 보통 (벡터 연산) |
| **적합한 쿼리** | "매출 통계", "고객 목록" | "관련 문서", "유사 내용" |
| **결과 정확도** | 100% 일치 | 유사도 점수 기반 |

## 에러 응답

### 400 Bad Request
```json
{
  "detail": "검색 쿼리는 필수입니다."
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 500 Internal Server Error
```json
{
  "detail": "검색 중 오류가 발생했습니다: <error_message>"
}
```

### 503 Service Unavailable
```json
{
  "detail": "OpenSearch 서비스를 사용할 수 없습니다."
}
```

## 사용 시나리오

### 시나리오 1: 매출 분석
```bash
# Text2SQL로 정확한 매출 데이터 조회
GET /search/text2sql?query=2024년 1월 매출 상위 10개 고객
```

### 시나리오 2: 문서 검색
```bash
# OpenSearch로 관련 문서 검색
GET /search/opensearch?query=FDA 승인 절차
```

### 시나리오 3: 종합 정보 조회
```bash
# 통합 검색으로 고객의 모든 정보 조회
GET /search/all?query=삼성병원
# 결과: 매출 데이터 + 계약서 + 미팅 노트 등
```

## 성능 고려사항

### 결과 개수 제한
- 기본값: 20개
- 최대값: 100개
- 대량 데이터는 페이지네이션 고려

### 검색 시간
- Text2SQL: 일반적으로 100ms 이내
- OpenSearch: 문서 양에 따라 50-500ms
- 통합 검색: 두 검색의 합 (병렬 처리)

### 최적화 팁
1. **구체적인 쿼리 사용**: "매출" 보다 "2024년 1월 A등급 고객 매출"
2. **적절한 검색 방식 선택**: 수치 데이터는 Text2SQL, 문서는 OpenSearch
3. **결과 개수 제한**: 필요한 만큼만 요청
4. **캐싱 활용**: 자주 사용되는 쿼리는 프론트엔드에서 캐싱

## 주의사항

1. **인증 필수**: 모든 엔드포인트는 JWT 토큰 인증 필요
2. **쿼리 길이**: 최대 500자 권장
3. **특수문자 인코딩**: URL 쿼리 파라미터는 URL 인코딩 필요
4. **서비스 가용성**: `/search/stats`로 서비스 상태 확인 후 사용
5. **에러 처리**: 통합 검색에서 부분 실패 가능성 고려
6. **검색 언어**: 한국어 쿼리 최적화됨