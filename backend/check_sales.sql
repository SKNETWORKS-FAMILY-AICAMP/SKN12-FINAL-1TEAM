-- 조시현의 employee_id 찾기
SELECT employee_id, name FROM employee_info WHERE name = '조시현';

-- sales_records 테이블 구조 확인
SHOW COLUMNS FROM sales_records;

-- sales_records 데이터 개수 확인
SELECT COUNT(*) as total_records FROM sales_records;

-- 조시현의 sales_records 확인 (employee_id를 적절히 변경)
SELECT * FROM sales_records WHERE employee_id IN (
    SELECT employee_id FROM employee_info WHERE name = '조시현'
) LIMIT 10;

-- 전체 직원별 실적 데이터 현황
SELECT 
    ei.name,
    COUNT(sr.sale_id) as sale_count,
    SUM(sr.sale_amount) as total_amount
FROM employee_info ei
LEFT JOIN sales_records sr ON ei.employee_id = sr.employee_id
GROUP BY ei.employee_id, ei.name
HAVING COUNT(sr.sale_id) > 0
ORDER BY ei.name
LIMIT 20;