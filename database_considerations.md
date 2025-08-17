# 데이터베이스 추가 고려사항

## 📋 목차
1. [인덱스 전략](#인덱스-전략)
2. [전문 검색 설정](#전문-검색-설정)
3. [데이터 보존 정책](#데이터-보존-정책)
4. [백업 및 아카이빙 전략](#백업-및-아카이빙-전략)
5. [성능 최적화](#성능-최적화)
6. [데이터 검증 규칙](#데이터-검증-규칙)
7. [시스템 통합 포인트](#시스템-통합-포인트)
8. [향후 확장 고려사항](#향후-확장-고려사항)

---

## 인덱스 전략

### 1. news 테이블
```sql
-- 이미 생성된 인덱스
CREATE INDEX ix_news_news_id ON news(news_id);
CREATE INDEX ix_news_news_type ON news(news_type);
CREATE INDEX ix_news_published_date ON news(published_date);

-- 추가 권장 인덱스
CREATE INDEX ix_news_source ON news(source);  -- 출처별 조회용
CREATE INDEX ix_news_created_at ON news(created_at DESC);  -- 최신 뉴스 조회용
CREATE INDEX ix_news_tags ON news USING gin(tags);  -- JSONB 태그 검색용
```

### 2. laws 테이블
```sql
-- 이미 생성된 인덱스
CREATE INDEX ix_laws_law_id ON laws(law_id);
CREATE INDEX ix_laws_category ON laws(category);
CREATE INDEX ix_laws_effective_date ON laws(effective_date);

-- 추가 권장 인덱스
CREATE INDEX ix_laws_status ON laws(status);  -- 활성 법령 필터링용
CREATE INDEX ix_laws_enacted_date ON laws(enacted_date);  -- 제정일 기준 조회용
```

### 3. insurance_recognition_criteria 테이블
```sql
-- 이미 생성된 인덱스
CREATE INDEX ix_insurance_recognition_criteria_criteria_id ON insurance_recognition_criteria(criteria_id);
CREATE INDEX ix_insurance_recognition_criteria_product_id ON insurance_recognition_criteria(product_id);
CREATE INDEX ix_insurance_recognition_criteria_status ON insurance_recognition_criteria(status);

-- 추가 권장 인덱스
CREATE INDEX ix_irc_effective_period ON insurance_recognition_criteria(effective_from, effective_to);  -- 유효기간 검색용
CREATE INDEX ix_irc_requirements ON insurance_recognition_criteria USING gin(requirements);  -- JSONB 검색용
```

### 4. news_strategy_reports 테이블
```sql
-- 이미 생성된 인덱스
CREATE INDEX ix_news_strategy_reports_report_id ON news_strategy_reports(report_id);
CREATE INDEX ix_news_strategy_reports_report_type ON news_strategy_reports(report_type);
CREATE INDEX ix_news_strategy_reports_created_by ON news_strategy_reports(created_by);

-- 추가 권장 인덱스
CREATE INDEX ix_nsr_created_at ON news_strategy_reports(created_at DESC);  -- 최신 보고서 조회용
```

---

## 전문 검색 설정

### PostgreSQL 전문 검색 기능 활용

#### 1. 뉴스 검색
```sql
-- 전문 검색용 컬럼 추가
ALTER TABLE news ADD COLUMN search_vector tsvector;

-- 트리거로 자동 업데이트
CREATE OR REPLACE FUNCTION update_news_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('korean', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('korean', coalesce(NEW.content, '')), 'B') ||
        setweight(to_tsvector('korean', coalesce(NEW.source, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER news_search_vector_update
    BEFORE INSERT OR UPDATE ON news
    FOR EACH ROW EXECUTE FUNCTION update_news_search_vector();

-- 전문 검색 인덱스
CREATE INDEX ix_news_search_vector ON news USING gin(search_vector);
```

#### 2. 법령 검색
```sql
-- 전문 검색용 컬럼 추가
ALTER TABLE laws ADD COLUMN search_vector tsvector;

-- 트리거로 자동 업데이트
CREATE OR REPLACE FUNCTION update_laws_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('korean', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('korean', coalesce(NEW.content, '')), 'B') ||
        setweight(to_tsvector('korean', coalesce(NEW.category, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER laws_search_vector_update
    BEFORE INSERT OR UPDATE ON laws
    FOR EACH ROW EXECUTE FUNCTION update_laws_search_vector();

-- 전문 검색 인덱스
CREATE INDEX ix_laws_search_vector ON laws USING gin(search_vector);
```

### 검색 쿼리 예시
```sql
-- 뉴스 검색
SELECT * FROM news
WHERE search_vector @@ plainto_tsquery('korean', '제약 신약')
ORDER BY ts_rank(search_vector, plainto_tsquery('korean', '제약 신약')) DESC;

-- 법령 검색
SELECT * FROM laws
WHERE search_vector @@ plainto_tsquery('korean', '의료기기 인증')
ORDER BY ts_rank(search_vector, plainto_tsquery('korean', '의료기기 인증')) DESC;
```

---

## 데이터 보존 정책

### 1. 뉴스 데이터
- **보존 기간**: 3년
- **아카이빙**: 3년 이상 된 데이터는 별도 아카이브 테이블로 이동
- **삭제 정책**: 5년 이상 된 아카이브 데이터는 완전 삭제

### 2. 법령 데이터
- **보존 기간**: 무기한 (법적 요구사항)
- **버전 관리**: 개정 시 이전 버전도 보존
- **상태 관리**: 폐지된 법령도 'abolished' 상태로 보존

### 3. 보험 인정기준
- **보존 기간**: 유효기간 종료 후 5년
- **이력 관리**: 변경 이력은 별도 audit 테이블에 기록
- **참조 무결성**: 관련 제품이 삭제되어도 기준은 보존

### 4. 전략 보고서
- **보존 기간**: 5년
- **아카이빙**: 2년 이상 된 보고서는 압축 저장
- **첨부 파일**: S3 등 객체 스토리지로 이동

---

## 백업 및 아카이빙 전략

### 1. 백업 전략
```bash
# 일일 백업 (증분)
pg_dump -Fc -t news -t laws -t insurance_recognition_criteria \
        -t news_strategy_reports -t news_strategy_report_references \
        dbname > daily_backup_$(date +%Y%m%d).dump

# 주간 백업 (전체)
pg_dump -Fc dbname > weekly_full_backup_$(date +%Y%m%d).dump

# 월간 백업 (전체 + 압축)
pg_dump -Fc dbname | gzip > monthly_backup_$(date +%Y%m).dump.gz
```

### 2. 아카이빙 전략

#### 아카이브 테이블 구조
```sql
-- 뉴스 아카이브 테이블
CREATE TABLE news_archive (
    LIKE news INCLUDING ALL,
    archived_at TIMESTAMP DEFAULT NOW()
);

-- 보고서 아카이브 테이블
CREATE TABLE news_strategy_reports_archive (
    LIKE news_strategy_reports INCLUDING ALL,
    archived_at TIMESTAMP DEFAULT NOW()
);
```

#### 아카이빙 프로시저
```sql
-- 3년 이상 된 뉴스 아카이빙
CREATE OR REPLACE FUNCTION archive_old_news() RETURNS void AS $$
BEGIN
    INSERT INTO news_archive
    SELECT *, NOW() FROM news
    WHERE published_date < NOW() - INTERVAL '3 years';
    
    DELETE FROM news
    WHERE published_date < NOW() - INTERVAL '3 years';
END;
$$ LANGUAGE plpgsql;
```

---

## 성능 최적화

### 1. 파티셔닝

#### 뉴스 테이블 파티셔닝 (월별)
```sql
-- 파티션 테이블 생성
CREATE TABLE news_partitioned (
    LIKE news INCLUDING ALL
) PARTITION BY RANGE (published_date);

-- 월별 파티션 생성
CREATE TABLE news_2024_01 PARTITION OF news_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
    
CREATE TABLE news_2024_02 PARTITION OF news_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- ... 계속
```

### 2. 쿼리 최적화

#### 자주 사용되는 쿼리용 Materialized View
```sql
-- 최근 뉴스 요약
CREATE MATERIALIZED VIEW recent_news_summary AS
SELECT 
    news_type,
    DATE(published_date) as publish_date,
    COUNT(*) as news_count,
    array_agg(DISTINCT source) as sources
FROM news
WHERE published_date >= NOW() - INTERVAL '30 days'
GROUP BY news_type, DATE(published_date);

CREATE INDEX ix_recent_news_summary ON recent_news_summary(publish_date DESC);

-- 일일 갱신
REFRESH MATERIALIZED VIEW CONCURRENTLY recent_news_summary;
```

### 3. 커넥션 풀링
```python
# SQLAlchemy 설정
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,          # 기본 커넥션 풀 크기
    'max_overflow': 40,       # 최대 오버플로우
    'pool_timeout': 30,       # 타임아웃 (초)
    'pool_recycle': 3600,     # 커넥션 재활용 시간 (초)
    'pool_pre_ping': True,    # 커넥션 유효성 체크
}
```

---

## 데이터 검증 규칙

### 1. 뉴스 데이터 검증
```python
class NewsValidator:
    @staticmethod
    def validate_news(data):
        errors = []
        
        # 제목 검증
        if not data.get('title') or len(data['title']) < 10:
            errors.append("제목은 최소 10자 이상이어야 합니다")
        
        # URL 중복 검증
        if data.get('url'):
            # DB 조회로 중복 체크
            pass
        
        # 날짜 검증
        if data.get('published_date'):
            if data['published_date'] > datetime.now():
                errors.append("미래 날짜는 허용되지 않습니다")
        
        # 뉴스 타입 검증
        if data.get('news_type') not in ['general', 'pharmaceutical']:
            errors.append("유효하지 않은 뉴스 타입입니다")
        
        return errors
```

### 2. 보험 인정기준 검증
```python
class InsuranceCriteriaValidator:
    @staticmethod
    def validate_criteria(data):
        errors = []
        
        # 기간 검증
        if data.get('effective_from') and data.get('effective_to'):
            if data['effective_from'] > data['effective_to']:
                errors.append("시작일이 종료일보다 늦을 수 없습니다")
        
        # 금액 검증
        if data.get('coverage_amount'):
            if data['coverage_amount'] < 0:
                errors.append("보장 금액은 0 이상이어야 합니다")
        
        # 제품 존재 여부 검증
        if data.get('product_id'):
            # DB 조회로 제품 존재 확인
            pass
        
        return errors
```

---

## 시스템 통합 포인트

### 1. 외부 API 연동

#### 뉴스 수집 API
```python
class NewsCollector:
    """외부 뉴스 API와의 통합"""
    
    async def collect_news_from_apis(self):
        sources = [
            {'name': 'NewsAPI', 'url': 'https://newsapi.org/v2/'},
            {'name': 'NaverNews', 'url': 'https://openapi.naver.com/v1/search/news'},
            {'name': 'GoogleNews', 'url': 'https://news.google.com/rss'}
        ]
        
        for source in sources:
            news_items = await self.fetch_from_source(source)
            await self.save_news_batch(news_items)
```

#### 법령 정보 연동
```python
class LawInfoIntegration:
    """법제처 API 연동"""
    
    async def sync_laws(self):
        api_url = "https://www.law.go.kr/DRF/lawService.do"
        # 법령 정보 동기화 로직
```

### 2. 내부 시스템 연동

#### 직원 성과와 뉴스 전략 보고서 연계
```sql
-- 보고서 작성자별 성과 분석
CREATE VIEW employee_report_performance AS
SELECT 
    e.employee_id,
    e.name,
    COUNT(nsr.report_id) as total_reports,
    AVG(jsonb_array_length(nsr.recommendations)) as avg_recommendations
FROM employees e
LEFT JOIN news_strategy_reports nsr ON e.employee_id = nsr.created_by
GROUP BY e.employee_id, e.name;
```

#### 제품과 보험 인정기준 연계
```python
class ProductInsuranceIntegration:
    """제품과 보험 인정기준 통합 관리"""
    
    async def get_product_with_criteria(self, product_id):
        # 제품 정보와 관련 보험 인정기준을 함께 조회
        query = """
            SELECT p.*, 
                   json_agg(irc.*) as insurance_criteria
            FROM products p
            LEFT JOIN insurance_recognition_criteria irc 
                ON p.product_id = irc.product_id
            WHERE p.product_id = :product_id
            GROUP BY p.product_id
        """
```

### 3. 알림 시스템

#### 중요 뉴스 알림
```python
class NewsNotificationService:
    """중요 뉴스 알림 서비스"""
    
    async def check_important_news(self):
        # 키워드 기반 중요 뉴스 감지
        keywords = ['규제', '인증', '급여', '보험']
        
        query = """
            SELECT * FROM news
            WHERE created_at > NOW() - INTERVAL '1 hour'
            AND (
                title ~* ANY(ARRAY[:keywords])
                OR content ~* ANY(ARRAY[:keywords])
            )
        """
        
        important_news = await self.db.fetch(query, keywords=keywords)
        if important_news:
            await self.send_notifications(important_news)
```

---

## 향후 확장 고려사항

### 1. 다국어 지원
```sql
-- 다국어 테이블 구조
CREATE TABLE news_translations (
    translation_id SERIAL PRIMARY KEY,
    news_id INTEGER REFERENCES news(news_id),
    language_code VARCHAR(5),  -- ko, en, ja, zh 등
    title TEXT,
    content TEXT,
    UNIQUE(news_id, language_code)
);
```

### 2. AI/ML 통합
```python
class NewsAnalyzer:
    """AI 기반 뉴스 분석"""
    
    async def analyze_sentiment(self, news_id):
        # 감정 분석
        pass
    
    async def extract_entities(self, news_id):
        # 개체명 인식
        pass
    
    async def classify_importance(self, news_id):
        # 중요도 분류
        pass
```

### 3. 실시간 스트리밍
```python
class NewsStreamService:
    """실시간 뉴스 스트리밍"""
    
    async def stream_news(self):
        # WebSocket을 통한 실시간 뉴스 전송
        pass
```

### 4. 데이터 분석 대시보드
```sql
-- 분석용 집계 테이블
CREATE TABLE news_analytics (
    date DATE PRIMARY KEY,
    news_type VARCHAR(50),
    total_count INTEGER,
    unique_sources INTEGER,
    avg_content_length FLOAT,
    top_keywords JSONB
);

-- 일일 집계 프로시저
CREATE OR REPLACE FUNCTION aggregate_news_analytics() RETURNS void AS $$
BEGIN
    INSERT INTO news_analytics
    SELECT 
        DATE(published_date),
        news_type,
        COUNT(*),
        COUNT(DISTINCT source),
        AVG(LENGTH(content)),
        -- 키워드 추출 로직
    FROM news
    WHERE DATE(published_date) = CURRENT_DATE - 1
    GROUP BY DATE(published_date), news_type;
END;
$$ LANGUAGE plpgsql;
```

### 5. 보안 강화
```python
class DataEncryption:
    """민감 데이터 암호화"""
    
    @staticmethod
    def encrypt_sensitive_fields(data):
        # PII 정보 암호화
        pass
    
    @staticmethod
    def decrypt_sensitive_fields(data):
        # PII 정보 복호화
        pass
```

### 6. 감사(Audit) 로그
```sql
-- 감사 로그 테이블
CREATE TABLE audit_logs (
    audit_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    operation VARCHAR(10),  -- INSERT, UPDATE, DELETE
    user_id INTEGER,
    changed_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 트리거 예시 (뉴스 테이블)
CREATE OR REPLACE FUNCTION audit_news_changes() RETURNS trigger AS $$
BEGIN
    INSERT INTO audit_logs (table_name, operation, user_id, changed_data)
    VALUES (
        'news',
        TG_OP,
        current_setting('app.current_user_id')::INTEGER,
        row_to_json(NEW)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER news_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON news
    FOR EACH ROW EXECUTE FUNCTION audit_news_changes();
```

---

## 모니터링 및 유지보수

### 1. 성능 모니터링
```sql
-- 테이블 크기 모니터링
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename IN ('news', 'laws', 'insurance_recognition_criteria', 
                    'news_strategy_reports', 'news_strategy_report_references')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 인덱스 사용률 모니터링
SELECT 
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### 2. 정기 유지보수
```bash
# VACUUM 및 ANALYZE 스케줄
0 2 * * * psql -d dbname -c "VACUUM ANALYZE news;"
0 3 * * * psql -d dbname -c "VACUUM ANALYZE laws;"
0 4 * * * psql -d dbname -c "VACUUM ANALYZE insurance_recognition_criteria;"

# 인덱스 재구성 (월 1회)
0 5 1 * * psql -d dbname -c "REINDEX TABLE news;"
0 5 1 * * psql -d dbname -c "REINDEX TABLE laws;"
```

### 3. 용량 관리
```python
class StorageManager:
    """스토리지 용량 관리"""
    
    async def check_table_sizes(self):
        query = """
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(tablename::regclass) DESC
        """
        
        results = await self.db.fetch(query)
        
        # 임계값 초과 시 알림
        for table in results:
            if self.parse_size(table['size']) > 10 * 1024 * 1024 * 1024:  # 10GB
                await self.send_alert(f"Table {table['tablename']} exceeds 10GB")
```

---

## 마무리

이 문서는 새로운 데이터베이스 테이블들에 대한 종합적인 고려사항을 담고 있습니다. 실제 구현 시에는 시스템의 요구사항과 제약사항에 맞게 조정이 필요할 수 있습니다.

정기적으로 이 문서를 검토하고 업데이트하여 데이터베이스 관리의 모범 사례를 유지하시기 바랍니다.