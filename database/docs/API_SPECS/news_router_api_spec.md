# News API 명세서

## 개요
뉴스 데이터를 조회하는 API입니다. 일반 뉴스, 제약 뉴스 조회 및 관련 전략 레포트 조회 기능을 제공합니다.

## 기본 정보
- **Base URL**: `/news`
- **인증**: JWT 토큰 기반 (Bearer Token)
- **Content-Type**: `application/json`

## API 엔드포인트

### 1. 특정 날짜의 일반 뉴스 조회
**GET** `/news/general/{target_date}`

#### 설명
지정된 날짜의 일반 뉴스 목록을 조회합니다.

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| target_date | date | Y | 조회할 날짜 (YYYY-MM-DD 형식) |

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 응답
```json
[
  {
    "news_id": 1,
    "title": "의료 시스템 개선 방안 발표",
    "content": "정부는 오늘...",
    "news_type": "general",
    "source": "의학신문",
    "author": "김기자",
    "published_date": "2024-01-15",
    "url": "https://news.example.com/123",
    "tags": {
      "keywords": ["의료", "정책"]
    },
    "created_at": "2024-01-15T10:30:00"
  }
]
```

#### 응답 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| news_id | integer | 뉴스 고유 ID |
| title | string | 뉴스 제목 |
| content | string | 뉴스 내용 |
| news_type | string | 뉴스 타입 (general/pharmaceutical) |
| source | string | 뉴스 출처 |
| author | string | 기사 작성자 |
| published_date | date | 게시 날짜 |
| url | string | 원문 URL |
| tags | object | 태그 정보 (JSON) |
| created_at | datetime | 생성 일시 |

#### 에러 응답
- **500**: 뉴스 조회 중 오류 발생

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/news/general/2024-01-15" \
  -H "Authorization: Bearer <access_token>"
```

---

### 2. 특정 날짜의 제약 뉴스 조회
**GET** `/news/pharmaceutical/{target_date}`

#### 설명
지정된 날짜의 제약 관련 뉴스 목록을 조회합니다.

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| target_date | date | Y | 조회할 날짜 (YYYY-MM-DD 형식) |

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 응답
```json
[
  {
    "news_id": 2,
    "title": "신약 FDA 승인 획득",
    "content": "국내 제약사가 개발한...",
    "news_type": "pharmaceutical",
    "source": "약업신문",
    "author": "박기자",
    "published_date": "2024-01-15",
    "url": "https://pharma.example.com/456",
    "tags": {
      "keywords": ["FDA", "신약", "승인"]
    },
    "created_at": "2024-01-15T14:20:00"
  }
]
```

#### 에러 응답
- **500**: 뉴스 조회 중 오류 발생

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/news/pharmaceutical/2024-01-15" \
  -H "Authorization: Bearer <access_token>"
```

---

### 3. 특정 뉴스와 관련된 전략 레포트 조회
**GET** `/news/{news_id}/strategy-reports`

#### 설명
특정 뉴스와 연관된 전략 레포트 목록을 조회합니다.

#### 경로 파라미터
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| news_id | integer | Y | 뉴스 ID |

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 응답
```json
[
  {
    "report_id": 1,
    "title": "신약 개발 동향 분석 레포트",
    "content": "minio://reports/2024/01/report_123.pdf",
    "created_by": 101,
    "created_at": "2024-01-16T09:00:00",
    "reference_type": "main_source",
    "reference_notes": "주요 참고 자료로 활용"
  }
]
```

#### 응답 필드
| 필드 | 타입 | 설명 |
|------|------|------|
| report_id | integer | 레포트 고유 ID |
| title | string | 레포트 제목 |
| content | string | MinIO 파일 경로 |
| created_by | integer | 작성자 ID |
| created_at | datetime | 생성 일시 |
| reference_type | string | 참조 유형 (main_source/supporting/related) |
| reference_notes | string | 참조 관련 메모 |

#### 에러 응답
- **404**: 뉴스 ID를 찾을 수 없음
- **500**: 전략 레포트 조회 중 오류 발생

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/news/123/strategy-reports" \
  -H "Authorization: Bearer <access_token>"
```

---

### 4. 뉴스 검색
**GET** `/news/search`

#### 설명
다양한 조건으로 뉴스를 검색합니다. 모든 파라미터는 선택사항입니다.

#### 쿼리 파라미터
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|--------|
| keyword | string | N | 제목 또는 내용에서 검색할 키워드 | - |
| news_type | string | N | 뉴스 타입 (general/pharmaceutical) | - |
| start_date | date | N | 검색 시작 날짜 (YYYY-MM-DD) | - |
| end_date | date | N | 검색 종료 날짜 (YYYY-MM-DD) | - |
| limit | integer | N | 최대 결과 수 | 100 |

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 응답
```json
[
  {
    "news_id": 3,
    "title": "코로나19 백신 개발 현황",
    "content": "글로벌 제약사들의...",
    "news_type": "pharmaceutical",
    "source": "헬스조선",
    "author": "이기자",
    "published_date": "2024-01-10",
    "url": "https://health.example.com/789",
    "tags": {
      "keywords": ["백신", "코로나19", "제약"]
    },
    "created_at": "2024-01-10T11:45:00"
  }
]
```

#### 검색 예시

##### 키워드로 검색
```bash
curl -X GET "http://localhost:8010/news/search?keyword=FDA" \
  -H "Authorization: Bearer <access_token>"
```

##### 날짜 범위로 검색
```bash
curl -X GET "http://localhost:8010/news/search?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer <access_token>"
```

##### 제약 뉴스만 검색
```bash
curl -X GET "http://localhost:8010/news/search?news_type=pharmaceutical&limit=20" \
  -H "Authorization: Bearer <access_token>"
```

##### 복합 조건 검색
```bash
curl -X GET "http://localhost:8010/news/search?keyword=신약&news_type=pharmaceutical&start_date=2024-01-01&end_date=2024-12-31&limit=50" \
  -H "Authorization: Bearer <access_token>"
```

#### 에러 응답
- **500**: 뉴스 검색 중 오류 발생

---

## 데이터 모델

### NewsType 열거형
```python
class NewsType(enum.Enum):
    GENERAL = "general"  # 일반 뉴스
    PHARMACEUTICAL = "pharmaceutical"  # 제약 뉴스
```

### News 테이블
- **news_id**: 뉴스 고유 ID (Primary Key)
- **title**: 뉴스 제목
- **content**: 뉴스 내용
- **news_type**: 뉴스 타입
- **source**: 뉴스 출처
- **author**: 기사 작성자
- **published_date**: 게시 날짜
- **url**: 원문 URL (Unique)
- **tags**: 태그 정보 (JSONB)
- **created_at**: 생성 일시
- **updated_at**: 수정 일시

### NewsStrategyReport 테이블
- **report_id**: 보고서 고유 ID (Primary Key)
- **title**: 보고서 제목
- **content**: MinIO 파일 경로
- **created_by**: 작성자 ID (Foreign Key → employees)
- **created_at**: 생성 일시

### NewsStrategyReportReference 테이블
- **id**: 참조 고유 ID (Primary Key)
- **report_id**: 보고서 ID (Foreign Key → news_strategy_reports)
- **news_id**: 뉴스 ID (Foreign Key → news)
- **reference_type**: 참조 유형
- **notes**: 참조 관련 메모
- **created_at**: 생성 일시

---

## 주의사항

1. **인증**: 모든 엔드포인트는 JWT 토큰 인증이 필요합니다.
2. **날짜 형식**: 날짜는 반드시 `YYYY-MM-DD` 형식으로 입력해야 합니다.
3. **뉴스 타입**: `general` 또는 `pharmaceutical` 값만 허용됩니다.
4. **검색 제한**: 검색 결과는 기본적으로 100개로 제한되며, limit 파라미터로 조정 가능합니다.
5. **빈 결과**: 조회 결과가 없을 경우 빈 배열(`[]`)을 반환합니다.

---

## 에러 코드

| HTTP 상태 코드 | 설명 |
|---------------|------|
| 200 | 성공 |
| 401 | 인증 실패 (토큰 없음 또는 만료) |
| 404 | 리소스를 찾을 수 없음 |
| 422 | 잘못된 파라미터 형식 |
| 500 | 서버 내부 오류 |