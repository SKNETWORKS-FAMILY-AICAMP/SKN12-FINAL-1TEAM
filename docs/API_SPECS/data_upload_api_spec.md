# Data Upload API 명세서

## 개요
뉴스, 법률, 보험 인정기준, 뉴스 전략 레포트 데이터를 업로드하는 API입니다.

## 기본 정보
- **Base URL**: `/data`
- **인증**: JWT 토큰 기반 (Bearer Token)
- **Content-Type**: `multipart/form-data`

## API 엔드포인트

### 1. 뉴스 Excel 업로드
**POST** `/data/upload/news`

#### 설명
뉴스 데이터가 포함된 Excel 파일을 업로드하여 news 테이블에 저장합니다.

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### 요청 본문
```
file: Excel 파일 (.xlsx, .xls)
```

#### 필수 컬럼
| 컬럼명 | 설명 | 데이터 타입 | 예시 |
|--------|------|------------|------|
| 제목 | 뉴스 제목 | String | "신약 개발 성공" |
| url | 뉴스 URL | String | "https://news.example.com/1" |
| 언론사 | 뉴스 출처 | String | "의학신문" |
| 업로드_날짜 | 게시 날짜 | Date | "2024-01-15" |
| 타입 | 뉴스 타입 | String | "common news" 또는 "medical news" |
| 요약 | 뉴스 요약 | String | "새로운 항암제가..." |

#### 응답
```json
{
  "success_count": 10,
  "duplicate_count": 2,
  "error_count": 1,
  "errors": [
    "행 5: 잘못된 뉴스 타입 'unknown'"
  ]
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/data/upload/news" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@news_data.xlsx"
```

---

### 2. 법률 Excel 업로드
**POST** `/data/upload/laws`

#### 설명
법률 데이터가 포함된 Excel 파일을 업로드하여 laws 테이블에 저장합니다.

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### 요청 본문
```
file: Excel 파일 (.xlsx, .xls)
```

#### 필수 컬럼
| 컬럼명 | 설명 | 데이터 타입 | 예시 |
|--------|------|------------|------|
| 법명 | 법률 제목 | String | "약사법" |
| 법률정보 | 법률 번호 | String | "제2024-001호" |
| 조문 | 조문 정보 | String | "제31조" |
| 내용 | 법률 내용 | String | "의약품 제조업 허가..." |
| 소스_URL | 출처 URL | String | "https://law.go.kr/..." |

#### 응답
```json
{
  "success_count": 15,
  "duplicate_count": 3,
  "error_count": 0,
  "errors": []
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/data/upload/laws" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@laws_data.xlsx"
```

---

### 3. 보험 인정기준 Excel 업로드
**POST** `/data/upload/insurance-criteria`

#### 설명
보험 인정기준 데이터가 포함된 Excel 파일을 업로드하여 insurance_recognition_criteria 테이블에 저장합니다.

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### 요청 본문
```
file: Excel 파일 (.xlsx, .xls)
```

#### 필수 컬럼
| 컬럼명 | 설명 | 데이터 타입 | 예시 |
|--------|------|------------|------|
| 고시 | 고시 번호 | String | "제2024-001호" |
| 제목 | 인정기준 제목 | String | "항암제 급여기준" |
| 업로드_날짜 | 업로드 날짜 | Date | "2024-01-15" |
| url | 관련 URL | String | "https://hira.or.kr/..." |
| 수집날짜 | 수집 날짜 | Date | "2024-01-16" |

#### 응답
```json
{
  "success_count": 8,
  "duplicate_count": 1,
  "error_count": 0,
  "errors": []
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/data/upload/insurance-criteria" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@insurance_criteria.xlsx"
```

---

### 4. 뉴스 전략 레포트 업로드
**POST** `/data/upload/news-strategy-report`

#### 설명
뉴스 전략 레포트 MD 파일을 업로드하고 관련 뉴스와 연결합니다.
- 파일명에서 자동으로 제목이 추출됩니다 (.md 제거, `_`와 `-`는 공백으로 변환)
- MD 파일은 MinIO에 저장되며, DB에는 파일 경로만 저장됩니다

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### 요청 본문
| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| file | File | O | Markdown 파일 (.md) |
| news_titles | String (JSON) | O | 관련 뉴스 제목 리스트 |

#### news_titles 형식
```json
["뉴스 제목 1", "뉴스 제목 2", "뉴스 제목 3"]
```

#### 응답
```json
{
  "report_id": 1,
  "title": "2024년 1월 제약 시장 동향 보고서",
  "file_path": "strategy-reports/2024-01/abc-def-ghi.md",
  "connected_news_count": 5,
  "not_found_news": [
    "찾을 수 없는 뉴스 제목"
  ],
  "created_at": "2024-01-20T10:30:00Z"
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/data/upload/news-strategy-report" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@2024_january_market_report.md" \
  -F 'news_titles=["신약 개발 성공", "FDA 승인 소식", "제약사 실적 발표"]'
```

> 참고: 파일명 `2024_january_market_report.md`는 자동으로 "2024 january market report"로 변환되어 제목으로 저장됩니다.

#### Python 클라이언트 예시
```python
import requests
import json

# 파일과 데이터 준비
# 파일명: 2024_january_pharma_report.md
with open('2024_january_pharma_report.md', 'rb') as f:
    files = {'file': f}
    data = {
        'news_titles': json.dumps([
            "신약 개발 성공",
            "FDA 승인 소식",
            "제약사 실적 발표"
        ])
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.post(
        'http://localhost:8010/data/upload/news-strategy-report',
        files=files,
        data=data,
        headers=headers
    )
    
    result = response.json()
    print(f"보고서 ID: {result['report_id']}")
    print(f"보고서 제목: {result['title']}")  # "2024 january pharma report"
    print(f"저장 경로: {result['file_path']}")  # "strategy-reports/2024-01/uuid.md"
    print(f"연결된 뉴스: {result['connected_news_count']}개")
    if result['not_found_news']:
        print(f"찾지 못한 뉴스: {result['not_found_news']}")
```

---

### 5. 업로드 템플릿 조회
**GET** `/data/upload/template/{data_type}`

#### 설명
각 데이터 타입별 Excel 템플릿 정보를 제공합니다.

#### 파라미터
- `data_type`: `news`, `laws`, `insurance-criteria` 중 하나

#### 응답
```json
{
  "columns": ["제목", "url", "언론사", "업로드_날짜", "타입", "요약"],
  "sample": {
    "제목": "신약 개발 소식",
    "url": "https://example.com/news/1",
    "언론사": "의학신문",
    "업로드_날짜": "2024-01-15",
    "타입": "medical news",
    "요약": "새로운 항암제 개발 성공..."
  }
}
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/data/upload/template/news" \
  -H "Authorization: Bearer <access_token>"
```

---

## 에러 응답

### 400 Bad Request
```json
{
  "detail": "Excel 파일(.xlsx, .xls)만 업로드 가능합니다."
}
```

```json
{
  "detail": "필수 컬럼 누락: 제목, url"
}
```

```json
{
  "detail": "news_titles가 올바른 JSON 형식이 아닙니다."
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
  "detail": "파일 처리 중 오류가 발생했습니다: [오류 메시지]"
}
```

---

## 파일 크기 제한
- **최대 파일 크기**: 50MB (모든 파일 형식)

---

## 주의사항

### Excel 파일 형식
1. **인코딩**: UTF-8 권장
2. **헤더 행**: 첫 번째 행은 반드시 컬럼명이어야 함
3. **날짜 형식**: YYYY-MM-DD 또는 Excel 날짜 형식
4. **공백 처리**: 컬럼명의 앞뒤 공백은 자동 제거됨

### 중복 데이터 처리
1. **뉴스**: URL 기준으로 중복 체크
2. **법률**: 법률번호(법률정보) 기준으로 중복 체크
3. **보험 인정기준**: 고시번호 기준으로 중복 체크
4. 중복 데이터는 건너뛰고 duplicate_count에 포함

### 뉴스 타입 변환
- "common news", "common", "일반" → general
- "medical news", "medical", "제약", "pharmaceutical" → pharmaceutical

### 뉴스 전략 레포트
1. **파일명에서 제목 자동 추출**: `.md` 확장자 제거, `_`와 `-`는 공백으로 변환
2. **MinIO 저장**: MD 파일은 MinIO에 저장되며, DB의 content 필드에는 파일 경로만 저장
3. **파일 경로 구조**: `strategy-reports/년-월/UUID.md` 형식으로 저장
4. **뉴스 연결**: 제목으로 부분 일치(LIKE) 검색하여 관련 뉴스와 연결
5. **찾지 못한 뉴스**: not_found_news에 반환되지만 에러는 아님
6. **트랜잭션 처리**: 보고서 생성과 뉴스 연결이 모두 성공해야 커밋

---

## 성능 고려사항
1. **배치 처리**: Excel 데이터는 배치로 처리되어 성능 최적화
2. **트랜잭션**: 각 파일 업로드는 하나의 트랜잭션으로 처리
3. **에러 제한**: 에러 메시지는 최대 10개까지만 반환
4. **비동기 처리**: 모든 DB 작업은 비동기로 처리

---

## 사용 시나리오

### 1. 정기적인 뉴스 데이터 업데이트
```python
# 매일 수집된 뉴스를 Excel로 정리하여 업로드
import pandas as pd
import requests

# 뉴스 데이터 준비
news_df = pd.DataFrame({
    '제목': ['뉴스1', '뉴스2'],
    'url': ['http://...', 'http://...'],
    '언론사': ['A신문', 'B신문'],
    '업로드_날짜': ['2024-01-20', '2024-01-20'],
    '타입': ['common news', 'medical news'],
    '요약': ['내용1', '내용2']
})

# Excel 파일로 저장
news_df.to_excel('daily_news.xlsx', index=False)

# 업로드
with open('daily_news.xlsx', 'rb') as f:
    response = requests.post(
        'http://localhost:8010/data/upload/news',
        files={'file': f},
        headers={'Authorization': f'Bearer {token}'}
    )
```

### 2. 월간 전략 보고서 생성 및 업로드
```python
# 보고서 작성 후 관련 뉴스와 연결
report_content = """
# 2024년 1월 제약 시장 동향

## 주요 이슈
- 신약 개발 활발
- 규제 변화 예상

## 시장 전망
...
"""

# MD 파일 저장 (파일명이 제목이 됨)
filename = '2024_01_pharma_market_trend.md'
with open(filename, 'w', encoding='utf-8') as f:
    f.write(report_content)

# 관련 뉴스 제목 리스트
related_news = [
    "A사 신약 FDA 승인",
    "B사 임상 3상 성공",
    "제약 규제 완화 발표"
]

# 업로드
with open(filename, 'rb') as f:
    response = requests.post(
        'http://localhost:8010/data/upload/news-strategy-report',
        files={'file': f},
        data={
            'news_titles': json.dumps(related_news)
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
# 결과 확인
result = response.json()
print(f"보고서 제목: {result['title']}")  # "2024 01 pharma market trend"
print(f"MinIO 저장 경로: {result['file_path']}")  # "strategy-reports/2024-01/uuid.md"
```