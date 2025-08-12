# Document Router API 명세서

## 개요
문서 업로드, 관리, 검색 기능을 제공하는 API입니다. 다양한 파일 형식을 지원하며 텍스트 추출 및 분석 기능을 포함합니다.

## 기본 정보
- **Base URL**: `/documents`
- **Content-Type**: `multipart/form-data` (업로드), `application/json`
- **인증**: JWT 토큰 기반

## 지원 파일 형식

### 텍스트 문서
- **PDF** (.pdf)
- **DOCX** (.docx)
- **TXT** (.txt)

### 데이터 파일
- **CSV** (.csv)
- **Excel** (.xlsx, .xls)

## API 엔드포인트

### 1. 문서 업로드
**POST** `/documents/upload`

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### 요청 본문 (Form Data)
```
file: File (업로드할 파일)
doc_title: string (문서 제목)
uploader_id: integer (업로더 ID)
version: string (선택사항, 문서 버전)
```

#### 응답 (텍스트 문서)
```json
{
  "doc_id": 1,
  "doc_title": "샘플 문서",
  "doc_type": "pdf",
  "uploader_id": 1,
  "file_path": "documents/sample.pdf",
  "version": "1.0",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 응답 (데이터 파일 - Text2SQL 분류)
```json
{
  "doc_title": "매출 데이터",
  "doc_type": "text2sql_sales_records",
  "uploader_id": 1,
  "version": "1.0",
  "created_at": "2024-01-01T12:00:00Z",
  "message": "Text2SQL 분류 완료: sales_records 테이블로 분류됨 (문서 ID: 1)",
  "analysis": {
    "target_table": "sales_records",
    "confidence": 0.95,
    "reasoning": "매출 관련 컬럼들이 포함되어 있어 sales_records 테이블로 분류",
    "column_mapping": {
      "매출": "sales_amount",
      "날짜": "sale_date"
    },
    "doc_id": 1
  }
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/documents/upload" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@sample.pdf" \
  -F "doc_title=샘플 문서" \
  -F "uploader_id=1" \
  -F "version=1.0"
```

---

### 2. 배치 문서 업로드
**POST** `/documents/upload/batch`

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### 요청 본문 (Form Data)
```
files: File[] (업로드할 파일들)
uploader_id: integer (업로더 ID)
version: string (선택사항, 문서 버전)
```

#### 응답
```json
{
  "total_files": 3,
  "successful_uploads": 2,
  "failed_uploads": 1,
  "results": [
    {
      "doc_id": 1,
      "doc_title": "문서1",
      "doc_type": "pdf",
      "uploader_id": 1,
      "file_path": "documents/doc1.pdf",
      "version": "1.0",
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "doc_title": "매출 데이터",
      "doc_type": "text2sql_sales_records",
      "uploader_id": 1,
      "version": "1.0",
      "created_at": "2024-01-01T12:00:00Z",
      "message": "Text2SQL 분류 완료: sales_records 테이블로 분류됨",
      "analysis": {
        "target_table": "sales_records",
        "confidence": 0.95,
        "doc_id": 2
      }
    }
  ],
  "errors": [
    {
      "filename": "invalid.txt",
      "error": "지원하지 않는 파일 형식입니다: .txt"
    }
  ]
}
```

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/documents/upload/batch" \
  -H "Authorization: Bearer <access_token>" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -F "files=@data.csv" \
  -F "uploader_id=1" \
  -F "version=1.0"
```

---

### 3. 문서 목록 조회
**GET** `/documents/`

#### 헤더
```
Authorization: Bearer <access_token>
```

#### 응답
```json
[
  {
    "doc_id": 1,
    "doc_title": "샘플 문서",
    "doc_type": "pdf",
    "uploader_id": 1,
    "file_path": "documents/sample.pdf",
    "version": "1.0",
    "created_at": "2024-01-01T12:00:00Z"
  },
  {
    "doc_id": 2,
    "doc_title": "매출 데이터",
    "doc_type": "text2sql_sales_records",
    "uploader_id": 1,
    "file_path": "documents/data.csv",
    "version": "1.0",
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/documents/" \
  -H "Authorization: Bearer <access_token>"
```

---

### 4. 특정 문서 조회
**GET** `/documents/{doc_id}`

#### 헤더
```
Authorization: Bearer <access_token>
```

#### 응답
```json
{
  "doc_id": 1,
  "doc_title": "샘플 문서",
  "doc_type": "pdf",
  "uploader_id": 1,
  "file_path": "documents/sample.pdf",
  "version": "1.0",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/documents/1" \
  -H "Authorization: Bearer <access_token>"
```

---

### 5. 문서 삭제 (관리자만)
**DELETE** `/documents/{doc_id}`

#### 헤더
```
Authorization: Bearer <admin_token>
```

#### 응답
```json
{
  "doc_id": 1,
  "doc_title": "샘플 문서",
  "doc_type": "pdf",
  "uploader_id": 1,
  "file_path": "documents/sample.pdf",
  "version": "1.0",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 사용 예시
```bash
curl -X DELETE "http://localhost:8010/documents/1" \
  -H "Authorization: Bearer <admin_token>"
```

---

## 파일 처리 기능

### 텍스트 추출
- **PDF**: PyPDF2를 사용한 텍스트 추출
- **DOCX**: python-docx를 사용한 텍스트 추출
- **TXT**: UTF-8 인코딩으로 텍스트 읽기

### 데이터 처리
- **CSV**: pandas를 사용한 데이터 읽기
- **Excel**: pandas를 사용한 데이터 읽기

### 문서 분석
- 텍스트 청킹 (OpenSearch 인덱싱용)
- 엔티티 추출
- 문서 요약 생성
- 관계 분석

### Text2SQL 분류
- **테이블 파일 자동 분류**: CSV, Excel 파일을 자동으로 적절한 데이터베이스 테이블로 분류
- **신뢰도 점수**: 분류 정확도를 0.0-1.0 범위로 제공
- **컬럼 매핑**: 원본 컬럼명과 데이터베이스 컬럼명 매핑 정보 제공
- **분류 근거**: 분류 결정에 대한 설명 제공

---

## 에러 응답

### 400 Bad Request
```json
{
  "detail": "지원하지 않는 파일 형식입니다."
}
```

```json
{
  "detail": "파일 크기가 너무 큽니다. 최대 10MB까지 업로드 가능합니다."
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin privileges required"
}
```

### 404 Not Found
```json
{
  "detail": "Document not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "파일 업로드 중 오류가 발생했습니다."
}
```

---

## 파일 크기 제한

### 권장 사항
- **PDF**: 50MB 이하
- **DOCX**: 20MB 이하
- **TXT**: 10MB 이하
- **CSV**: 100MB 이하
- **Excel**: 50MB 이하

### 시스템 제한
- **최대 파일 크기**: 10MB (모든 파일 형식)

---

## 문서 분석 기능

### 텍스트 문서 분석
- 텍스트 길이 계산
- 청크 분할 (검색용)
- 엔티티 추출
- 요약 생성

### 데이터 파일 분석
- 행/열 수 계산
- 데이터 미리보기
- 스키마 분석
- Text2SQL 자동 분류

---

## 주의사항

1. **파일 형식**: 지원되는 형식만 업로드 가능
2. **파일 크기**: 권장 크기 제한 준수
3. **권한**: 문서 삭제는 관리자만 가능
4. **백업**: 중요한 문서는 별도 백업 권장
5. **보안**: 민감한 정보가 포함된 문서 주의
6. **Text2SQL 분류**: 테이블 파일은 자동으로 적절한 데이터베이스 테이블로 분류됨 