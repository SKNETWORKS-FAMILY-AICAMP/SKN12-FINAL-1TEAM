import pymysql
import json

# 데이터베이스 연결
conn = pymysql.connect(
    host='localhost',
    port=3307,
    user='root',
    password='rootpassword',
    database='narutalk_db'
)

cursor = conn.cursor()

# 1. 조시현 직원 정보 확인
print("=" * 60)
print("1. 조시현 직원 정보 검색")
print("=" * 60)
cursor.execute("""
    SELECT employee_id, employee_number, name, position, branch_name 
    FROM employee_info 
    WHERE name LIKE '%조시현%'
""")
employees = cursor.fetchall()
print(f"조시현 검색 결과: {len(employees)}명")
for emp in employees:
    print(f"  - ID: {emp[0]}, 사번: {emp[1]}, 이름: {emp[2]}, 직급: {emp[3]}, 지점: {emp[4]}")

# 2. 실적 데이터 확인
if employees:
    print("\n" + "=" * 60)
    print("2. 조시현 실적 데이터 확인")
    print("=" * 60)
    
    for emp in employees:
        emp_id = emp[0]
        emp_name = emp[2]
        
        cursor.execute(f"""
            SELECT year_month, amount, target 
            FROM employee_performance 
            WHERE employee_id = {emp_id}
            ORDER BY year_month
        """)
        performance = cursor.fetchall()
        
        print(f"\n{emp_name} (ID: {emp_id}) 실적:")
        if performance:
            for perf in performance[:10]:  # 처음 10개만
                print(f"  - {perf[0]}: 실적 {perf[1]:,}원, 목표 {perf[2]:,}원")
            if len(performance) > 10:
                print(f"  ... 외 {len(performance)-10}개 더")
        else:
            print("  실적 데이터 없음!")

# 3. 전체 실적 데이터 현황
print("\n" + "=" * 60)
print("3. 전체 실적 데이터 현황")
print("=" * 60)

cursor.execute("""
    SELECT 
        COUNT(DISTINCT employee_id) as emp_count,
        COUNT(*) as total_records,
        MIN(year_month) as min_month,
        MAX(year_month) as max_month
    FROM employee_performance
""")
stats = cursor.fetchone()
print(f"실적 데이터가 있는 직원 수: {stats[0]}명")
print(f"전체 실적 레코드 수: {stats[1]}개")
print(f"데이터 기간: {stats[2]} ~ {stats[3]}")

# 4. 실적이 있는 직원 목록
cursor.execute("""
    SELECT DISTINCT ei.name, COUNT(ep.performance_id) as record_count
    FROM employee_info ei
    LEFT JOIN employee_performance ep ON ei.employee_id = ep.employee_id
    GROUP BY ei.employee_id, ei.name
    HAVING COUNT(ep.performance_id) > 0
    ORDER BY ei.name
    LIMIT 20
""")
employees_with_perf = cursor.fetchall()
print(f"\n실적 데이터가 있는 직원 (상위 20명):")
for emp in employees_with_perf:
    print(f"  - {emp[0]}: {emp[1]}개 레코드")

cursor.close()
conn.close()

print("\n데이터 확인 완료!")