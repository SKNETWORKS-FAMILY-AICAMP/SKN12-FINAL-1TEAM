# 문서 타입 업데이트 로직 문서

## 📋 개요

이 문서는 문서 업로드 시스템에서 테이블 데이터가 업로드될 때 문서 타입을 업데이트하는 로직에 대한 상세한 분석과 구현 계획을 담고 있습니다.

## 🔍 현재 상황 분석

### 1. 현재 코드 흐름

#### 1.1 문서 업로드 프로세스 (`document_router.py`)

```python
@router.post("/documents/upload")
async def upload_document(file: UploadFile, doc_title: str, uploader_id: int, version: str = None):
    # 1. 파일 업로드 및 저장
    # 2. 파일 타입 분류 (문서 vs 테이블)
    # 3. 테이블 데이터인 경우 Text2SQL 분류기로 처리
    # 4. 결과 반환
```

#### 1.2 Text2SQL 분류 프로세스 (`text2sql_classifier.py`)

```python
async def classify_table_with_text2sql(self, table_data, table_description, document_id, uploader_id):
    # 1. 벡터 유사도 검색으로 후보 테이블 찾기
    # 2. LLM을 통한 정확한 테이블 분류
    # 3. 컬럼 매핑 및 SQL 생성
    # 4. 데이터베이스에 데이터 삽입
    # 5. 결과 반환
```

### 2. 현재 문제점

#### 2.1 누락된 문서 타입 업데이트 로직

**위치**: `app/routers/document_router.py` - `process_single_document` 함수

**문제**: 테이블 데이터가 성공적으로 처리된 후, 해당 문서의 타입을 업데이트하는 로직이 없습니다.

**현재 코드**:
```python
# 3. Text2SQL 분류기로 처리
result = await text2sql_classifier.classify_table_with_text2sql(
    table_data=table_data,
    table_description=doc_title,
    document_id=doc.doc_id,
    uploader_id=uploader_id
)

# ❌ 여기서 문서 타입 업데이트 로직이 누락됨
return result
```

#### 2.2 필요한 업데이트 사항

1. **문서 타입 변경**: `document` → `table_data`
2. **처리 상태 업데이트**: `pending` → `processed`
3. **처리 결과 저장**: 분류된 테이블 정보 저장

## 🎯 필요한 작업

### 1. 문서 타입 업데이트 로직 구현

#### 1.1 `document_router.py` 수정

**위치**: `process_single_document` 함수 내 Text2SQL 분류 후

**구현 내용**:
```python
# Text2SQL 분류 성공 후 문서 타입 업데이트
if result.get('success'):
    try:
        # 문서 타입을 'table_data'로 업데이트
        doc.document_type = 'table_data'
        doc.processing_status = 'processed'
        doc.processed_at = datetime.utcnow()
        
        # 처리 결과 저장 (선택사항)
        if 'target_table' in result:
            doc.metadata = {
                'target_table': result['target_table'],
                'confidence': result.get('confidence', 0.0),
                'column_mapping': result.get('column_mapping', {}),
                'method': result.get('method', 'text2sql')
            }
        
        session.commit()
        logger.info(f"문서 타입 업데이트 완료: {doc.doc_id} -> table_data")
        
    except Exception as e:
        logger.error(f"문서 타입 업데이트 실패: {e}")
        session.rollback()
```

#### 1.2 데이터베이스 스키마 확인

**파일**: `app/models/documents.py`

**필요한 필드들**:
- `document_type`: 문서 타입 (`document`, `table_data`)
- `processing_status`: 처리 상태 (`pending`, `processing`, `processed`, `failed`)
- `processed_at`: 처리 완료 시간
- `metadata`: 처리 결과 메타데이터 (JSONB)

### 2. 에러 처리 및 롤백 로직

#### 2.1 실패 시 처리

```python
# Text2SQL 분류 실패 시
if not result.get('success'):
    try:
        doc.processing_status = 'failed'
        doc.metadata = {
            'error': result.get('error', 'Unknown error'),
            'method': 'text2sql'
        }
        session.commit()
        logger.warning(f"문서 처리 실패: {doc.doc_id}")
        
    except Exception as e:
        logger.error(f"실패 상태 업데이트 실패: {e}")
        session.rollback()
```

#### 2.2 부분 실패 처리

```python
# 일부 테이블만 성공한 경우
if result.get('partial_success'):
    try:
        doc.document_type = 'table_data'
        doc.processing_status = 'partially_processed'
        doc.metadata = {
            'successful_tables': result.get('successful_tables', []),
            'failed_tables': result.get('failed_tables', []),
            'method': 'text2sql'
        }
        session.commit()
        
    except Exception as e:
        logger.error(f"부분 성공 상태 업데이트 실패: {e}")
        session.rollback()
```

### 3. 로깅 및 모니터링

#### 3.1 상세 로깅

```python
# 성공 시 로깅
logger.info(f"문서 타입 업데이트 성공: {doc.doc_id}")
logger.info(f"  - 이전 타입: {previous_type}")
logger.info(f"  - 새 타입: {doc.document_type}")
logger.info(f"  - 대상 테이블: {result.get('target_table')}")
logger.info(f"  - 신뢰도: {result.get('confidence', 0.0)}")

# 실패 시 로깅
logger.error(f"문서 타입 업데이트 실패: {doc.doc_id}")
logger.error(f"  - 오류: {result.get('error')}")
logger.error(f"  - 원인: {result.get('reason')}")
```

#### 3.2 메트릭 수집

```python
# 처리 통계 수집
processing_stats = {
    'total_processed': 1,
    'successful': 1 if result.get('success') else 0,
    'failed': 0 if result.get('success') else 1,
    'processing_time': processing_time,
    'target_table': result.get('target_table')
}
```

## 🛠️ 구현해야 할 것들

### 1. 핵심 구현 사항

#### 1.1 `document_router.py` 수정

**파일**: `app/routers/document_router.py`
**함수**: `process_single_document`

**추가할 코드**:
```python
# Text2SQL 분류 후 문서 타입 업데이트 로직
if result.get('success'):
    await update_document_type_after_success(doc, result, session)
elif result.get('partial_success'):
    await update_document_type_partial_success(doc, result, session)
else:
    await update_document_type_after_failure(doc, result, session)
```

#### 1.2 헬퍼 함수들 생성

**파일**: `app/services/processors/document_type_updater.py` (새로 생성)

```python
class DocumentTypeUpdater:
    @staticmethod
    async def update_after_success(doc, result, session):
        """성공 시 문서 타입 업데이트"""
        pass
    
    @staticmethod
    async def update_after_failure(doc, result, session):
        """실패 시 문서 타입 업데이트"""
        pass
    
    @staticmethod
    async def update_partial_success(doc, result, session):
        """부분 성공 시 문서 타입 업데이트"""
        pass
```

### 2. 데이터베이스 마이그레이션

#### 2.1 새로운 필드 추가

**파일**: `migrations/versions/` (새 마이그레이션 파일)

```sql
-- documents 테이블에 새로운 필드 추가
ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS metadata JSONB;
```

#### 2.2 인덱스 추가

```sql
-- 성능 향상을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_processed_at ON documents(processed_at);
```

### 3. API 엔드포인트 추가

#### 3.1 문서 타입 수동 업데이트 API

**파일**: `app/routers/document_router.py`

```python
@router.put("/documents/{doc_id}/type")
async def update_document_type(
    doc_id: int,
    document_type: str = Body(...),
    user = Depends(get_current_user)
):
    """문서 타입 수동 업데이트"""
    pass
```

#### 3.2 문서 처리 상태 조회 API

```python
@router.get("/documents/{doc_id}/status")
async def get_document_processing_status(
    doc_id: int,
    user = Depends(get_current_user)
):
    """문서 처리 상태 조회"""
    pass
```

### 4. 대시보드 업데이트

#### 4.1 문서 목록 화면

**파일**: `dashboard/main.py`

```python
# 문서 타입별 필터링
document_type_filter = st.selectbox(
    "문서 타입",
    ["전체", "document", "table_data"],
    key="document_type_filter"
)

# 처리 상태별 필터링
processing_status_filter = st.selectbox(
    "처리 상태",
    ["전체", "pending", "processing", "processed", "failed"],
    key="processing_status_filter"
)
```

#### 4.2 문서 상세 정보

```python
# 문서 상세 정보 표시
if selected_document:
    st.subheader("문서 상세 정보")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**문서 타입**: {selected_document.document_type}")
        st.write(f"**처리 상태**: {selected_document.processing_status}")
    
    with col2:
        st.write(f"**업로드 시간**: {selected_document.uploaded_at}")
        st.write(f"**처리 완료 시간**: {selected_document.processed_at}")
    
    # 메타데이터 표시
    if selected_document.metadata:
        st.subheader("처리 결과")
        st.json(selected_document.metadata)
```

## 📊 테스트 계획

### 1. 단위 테스트

#### 1.1 문서 타입 업데이트 테스트

**파일**: `tests/test_document_type_updater.py`

```python
class TestDocumentTypeUpdater:
    async def test_update_after_success(self):
        """성공 시 업데이트 테스트"""
        pass
    
    async def test_update_after_failure(self):
        """실패 시 업데이트 테스트"""
        pass
    
    async def test_update_partial_success(self):
        """부분 성공 시 업데이트 테스트"""
        pass
```

### 2. 통합 테스트

#### 2.1 전체 업로드 플로우 테스트

```python
class TestDocumentUploadFlow:
    async def test_table_data_upload_with_type_update(self):
        """테이블 데이터 업로드 시 타입 업데이트 테스트"""
        pass
    
    async def test_document_upload_without_type_update(self):
        """일반 문서 업로드 시 타입 업데이트 없음 테스트"""
        pass
```

### 3. 성능 테스트

#### 3.1 대용량 데이터 처리 테스트

```python
class TestPerformance:
    async def test_large_table_upload(self):
        """대용량 테이블 업로드 성능 테스트"""
        pass
    
    async def test_concurrent_uploads(self):
        """동시 업로드 성능 테스트"""
        pass
```

## 🚀 구현 우선순위

### 1단계: 핵심 기능 구현
1. ✅ `document_router.py`에 문서 타입 업데이트 로직 추가
2. ✅ 데이터베이스 마이그레이션 생성
3. ✅ 기본 에러 처리 로직 구현

### 2단계: 고급 기능 구현
1. 🔄 헬퍼 함수들 생성 (`DocumentTypeUpdater` 클래스)
2. 🔄 상세 로깅 및 메트릭 수집
3. 🔄 부분 성공 처리 로직

### 3단계: API 및 UI 개선
1. ⏳ 문서 타입 수동 업데이트 API
2. ⏳ 문서 처리 상태 조회 API
3. ⏳ 대시보드 UI 업데이트

### 4단계: 테스트 및 최적화
1. ⏳ 단위 테스트 작성
2. ⏳ 통합 테스트 작성
3. ⏳ 성능 최적화

## 📝 결론

문서 타입 업데이트 로직은 현재 누락되어 있지만, 위의 계획에 따라 구현하면 다음과 같은 이점을 얻을 수 있습니다:

1. **데이터 일관성**: 문서의 실제 타입과 저장된 타입이 일치
2. **처리 추적**: 문서 처리 상태를 명확히 추적 가능
3. **에러 복구**: 실패한 문서의 재처리 가능
4. **사용자 경험**: 처리 상태를 실시간으로 확인 가능
5. **시스템 모니터링**: 처리 통계 및 성능 지표 수집 가능

이 문서를 기반으로 단계별로 구현을 진행하면 안정적이고 확장 가능한 문서 타입 업데이트 시스템을 구축할 수 있습니다. 