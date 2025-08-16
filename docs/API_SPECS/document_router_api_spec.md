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

### 3. 직원 월간 목표 데이터 업로드
**POST** `/documents/upload/employee-targets`

#### 설명
직원 월간 목표 실적 데이터를 업로드합니다. 사번 컬럼과 YYYYMM 형식의 월별 목표 컬럼을 자동으로 인식하여 employee_performance 테이블에 저장합니다.

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### 요청 본문 (Form Data)
```
file: File (Excel 또는 CSV 파일)
doc_title: string (선택사항, 문서 제목)
uploader_id: integer (업로더 ID)
document_id: integer (선택사항, 관련 문서 ID)
```

#### 지원 파일 형식
- **Excel**: .xlsx, .xls
- **CSV**: .csv

#### 예상 파일 구조
파일은 다음과 같은 구조를 가져야 합니다:
- 사번 컬럼 (필수): "사번", "직원번호", "employee_number", "emp_no" 등
- 직원명 컬럼 (선택): "이름", "성명", "직원명", "담당자" 등
- YYYYMM 형식 컬럼들 (필수, 2개 이상): "202401", "202402", "202403" 등

예시:
| 사번 | 이름 | 202401 | 202402 | 202403 | 202404 |
|------|------|--------|--------|--------|--------|
| E001 | 홍길동 | 5000000 | 5500000 | 6000000 | 6000000 |
| E002 | 김철수 | 4000000 | 4500000 | 4500000 | 5000000 |

#### 응답
```json
{
  "success": true,
  "message": "직원 목표 데이터 처리 완료: 120개 생성, 30개 업데이트",
  "created_count": 120,
  "updated_count": 30,
  "skipped_count": 5,
  "total_processed": 155,
  "error_details": [
    "행 10: 직원을 찾을 수 없음 - 사번: E999",
    "행 15: 직원을 찾을 수 없음 - 사번: E888, 이름: 테스트"
  ]
}
```

#### 응답 필드 설명
- `success`: 처리 성공 여부
- `message`: 처리 결과 요약 메시지
- `created_count`: 새로 생성된 목표 레코드 수
- `updated_count`: 업데이트된 목표 레코드 수
- `skipped_count`: 건너뛴 행 수 (사번 없음, 직원 미존재 등)
- `total_processed`: 전체 처리된 레코드 수
- `error_details`: 처리 중 발생한 오류 상세 (최대 10개)

#### 처리 로직
1. **LLM 기반 컬럼 인식**: GPT-4를 사용하여 사번 및 YYYYMM 형식 컬럼 자동 탐지
2. **직원 확인**: 사번으로 employee_info 테이블에서 직원 ID 조회
3. **Upsert 처리**: 동일 직원-년월 조합이 있으면 업데이트, 없으면 신규 생성
4. **MV 갱신**: 처리 완료 후 employee_performance_mv 자동 갱신

#### 사용 예시
```bash
curl -X POST "http://localhost:8010/documents/upload/employee-targets" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@employee_targets_202401.xlsx" \
  -F "doc_title=2024년 1분기 직원 목표" \
  -F "uploader_id=1"
```

#### Python 클라이언트 예시
```python
import requests

# 파일 업로드
with open('employee_targets.xlsx', 'rb') as f:
    files = {'file': f}
    data = {
        'doc_title': '2024년 직원 목표',
        'uploader_id': 1
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.post(
        'http://localhost:8010/documents/upload/employee-targets',
        files=files,
        data=data,
        headers=headers
    )
    
    result = response.json()
    if result['success']:
        print(f"✅ 성공: {result['message']}")
        print(f"  - 생성: {result['created_count']}건")
        print(f"  - 업데이트: {result['updated_count']}건")
        print(f"  - 건너뜀: {result['skipped_count']}건")
    else:
        print(f"❌ 실패: {result['message']}")
        if result.get('error_details'):
            for error in result['error_details']:
                print(f"  - {error}")
```

#### 에러 응답
**400 Bad Request** - 파일 형식 오류
```json
{
  "detail": "지원하지 않는 파일 형식입니다. Excel(.xlsx, .xls) 또는 CSV(.csv) 파일만 가능합니다."
}
```

**400 Bad Request** - 데이터 형식 오류
```json
{
  "success": false,
  "message": "직원 목표 데이터 형식이 아닙니다. 사번 컬럼과 YYYYMM 형식의 월별 컬럼이 필요합니다.",
  "created_count": 0,
  "updated_count": 0,
  "skipped_count": 0,
  "total_processed": 0
}
```

**500 Internal Server Error**
```json
{
  "detail": "직원 목표 데이터 처리 중 오류가 발생했습니다: [오류 메시지]"
}
```

#### 주의사항
1. **사번 필수**: 모든 행에 유효한 사번이 있어야 처리 가능
2. **직원 사전 등록**: employee_info 테이블에 직원이 먼저 등록되어 있어야 함
3. **YYYYMM 형식**: 월별 컬럼은 반드시 6자리 숫자 형식 (202401, 202402 등)
4. **금액 형식**: 목표 금액은 숫자여야 하며, 콤마(,) 포함 가능
5. **부분 성공**: 일부 행 처리 실패 시에도 나머지는 정상 처리됨

---

### 4. 문서 목록 조회
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

### 5. 문서 다운로드 링크 생성
**GET** `/documents/{doc_id}/download`

#### 헤더
```
Authorization: Bearer <access_token>
```

#### 쿼리 파라미터
- `expiration_hours`: 링크 유효 시간 (시간 단위, 기본값: 1시간, 최대: 24시간)

#### 응답
```json
{
  "doc_id": 1,
  "doc_title": "샘플 문서",
  "file_name": "sample.pdf",
  "download_url": "https://s3-presigned-url...",
  "expires_in_hours": 1,
  "generated_at": "2024-01-01T12:00:00"
}
```

#### 사용 예시
```bash
curl -X GET "http://localhost:8010/documents/1/download?expiration_hours=2" \
  -H "Authorization: Bearer <access_token>"
```

---

### 7. 문서 업로드 with SSE (실시간 진행상황)
**POST** `/documents/upload-sse`

#### 설명
Server-Sent Events를 사용하여 문서 업로드 진행 상황을 실시간으로 전송합니다.
각 처리 단계(파일 검증, 타입 분석, 요약 생성, S3 업로드, DB 저장 등)를 스트리밍합니다.

#### 헤더
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

#### 요청 본문 (Form Data)
```
file: File (업로드할 파일)
uploader_id: integer (업로더 ID)
version: string (선택사항, 문서 버전)
```

#### 응답 (Event Stream)
```
Content-Type: text/event-stream
```

#### 이벤트 형식
각 이벤트는 JSON 형식으로 전송됩니다:

**공통 필드:**
- `type`: "single" (단일 문서)
- `step`: 현재 처리 단계
- `message`: 사용자에게 표시할 메시지

**처리 단계:**
1. `validating` - 파일 검증 중
2. `validated` - 파일 검증 완료
3. `detecting` - 파일 타입 감지 중
4. `detected` - 파일 타입 확인 (docType: "table" | "text")

**테이블 문서 단계:**
5. `classifying` - Text2SQL 분류 진행 중
6. `classified` - 분류 완료 (target_table, confidence 포함)

**텍스트 문서 단계:**
5. `analyzing` - 문서 타입 분석 중
6. `analyzed` - 분석 완료 (doc_subtype 포함)
7. `chunking` - OpenSearch 청킹 중 (regulation/law 문서)
8. `relation_analysis` - 관계 분석 중 (report 문서)

**공통 마지막 단계:**
- `summarizing` - 요약 생성 중
- `uploading` - S3 업로드 중
- `saving` - DB 저장 중
- `completed` - 완료 (result 포함)
- `error` - 오류 발생

#### 이벤트 예시
```json
data: {"type": "single", "step": "validating", "message": "파일 검증 중: sample.pdf"}

data: {"type": "single", "step": "detected", "message": "테이블 문서로 확인됨", "docType": "table"}

data: {"type": "single", "step": "classifying", "message": "Text2SQL 분류 진행 중...", "docType": "table"}

data: {"type": "single", "step": "classified", "message": "타겟 테이블: sales_records (신뢰도: 0.95)", "target_table": "sales_records", "confidence": 0.95}

data: {"type": "single", "step": "completed", "message": "테이블 문서 업로드 완료!", "result": {"doc_id": 1, "doc_title": "매출 데이터", "doc_type": "text2sql_sales_records", "target_table": "sales_records", "confidence": 0.95}}
```

#### JavaScript 클라이언트 예시
```javascript
const eventSource = new EventSource('/documents/upload-sse', {
  headers: {
    'Authorization': 'Bearer ' + accessToken
  }
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`[${data.step}] ${data.message}`);
  
  // UI 업데이트
  updateProgressBar(data.step);
  updateStatusMessage(data.message);
  
  if (data.step === 'completed') {
    console.log('업로드 완료:', data.result);
    eventSource.close();
  } else if (data.step === 'error') {
    console.error('오류 발생:', data.message);
    eventSource.close();
  }
};

eventSource.onerror = (error) => {
  console.error('SSE 연결 오류:', error);
  eventSource.close();
};
```

---

### 8. 배치 문서 업로드 with SSE (실시간 진행상황)
**POST** `/documents/upload-batch-sse`

#### 설명
여러 문서를 한 번에 업로드하면서 각 파일의 처리 상태를 실시간으로 전송합니다.
각 파일별로 처리 단계를 추적할 수 있습니다.

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

#### 응답 (Event Stream)
```
Content-Type: text/event-stream
```

#### 이벤트 형식
**공통 필드:**
- `type`: "batch" (배치 업로드)
- `step`: 현재 처리 단계
- `message`: 사용자에게 표시할 메시지

**배치 관련 필드:**
- `fileIndex`: 현재 처리 중인 파일 인덱스
- `fileName`: 현재 처리 중인 파일명
- `progress`: 전체 진행 상황
  - `current`: 현재 처리 중인 파일 번호
  - `total`: 전체 파일 수
  - `successful`: 성공한 파일 수
  - `failed`: 실패한 파일 수

**처리 단계:**
- `batch_start` - 배치 업로드 시작
- `file_start` - 개별 파일 처리 시작
- `validating` - 파일 검증 중
- `type_detected` - 파일 타입 확인
- (개별 파일 처리 단계는 단일 업로드와 동일)
- `file_completed` - 개별 파일 완료
- `file_error` - 개별 파일 오류
- `batch_completed` - 배치 완료

#### 이벤트 예시
```json
data: {"type": "batch", "step": "batch_start", "message": "총 3개 파일 업로드 시작", "total": 3}

data: {"type": "batch", "step": "file_start", "fileIndex": 1, "fileName": "doc1.pdf", "message": "[1/3] doc1.pdf 처리 시작", "progress": {"current": 1, "total": 3, "successful": 0, "failed": 0}}

data: {"type": "batch", "step": "type_detected", "fileIndex": 1, "fileName": "doc1.pdf", "docType": "text", "message": "[1/3] text 문서로 확인"}

data: {"type": "batch", "step": "file_completed", "fileIndex": 1, "fileName": "doc1.pdf", "message": "[1/3] doc1.pdf 완료", "progress": {"current": 1, "total": 3, "successful": 1, "failed": 0}}

data: {"type": "batch", "step": "batch_completed", "message": "배치 업로드 완료: 성공 2개, 실패 1개", "summary": {"total": 3, "successful": 2, "failed": 1, "results": [...], "errors": [...]}}
```

#### JavaScript 클라이언트 예시
```javascript
class BatchUploadHandler {
  constructor(files, accessToken) {
    this.files = files;
    this.accessToken = accessToken;
    this.fileStatus = new Map();
  }
  
  startUpload() {
    const formData = new FormData();
    this.files.forEach(file => formData.append('files', file));
    formData.append('uploader_id', '1');
    
    const eventSource = new EventSource('/documents/upload-batch-sse', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + this.accessToken
      },
      body: formData
    });
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.step) {
        case 'batch_start':
          this.initializeProgress(data.total);
          break;
          
        case 'file_start':
          this.updateFileStatus(data.fileName, 'processing');
          break;
          
        case 'file_completed':
          this.updateFileStatus(data.fileName, 'completed');
          this.updateOverallProgress(data.progress);
          break;
          
        case 'file_error':
          this.updateFileStatus(data.fileName, 'error', data.error);
          this.updateOverallProgress(data.progress);
          break;
          
        case 'batch_completed':
          this.showSummary(data.summary);
          eventSource.close();
          break;
      }
    };
  }
  
  updateFileStatus(fileName, status, error = null) {
    // UI에서 개별 파일 상태 업데이트
    const fileElement = document.getElementById(`file-${fileName}`);
    fileElement.className = `file-status ${status}`;
    if (error) {
      fileElement.setAttribute('title', error);
    }
  }
  
  updateOverallProgress(progress) {
    // 전체 진행률 바 업데이트
    const percent = (progress.current / progress.total) * 100;
    document.querySelector('.progress-bar').style.width = `${percent}%`;
    document.querySelector('.progress-text').textContent = 
      `${progress.successful}/${progress.total} 완료 (실패: ${progress.failed})`;
  }
}
```

---

### 9. 문서 삭제 (관리자만)
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