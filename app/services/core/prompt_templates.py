"""
LLM 프롬프트 템플릿 모듈
테이블별 맞춤 프롬프트 관리
"""

class PromptTemplates:
    """테이블별 프롬프트 템플릿"""
    
    # 기본 시스템 프롬프트
    SYSTEM_PROMPT = """당신은 Excel 테이블 데이터를 분석하여 적절한 데이터베이스 테이블에 분류하는 전문가입니다. 
    문서의 컬럼과 샘플 데이터를 보고 데이터베이스 테이블의 컬럼에 매핑해주세요.
    
⚠️ 절대 규칙 - 반드시 준수:
1. employee_id, customer_id, product_id는 외래키(Foreign Key)입니다 - 절대 매핑하지 마세요!
2. sales_records 테이블에서:
   - employee_id/customer_id/product_id를 직접 매핑하지 마세요
   - 대신 name/employee_number (직원정보), customer_name (고객정보)를 매핑하세요
3. 업로드 컬럼명을 실제 DB 컬럼명에 정확히 매핑하세요"""
    
    # 기본 헤더
    BASE_HEADER = """업로드된 Excel 파일의 컬럼들을 분석하여 어떤 데이터베이스 테이블들에 데이터를 생성할 수 있는지 판단해주세요.

## 업로드된 문서 정보:
- 컬럼: {columns}
- 샘플 데이터: {sample_data}
- 문서 설명: {description}

## 컬럼 의미 파악 및 매핑 가이드:
업로드된 컬럼의 의미를 파악하여 적절한 DB 컬럼에 매핑하세요:

### 직원 관련 (employee_info, sales_records)
- 직원 번호: 사번, 직원번호, 사내번호, emp_no, 직원ID, 담당자번호 → employee_number
- 직원 이름: 성명, 직원명, 담당자, 영업사원, 담당자명, 이름 → name
- 직급: 직급, 직위, 계급, 포지션 → position
- 지점: 지점명, 지사, 소속, 부서 → branch_name

### 고객 관련 (customers, sales_records, customer_monthly_status)
- 고객명: 거래처ID, 거래처명, 고객명, 병원명, 약국명, 기관명, 회사명, ID → customer_name
- 주소: 주소, 소재지, 위치, 거래처주소, 병원주소, 약국주소, 기관주소, 주소지, 병원소재지 → address
- 의사명: 의사명, 담당의사, 원장, 원장명, 대표의사, 대표원장 → doctor_name  
- 연락처: 전화번호, 연락처, 대표번호, 핸드폰, 거래처전화, 병원연락처 → contact_number
- 환자수: 총환자수, 환자수, 방문자수 → patient_count (customer_monthly_status)
- 월별 환자수: YYYYMM_환자수, 월별환자수, 월환자수 → patient_count (customer_monthly_status)

⚠️ 주의: 주소 관련 컬럼이 있으면 반드시 address로 매핑하세요!

### 제품 관련 (products, sales_records)
- 제품명: 품목, 제품명, 상품명, 약품명, 품명, 아이템 → product_name
- 카테고리: 카테고리, 분류, 종류, 타입 → category
- 설명: 설명, 상세, 비고, 특징 → description

### 지점/조직 관련 (branches)
- 지점명: 지점, 지점명, 지사, 영업소 → branch_name
- 본부: 본부, 사업부, 본사, 헤드쿼터 → headquarters
- 부서: 부서, 팀, 파트, 부문 → department

### 매출/실적 관련 (sales_records)
- 매출액: 매출, 매출액, 판매액, 금액, 실적 → sale_amount
- 날짜: 월, 날짜, 일자, 기간, 년월 → sale_date

### 상호작용 관련 (interaction_logs)
- 상호작용 유형: 방문유형, 미팅타입, 활동종류 → interaction_type
- 요약: 요약, 내용, 설명, 상세내용 → summary

### 월별 상태 관련 (customer_monthly_status)
- 거래처명: 거래처ID, 거래처명, 고객명, 병원명, 약국명 → customer_name (customer_id 조회용)
- 년월: 년월, YYYYMM, 월별, 기간, 월 → year_month
- 환자수: 총환자수, 월별환자수, 월환자수, 방문자수, 내원환자수 → patient_count
- 예산: 사용예산, 사용 예산, 예산액, 지출 → used_budget

⚠️ 중요: 컬럼명이 정확히 일치하지 않아도 의미가 유사하면 매핑하세요!
⚠️ sales_records는 직원 정보와 고객 정보가 모두 필요합니다!

## 관련성이 높은 테이블들과 실제 DB 컬럼:
{related_tables}
"""

    # 테이블별 특수 규칙
    TABLE_RULES = {
        'customer_monthly_status': """
### customer_monthly_status 테이블:
거래처별 월간 상태(환자수, 사용예산) 관리 테이블입니다.

⚠️ 필수 조건 체크:
1. 거래처 정보가 있는가?
   - 거래처ID, 거래처명, 고객명, 병원명, 약국명 → customer_name으로 매핑
   ❌ customer_id로 직접 매핑하지 마세요!

2. 월별 데이터가 있는가?
   - YYYYMM 형식의 컬럼명 또는 년월, 월 컬럼 → year_month
   - 월별 환자수/예산 패턴 (202401_환자수, 202401_예산 등)

3. 환자수 또는 예산 데이터가 있는가?
   - 환자수: 총환자수, 월별환자수, 방문자수, 내원환자수 → patient_count
   - 예산: 사용예산, 사용 예산, 예산액 → used_budget
   - 둘 중 하나라도 있으면 저장 가능

위 조건이 충족되어야 customer_monthly_status로 분류 가능!

⚠️ 매우 중요:
- 월별 환자수 변동 추적이 목적
- 월별 환자수 데이터를 관리
""",
        'sales_records': """
### sales_records 테이블:
매출 실적 기록 테이블입니다.

⚠️ 필수 조건 체크:
1. 직원 정보가 있는가? (다음 중 하나라도 있으면 가능)
   - 사번, 직원번호, 담당자번호, emp_no → employee_number로 매핑
   - 담당자, 영업사원, 직원명, 성명 → name으로 매핑
   ❌ employee_id로 매핑하지 마세요!

2. 고객 정보가 있는가? (다음 중 하나라도 있으면 가능)
   - 거래처ID, 거래처명, 고객명, 병원명, 약국명 → customer_name으로 매핑
   ❌ customer_id로 매핑하지 마세요!

3. 매출 관련 데이터가 있는가?
   - 매출, 매출액, 판매액, 금액 → sale_amount
   - 월, 날짜, 일자, 년월 → sale_date
   - 사용예산, 예산 → used_budget

위 1, 2번이 모두 충족되어야 sales_records로 분류 가능!

⚠️ 매우 중요:
❌ employee_id, customer_id, product_id는 외래키입니다 - 절대 직접 매핑 금지!
✅ 대신 name/employee_number (직원), customer_name (고객)을 매핑하세요!
⚠️ 제품 정보(품목)는 products 테이블에만 product_name으로 매핑하세요!
❌ sales_records에는 product_name을 매핑하지 마세요! (시스템이 자동으로 product_id 연결)
""",

        'employee_info': """
### employee_info 테이블:
- 직원 기본 정보 관리
- 필수: name(직원명/담당자), employee_number(사번)
- 선택: position(직급), branch_id, contact_number 등

매핑 규칙:
- 담당자/직원명/성명 → name
- 사번/직원번호 → employee_number
- 대상/지점 컬럼은 branch 정보이므로 employee_info에서는 무시

""",

        'customers': """
### customers 테이블:
- 거래처/고객 정보 관리
- 필수: customer_name(고객명/거래처명/ID)
- 선택: address, doctor_name, contact_number 등

⚠️ 중요: 모든 고객 정보를 최대한 매핑하세요!

매핑 규칙:
- 거래처/거래처명/고객명/ID → customer_name
- 주소/소재지/위치/병원주소/약국주소 → address (반드시 찾아서 매핑!)
- 원장/원장명/의사명 → doctor_name
- 연락처/전화번호/병원연락처 → contact_number

주소가 있다면 반드시 address로 매핑하세요!
""",

        'products': """
### products 테이블:
- 제품/품목 정보 관리
- 필수: product_name(제품명/품목)
- 선택: description, category 등

매핑 규칙:
- 품목/제품명 → product_name
""",

        'branches': """
### branches 테이블:
- 지점/조직 정보 관리
- 필수: branch_name(지점명), headquarters(본부), department(부서)
- 선택: contact_number, status, notes

매핑 규칙:
- 지점/지점명/지사 → branch_name
- 본부/사업부 → headquarters
- 부서/팀 → department
"""
    }

    # 응답 형식
    RESPONSE_FORMAT = """
## 반드시 지켜야 할 매핑 규칙:

업로드 컬럼에 "사번", "성명"이 있으면:
→ sales_records에 반드시 포함: {{"employee_number": "사번", "name": "성명", ...}}
→ employee_info에도 포함: {{"employee_number": "사번", "name": "성명"}}

업로드 컬럼에 "거래처ID"가 있으면:
→ sales_records에 반드시 포함: {{"customer_name": "거래처ID", ...}}
→ customers에도 포함: {{"customer_name": "거래처ID"}}

업로드 컬럼에 "품목"이 있으면:
→ products에만 포함: {{"product_name": "품목"}}
→ sales_records에는 포함하지 마세요! (시스템이 자동으로 product_id 연결)

sales_records 완전한 매핑 예시:
{{
    "employee_number": "사번",    // 필수
    "name": "성명",               // 필수
    "customer_name": "거래처ID",   // 필수
    "sale_amount": "매출",
    "sale_date": "월",
    "used_budget": "사용 예산"
    // ❌ product_name은 매핑하지 마세요!
}}

## 응답 형식:
{{
    "target_tables": [
        {{
            "table_name": "테이블명",
            "confidence": 0.9,
            "column_mapping": {{
                "실제_DB_컬럼명": "업로드_파일_컬럼명"
            }},
            "reasoning": "매핑 가능 근거"
        }}
    ],
    "confidence": 0.9,
    "reasoning": "전체 분류 근거"
}}

**중요**: 
- sales_records의 경우 직원 정보(name/employee_number)와 고객 정보(customer_name)는 필수입니다
- 필수 컬럼을 매핑할 수 없는 테이블은 포함하지 마세요
- 실제 DB 컬럼명을 사용하세요
- JSON 형식으로만 응답하세요
- 주석을 포함하지 마세요
"""

    @classmethod
    def get_table_prompt(cls, table_name: str) -> str:
        """테이블별 프롬프트 반환"""
        return cls.TABLE_RULES.get(table_name, "")
    
    @classmethod
    def build_prompt(cls, columns: list, sample_data: list, description: str, 
                    related_tables: list) -> str:
        """동적 프롬프트 생성 - DB 컬럼명 직접 제공"""
        # 관련 테이블 정보 구성
        tables_info = []
        table_specific_rules = []
        
        for i, table_info in enumerate(related_tables, 1):
            table_name = table_info['table_name']
            db_columns = table_info.get('columns', [])
            
            # 테이블 정보 추가 (실제 DB 컬럼명 포함)
            tables_info.append(
                f"{i}. {table_name} (유사도: {table_info['similarity']:.3f})\n"
                f"   - 설명: {table_info['description']}\n"
                f"   - DB 컬럼 (실제 컬럼명): {', '.join(db_columns)}\n"
                f"   - 샘플 데이터: {table_info.get('sample_data', [])[:3]}"
            )
            
            # 해당 테이블의 특수 규칙 추가
            specific_rule = cls.get_table_prompt(table_name)
            if specific_rule:
                table_specific_rules.append(specific_rule)
        
        # 프롬프트 조합
        prompt = cls.BASE_HEADER.format(
            columns=', '.join(columns[:50]) if len(columns) > 50 else ', '.join(columns),
            sample_data=sample_data[:3] if sample_data else '없음',
            description=description if description else '없음',
            related_tables='\n'.join(tables_info)
        )
        
        # 테이블별 규칙 추가
        if table_specific_rules:
            prompt += "\n## 테이블별 매핑 규칙:\n"
            prompt += '\n'.join(table_specific_rules)
        
        # 응답 형식 추가
        prompt += "\n" + cls.RESPONSE_FORMAT
        
        return prompt
    
    @classmethod
    def get_dependency_order(cls) -> dict:
        """테이블 의존성 순서"""
        return {
            'branches': 1,
            'customers': 1,
            'products': 1,
            'employee_info': 2,
            'customer_monthly_status': 2,
            'sales_records': 3,
            'interaction_logs': 3,
            'assignment_map': 3,
        }