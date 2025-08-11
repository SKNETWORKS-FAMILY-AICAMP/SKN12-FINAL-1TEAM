"""
LLM 프롬프트 템플릿 모듈
테이블별 맞춤 프롬프트 관리
"""

class PromptTemplates:
    """테이블별 프롬프트 템플릿"""
    
    # 기본 시스템 프롬프트
    SYSTEM_PROMPT = "당신은 Excel 테이블 데이터를 분석하여 적절한 데이터베이스 테이블에 분류하는 전문가입니다."
    
    # 기본 헤더
    BASE_HEADER = """업로드된 Excel 파일의 컬럼들을 분석하여 어떤 데이터베이스 테이블들에 데이터를 생성할 수 있는지 판단해주세요.

## 업로드된 문서 정보:
- 컬럼: {columns}
- 샘플 데이터: {sample_data}
- 문서 설명: {description}

## 관련성이 높은 테이블들:
{related_tables}
"""

    # 테이블별 특수 규칙
    TABLE_RULES = {
        'sales_records': """
### sales_records 테이블 특별 처리:
- 월별 매출 데이터 자동 인식
- YYYYMM 형식 컬럼의 값이 매출 데이터인 경우
- 담당자/사번/거래처/품목 + 월별 매출 구조
- 월별 컬럼은 sale_amount/sale_date로 매핑하지 않음 (자동 처리)

필요한 매핑:
- employee_name: 담당자 컬럼
- employee_number: 사번 컬럼
- customer_name: 거래처/ID 컬럼
- product_name: 품목 컬럼 (선택)
""",

        'employee_info': """
### employee_info 테이블:
- 직원 기본 정보 관리
- 필수: name(직원명/담당자), employee_number(사번)
- 선택: position(직급), branch_id, contact_number 등

매핑 규칙:
- 담당자/직원명/성명 → name (보통 두 번째 컬럼)
- 사번/직원번호 → employee_number (보통 세 번째 컬럼)
- 대상/지점 컬럼은 branch 정보이므로 employee_info에서는 무시

중요: 다단계 헤더 구조에서 처리된 컬럼명을 그대로 사용해야 함
""",

        'customers': """
### customers 테이블:
- 거래처/고객 정보 관리
- 필수: customer_name(고객명/거래처명/ID)
- 선택: address, doctor_name, total_patients 등

매핑 규칙:
- 거래처/거래처명/고객명/ID → customer_name
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
""",

        'employee_performance': """
### employee_performance 테이블:
- 직원별 월간 목표 관리
- 목표/계획/예산 데이터 저장
- 월별 목표 데이터 자동 처리

인식 조건:
1. 202401_목표, 202402_목표 같은 YYYYMM_목표 패턴 컬럼
2. "목표", "계획", "예산" 키워드가 컬럼에 포함
3. 월별 데이터 구조

매핑 규칙:
- column_mapping은 비워두거나 최소한만 지정
- 월별 목표 컬럼(YYYYMM_목표)은 자동으로 인식되므로 매핑 불필요
- 담당자, 사번 컬럼도 위치로 자동 인식

**중요**: 
- column_mapping에 "YYYYMM_목표" 같은 패턴을 넣지 마세요
- 실제 컬럼명을 매핑하거나, 빈 객체 {} 를 사용하세요
- 처리기가 자동으로 월별 목표를 추출합니다
"""
    }

    # 응답 형식
    RESPONSE_FORMAT = """
## 응답 형식:
{{
    "target_tables": [
        {{
            "table_name": "테이블명",
            "confidence": 0.9,
            "column_mapping": {{
                "db_column": "source_column"
            }},
            "reasoning": "매핑 가능 근거"
        }}
    ],
    "confidence": 0.9,
    "reasoning": "전체 분류 근거"
}}

**중요**: 
- 필수 컬럼을 매핑할 수 없는 테이블은 포함하지 마세요
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
        """동적 프롬프트 생성"""
        # 관련 테이블 정보 구성
        tables_info = []
        table_specific_rules = []
        
        for i, table_info in enumerate(related_tables, 1):
            table_name = table_info['table_name']
            
            # 테이블 정보 추가
            tables_info.append(
                f"{i}. {table_name} (유사도: {table_info['similarity']:.3f})\n"
                f"   - 설명: {table_info['description']}\n"
                f"   - 컬럼: {', '.join(table_info.get('columns', []))}"
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
            'employee_performance': 3,
            'sales_records': 3,
            'interaction_logs': 3,
            'assignment_map': 3,
        }