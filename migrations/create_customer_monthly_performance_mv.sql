-- 거래처별 월간 성과 Materialized View
-- sales_records의 매출, 예산과 customer_monthly_patients의 환자수를 조인

-- 기존 뷰가 있다면 삭제
DROP MATERIALIZED VIEW IF EXISTS customer_monthly_performance_mv CASCADE;

-- Materialized View 생성
CREATE MATERIALIZED VIEW customer_monthly_performance_mv AS
WITH sales_summary AS (
    -- sales_records에서 월별 매출 및 예산 집계
    SELECT 
        sr.customer_id,
        TO_CHAR(sr.sale_date, 'YYYY-MM') as year_month,
        SUM(sr.sale_amount) as monthly_sales,
        SUM(sr.used_budget) as budget_used,
        COUNT(DISTINCT sr.sale_date) as visit_count,
        COUNT(DISTINCT sr.record_id) as transaction_count
    FROM 
        sales_records sr
    WHERE 
        sr.sale_date IS NOT NULL
    GROUP BY 
        sr.customer_id,
        TO_CHAR(sr.sale_date, 'YYYY-MM')
),
patient_summary AS (
    -- customer_monthly_patients에서 월별 환자수 조회
    SELECT 
        customer_id,
        year_month,
        patient_count
    FROM 
        customer_monthly_patients
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY c.customer_id, COALESCE(ss.year_month, ps.year_month)) as performance_id,
    c.customer_id,
    c.customer_name,
    c.customer_grade,
    COALESCE(ss.year_month, ps.year_month) as year_month,
    COALESCE(ss.monthly_sales, 0) as monthly_sales,
    COALESCE(ss.budget_used, 0) as budget_used,
    COALESCE(ss.visit_count, 0) as visit_count,
    COALESCE(ss.transaction_count, 0) as transaction_count,
    COALESCE(ps.patient_count, 0) as patient_count,
    NOW() as created_at
FROM 
    customers c
    LEFT JOIN sales_summary ss ON c.customer_id = ss.customer_id
    FULL OUTER JOIN patient_summary ps 
        ON c.customer_id = ps.customer_id 
        AND ss.year_month = ps.year_month
WHERE 
    c.is_deleted = false
    AND (ss.year_month IS NOT NULL OR ps.year_month IS NOT NULL)
WITH DATA;

-- 인덱스 생성 (빠른 조회)
CREATE UNIQUE INDEX idx_customer_performance_mv_pk 
ON customer_monthly_performance_mv (performance_id);

CREATE INDEX idx_customer_performance_mv_customer 
ON customer_monthly_performance_mv (customer_id);

CREATE INDEX idx_customer_performance_mv_yearmonth 
ON customer_monthly_performance_mv (year_month);

CREATE INDEX idx_customer_performance_mv_customer_yearmonth 
ON customer_monthly_performance_mv (customer_id, year_month);

-- 뷰 갱신 명령어 (주기적으로 실행 필요)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY customer_monthly_performance_mv;

COMMENT ON MATERIALIZED VIEW customer_monthly_performance_mv IS '거래처별 월간 성과 (매출, 예산, 환자수 포함)';