-- 직원 실적 Materialized View
-- employee_performance 테이블의 목표와 sales_records의 실제 매출을 조인

-- 기존 뷰가 있다면 삭제
DROP MATERIALIZED VIEW IF EXISTS employee_performance_mv CASCADE;

-- Materialized View 생성
CREATE MATERIALIZED VIEW employee_performance_mv AS
WITH sales_summary AS (
    -- sales_records에서 월별 매출 집계
    SELECT 
        sr.employee_id,
        DATE_TRUNC('month', sr.sale_date)::DATE as year_month,
        SUM(sr.sale_amount) as actual_sales,
        COUNT(*) as sales_count,
        COUNT(DISTINCT sr.customer_id) as customer_count
    FROM 
        sales_records sr
    WHERE 
        sr.sale_date IS NOT NULL
    GROUP BY 
        sr.employee_id,
        DATE_TRUNC('month', sr.sale_date)
)
SELECT 
    COALESCE(ep.employee_id, ss.employee_id) as employee_id,
    ei.name as employee_name,
    ei.employee_number,
    COALESCE(ep.year_month, ss.year_month) as year_month,
    COALESCE(ep.target_amount, 0) as target_amount,
    COALESCE(ss.actual_sales, 0) as actual_sales,
    CASE 
        WHEN ep.target_amount > 0 THEN 
            ROUND((COALESCE(ss.actual_sales, 0) / ep.target_amount) * 100, 2)
        ELSE 0
    END as achievement_rate,
    COALESCE(ss.sales_count, 0) as sales_count,
    COALESCE(ss.customer_count, 0) as customer_count
FROM 
    employee_performance ep
    FULL OUTER JOIN sales_summary ss 
        ON ep.employee_id = ss.employee_id 
        AND ep.year_month = ss.year_month
    LEFT JOIN employee_info ei 
        ON COALESCE(ep.employee_id, ss.employee_id) = ei.employee_info_id
WHERE 
    COALESCE(ep.employee_id, ss.employee_id) IS NOT NULL
WITH DATA;

-- 인덱스 생성 (빠른 조회)
CREATE UNIQUE INDEX idx_employee_performance_mv_pk 
ON employee_performance_mv (employee_id, year_month);

CREATE INDEX idx_employee_performance_mv_yearmonth 
ON employee_performance_mv (year_month);

CREATE INDEX idx_employee_performance_mv_achievement 
ON employee_performance_mv (achievement_rate DESC);

-- 뷰 갱신 명령어 (주기적으로 실행)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY employee_performance_mv;

COMMENT ON MATERIALIZED VIEW employee_performance_mv IS '직원별 월간 목표 대비 실적 (목표: employee_performance 테이블, 실적: sales_records 집계)';