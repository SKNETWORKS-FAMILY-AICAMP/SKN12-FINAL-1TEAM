# Text2SQL 테이블 문서 업로드 기능 상세 문서

## 📌 개요

`text2sql_classifier.py`는 Excel 또는 CSV 형태의 테이블 데이터를 자동으로 분석하여 적절한 데이터베이스 테이블로 분류하고 저장하는 AI 기반 시스템입니다. LLM(Large Language Model)과 벡터 유사도 검색을 활용하여 업로드된 문서의 컬럼과 데이터를 분석하고, 자동으로 올바른 데이터베이스 테이블에 매핑합니다.

## 🏗️ 시스템 아키텍처

### 핵심 컴포넌트

1. **Text2SQLTableClassifier** (메인 클래스)
   - 전체 분류 및 저장 프로세스 관리
   - LLM 기반 테이블 분류 수행
   - 데이터 검증 및 필터링
   - 다중 테이블 처리 지원

2. **TableProcessor** (테이블별 처리기)
   - 각 테이블별 특화된 데이터 처리 로직
   - 데이터 변환 및 정규화
   - 중복 확인 및 업데이트 처리

3. **PromptTemplates** (프롬프트 관리)
   - LLM 프롬프트 템플릿 관리
   - 테이블별 특수 규칙 정의
   - 컬럼 매핑 가이드라인 제공

4. **VectorSimilarityService** (유사도 검색)
   - 업로드된 컬럼과 DB 스키마 간 유사도 분석
   - 다중 테이블 매핑 가능성 탐색
   - 관련 테이블 추천

## 📊 업로드 프로세스 흐름

### 1. 데이터 수신 및 초기 분석
```python
async def classify_table_with_text2sql(
    self, 
    table_data: List[Dict[str, Any]], 
    table_description: str = "", 
    document_id: Optional[int] = None, 
    uploader_id: Optional[int] = None
) -> Dict[str, Any]
```

**처리 단계:**
- 테이블 데이터 유효성 검증
- 컬럼 구조 추출 (모든 컬럼명을 문자열로 변환)
- 샘플 데이터 추출 (최대 30행)

### 2. LLM 분류 수행
```python
async def _perform_llm_classification(
    self, 
    columns: List[str], 
    sample_data: List[Dict], 
    table_description: str
) -> Dict[str, Any]
```

**처리 과정:**

#### 2.1 다중 테이블 분석
- 벡터 유사도 서비스를 통해 관련 테이블 탐색
- 각 테이블과의 스키마 유사도 계산
- 가능한 모든 테이블 매핑 조합 도출

#### 2.2 LLM 프롬프트 생성
프롬프트는 다음 정보를 포함:
- 업로드된 컬럼 목록
- 샘플 데이터 (첫 30행)
- 문서 설명 (제공된 경우)
- 관련 테이블 스키마 정보
- 테이블별 매핑 규칙

#### 2.3 OpenAI GPT-4 API 호출
```python
result = openai_service.create_json_completion(
    messages=messages,
    model="gpt-4o-mini",
    max_tokens=1500,
    temperature=0.1
)
```

#### 2.4 LLM 응답 처리
LLM은 다음 형식의 JSON 응답 반환:
```json
{
    "target_tables": [
        {
            "table_name": "employee_info",
            "confidence": 0.95,
            "reasoning": "직원 정보 관련 컬럼 발견",
            "column_mapping": {
                "name": "담당자",
                "employee_number": "사번",
                "position": "직급"
            }
        }
    ]
}
```

### 3. 결과 검증 및 필터링
```python
async def _validate_and_filter_target_tables(
    self, 
    uploaded_columns: List[str], 
    target_tables: List[Dict[str, Any]], 
    sample_data: List[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]
```

**검증 항목:**
- 매핑된 소스 컬럼의 실재 여부 확인
- 테이블별 필수 필드 검증
- 특수 패턴 인식 (월별 데이터, 매출 패턴 등)
- 테이블 간 의존성 검증

**특수 처리 케이스:**

#### employee_performance 테이블
- 월별 목표 패턴 컬럼 자동 인식 (`*_목표`)
- 패턴 매칭 시 빈 매핑으로 자동 처리

#### sales_records 테이블
- products 테이블과의 연관성 검증
- 월별 매출 패턴 자동 인식 (YYYYMM 형식)
- product_id 필수 연결 확인

#### customer_monthly_status 테이블
- 고객별 월간 데이터 패턴 인식
- 환자수/예산 컬럼 자동 매핑

### 4. 테이블 의존성 분석
```python
def _analyze_table_dependencies(
    self, 
    target_tables: List[Dict[str, Any]]
) -> List[Dict[str, Any]]
```

**의존성 레벨 (저장 순서):**
1. Level 0: 독립 테이블 (branches, employee_info, customers, products)
2. Level 1: 1차 의존 테이블 (sales_records, interaction_logs)
3. Level 2: 2차 의존 테이블 (employee_performance, customer_monthly_status)

### 5. 데이터 저장 실행
```python
async def _insert_data_to_target_table(
    self, 
    table_data: List[Dict[str, Any]], 
    target_table: str, 
    column_mapping: Dict[str, str], 
    document_id: Optional[int] = None, 
    uploader_id: Optional[int] = None
) -> Dict[str, Any]
```

**처리 단계:**

#### 5.1 테이블별 프로세서 호출
```python
processor = get_table_processor(table_name, session)
result = await processor.process_batch(
    table_data, 
    column_mapping, 
    document_id, 
    uploader_id
)
```

#### 5.2 배치 처리 실행
각 프로세서는 다음 작업 수행:
- 데이터 변환 및 정규화
- 중복 확인 (unique 필드 기준)
- 신규 생성 또는 기존 레코드 업데이트
- 외래키 자동 연결

#### 5.3 처리 결과 집계
```python
{
    'success': True,
    'processed_count': 100,  # 처리된 전체 행 수
    'created_count': 80,      # 신규 생성된 레코드 수
    'updated_count': 15,      # 업데이트된 레코드 수
    'skipped_count': 5        # 건너뛴 레코드 수
}
```

### 6. MV(Materialized View) 자동 갱신
데이터 저장 성공 시 백그라운드로 MV 갱신:
```python
if created_count > 0 or updated_count > 0:
    asyncio.create_task(refresh_mv_background())
```

### 7. 통합 결과 로깅
```python
def _log_consolidated_summary(
    self, 
    all_results: List[Dict[str, Any]], 
    document_id: Optional[int] = None
)
```

**로그 출력 예시:**
```
📊 문서 처리 완료 (문서 ID: 123): 
employee_info(30명 생성) | customers(50건 생성, 10건 업데이트) | 
sales_records(200건 생성) | 총 290건 처리됨
```

## 🔧 주요 기능 특징

### 1. 지능형 컬럼 매핑
- **유사 의미 인식**: "담당자" → "name", "사번" → "employee_number"
- **패턴 인식**: YYYYMM 형식 자동 감지
- **다양한 표현 처리**: "거래처명", "고객명", "병원명" 모두 customer_name으로 매핑

### 2. 외래키 자동 처리
- 직접적인 ID 매핑 방지
- 이름/번호 기반 자동 ID 조회 및 연결
- 테이블 간 참조 무결성 보장

### 3. 다중 테이블 동시 처리
- 하나의 문서에서 여러 테이블로 데이터 분산 저장
- 의존성 순서에 따른 순차 처리
- 트랜잭션 관리 및 롤백 지원

### 4. 특수 케이스 처리

#### 월별 데이터 처리
```python
# employee_performance의 월별 목표 패턴
"202401_목표", "202402_목표" → 자동으로 월별 레코드 생성

# sales_records의 월별 매출 패턴  
"202401", "202402" → sale_date로 자동 변환
```

#### 중복 데이터 관리
- Upsert 방식 (Insert or Update)
- 고유 필드 기준 중복 체크
- 기존 데이터 보존 및 선택적 업데이트

### 5. 에러 처리 및 복구
- 각 테이블별 독립적 에러 처리
- 부분 실패 시 성공한 테이블은 유지
- 상세한 에러 로깅 및 추적

## 📋 지원 테이블 및 매핑 규칙

### employee_info (직원 정보)
**필수 필드:**
- name: 직원명, 담당자, 성명
- employee_number: 사번, 직원번호, emp_no

**선택 필드:**
- position: 직급, 직위
- branch_id: 지점명, 소속 (자동 ID 변환)
- contact_number: 연락처, 전화번호

### customers (고객 정보)
**필수 필드:**
- customer_name: 거래처명, 고객명, 병원명, 약국명

**선택 필드:**
- address: 주소, 소재지, 위치
- doctor_name: 의사명, 원장명
- contact_number: 전화번호, 연락처

### products (제품 정보)
**필수 필드:**
- product_name: 품목, 제품명, 상품명

**선택 필드:**
- category: 카테고리, 분류
- description: 설명, 비고

### sales_records (매출 기록)
**필수 조건:**
- 직원 정보 (name 또는 employee_number)
- 고객 정보 (customer_name)
- 매출 데이터 (sale_amount 또는 월별 매출 컬럼)

**자동 처리:**
- 월별 매출 컬럼 → 개별 매출 레코드로 변환
- product_id 자동 연결 (products 테이블 참조)

### employee_performance (직원 성과)
**특수 처리:**
- 월별 목표 패턴 자동 인식 (`*_목표`)
- 연월별 개별 레코드 생성

### customer_monthly_status (고객 월별 상태)
**필수 조건:**
- 고객 정보 (customer_name)
- 월별 데이터 (year_month 또는 YYYYMM 패턴)
- 수치 데이터 (patient_count 또는 used_budget)

## 🔍 디버깅 및 모니터링

### 로그 레벨
- **INFO**: 정상 처리 흐름
- **WARNING**: 검증 실패, 데이터 제외
- **ERROR**: 처리 실패, 예외 발생

### 주요 로그 포인트
1. LLM 프롬프트 및 응답
2. 테이블 분류 결과
3. 검증 통과/실패 사유
4. 각 테이블별 처리 통계
5. 최종 처리 요약

### 성능 모니터링
- 처리 시간 측정
- 배치 크기 최적화 (기본 1000행)
- 메모리 사용량 추적
- DB 연결 풀 관리

## 🚀 최적화 전략

### 1. 배치 처리
- 대량 데이터는 1000행 단위로 분할 처리
- 트랜잭션 크기 최적화
- 메모리 효율적 스트리밍 처리

### 2. 병렬 처리
- 독립적인 테이블은 동시 처리 가능
- 백그라운드 MV 갱신
- 비동기 I/O 활용

### 3. 캐싱
- 외래키 조회 결과 캐싱
- 스키마 정보 캐싱
- LLM 응답 캐싱 (동일 구조)

## 📝 사용 예시

### 기본 사용법
```python
from app.services.core.text2sql_classifier import text2sql_classifier

# Excel 데이터 업로드 및 분류
result = await text2sql_classifier.classify_table_with_text2sql(
    table_data=[
        {"담당자": "홍길동", "사번": "E001", "직급": "과장"},
        {"담당자": "김철수", "사번": "E002", "직급": "대리"}
    ],
    table_description="직원 정보 목록",
    document_id=123,
    uploader_id=1
)

# 결과 확인
if result['success']:
    print(f"분류 완료: {result['target_table']}")
    print(f"처리된 레코드: {result['processed_count']}건")
    print(f"신규 생성: {result['created_count']}건")
```

### 다중 테이블 처리 예시
```python
# 직원, 고객, 매출 정보가 혼재된 데이터
mixed_data = [
    {
        "담당자": "홍길동", 
        "사번": "E001",
        "거래처명": "A병원",
        "202401": 1000000,
        "202402": 1500000
    }
]

result = await text2sql_classifier.classify_table_with_text2sql(
    table_data=mixed_data,
    table_description="월별 매출 실적"
)

# 다중 테이블 결과
if result['success'] and 'target_tables' in result:
    for table_result in result['target_tables']:
        print(f"{table_result['table_name']}: {table_result['processed_count']}건")
```

## ⚠️ 주의사항

### 1. 데이터 형식
- Excel/CSV 데이터는 딕셔너리 리스트 형태로 변환 필요
- 컬럼명은 문자열로 통일
- 빈 값은 None 또는 빈 문자열로 처리

### 2. 외래키 처리
- ID 필드 직접 매핑 금지
- 이름/번호 기반 자동 조회 활용
- 참조 테이블이 먼저 처리되도록 순서 보장

### 3. 트랜잭션 관리
- 대량 데이터는 배치 단위 커밋
- 실패 시 롤백 처리
- 격리 레벨 설정 (SERIALIZABLE)

### 4. 성능 고려사항
- 샘플 데이터는 30행으로 제한
- LLM 호출 비용 최적화
- 불필요한 재처리 방지

## 🔄 업데이트 이력

### v2.0 (현재)
- 다중 테이블 동시 처리 지원
- 통합 프로세서 아키텍처 도입
- 월별 패턴 자동 인식 강화
- 의존성 기반 순차 처리

### v1.0
- 단일 테이블 분류 및 저장
- 기본 LLM 분류 기능
- 수동 컬럼 매핑

## 📚 관련 모듈

- `table_processors.py`: 테이블별 처리 로직
- `prompt_templates.py`: LLM 프롬프트 템플릿
- `vector_similarity_service.py`: 스키마 유사도 분석
- `table_validators.py`: 데이터 검증 로직
- `mv_refresh_service.py`: Materialized View 갱신
- `base_table_processor.py`: 프로세서 기본 클래스

## 🤝 기여 가이드

새로운 테이블 지원 추가 시:
1. `table_processors.py`에 프로세서 클래스 추가
2. `prompt_templates.py`에 매핑 규칙 정의
3. `table_validators.py`에 검증 로직 추가
4. 의존성 레벨 설정 및 테스트

---

*이 문서는 Text2SQL 테이블 문서 업로드 시스템의 핵심 기능과 구현 세부사항을 담고 있습니다.*