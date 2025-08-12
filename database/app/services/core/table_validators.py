"""
테이블별 검증 로직 모듈
각 테이블의 검증 로직을 분리하여 관리
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class TableValidator:
    """테이블 검증 기본 클래스"""
    
    
    @staticmethod
    def validate_sales_records(
        uploaded_columns: List[str],
        mapping: Dict[str, str],
        sample_data: List[Dict[str, Any]] = None,
        metrics: Dict[str, Any] = None
    ) -> Tuple[bool, str]:
        """sales_records 테이블 검증"""
        # 매핑 키 수정
        if 'customer_id' in mapping:
            mapping['customer_name'] = mapping.pop('customer_id')
        if 'employee_id' in mapping:
            mapping['employee_number'] = mapping.pop('employee_id')
        if 'product_id' in mapping:
            mapping['product_name'] = mapping.pop('product_id')
        
        # 월별 컬럼 패턴 확인
        has_monthly_columns = any(re.fullmatch(r'\d{6}', str(col)) for col in uploaded_columns)
        
        # 매출 관련 키워드 확인
        sales_keywords = ['매출', '매출액', '금액', '수량', '방문횟수', '예산', '환자수', '판매']
        has_sales_related = any(
            any(keyword in str(col).lower() for keyword in sales_keywords)
            for col in uploaded_columns
        )
        
        # 월별 행 데이터 확인
        has_monthly_rows = False
        if sample_data:
            for row in sample_data[:5]:
                for val in row.values():
                    if re.fullmatch(r'\d{6}', str(val)):
                        has_monthly_rows = True
                        break
                if has_monthly_rows:
                    break
        
        # metrics 기반 판단
        if metrics:
            amount_ratio = float(metrics.get('sale_amount_numeric_ratio', 0.0) or 0.0)
            date_ratio = float(metrics.get('sale_date_parse_ratio', 0.0) or 0.0)
            has_amount_date = ('sale_amount' in mapping) and ('sale_date' in mapping)
            
            if has_amount_date and amount_ratio >= 0.7 and date_ratio >= 0.7:
                return True, "sale_amount/sale_date 매핑 확인"
        
        # 검증 조건
        if not (has_monthly_columns or has_sales_related or has_monthly_rows):
            return False, "월별 데이터 또는 매출 관련 컬럼이 부족함"
        
        return True, "sales_records 검증 통과"
    
    @staticmethod
    def validate_employee_info(
        uploaded_columns: List[str],
        mapping: Dict[str, str]
    ) -> Tuple[bool, str]:
        """employee_info 테이블 검증"""
        required = ['name', 'employee_number']
        missing = [col for col in required if col not in mapping]
        
        if missing:
            return False, f"필수 컬럼 누락: {missing}"
        
        return True, "employee_info 검증 통과"
    
    @staticmethod
    def validate_customers(
        uploaded_columns: List[str],
        mapping: Dict[str, str]
    ) -> Tuple[bool, str]:
        """customers 테이블 검증"""
        if 'customer_name' not in mapping:
            return False, "필수 컬럼 누락: customer_name"
        
        return True, "customers 검증 통과"
    
    @staticmethod
    def validate_products(
        uploaded_columns: List[str],
        mapping: Dict[str, str]
    ) -> Tuple[bool, str]:
        """products 테이블 검증"""
        if 'product_name' not in mapping:
            return False, "필수 컬럼 누락: product_name"
        
        return True, "products 검증 통과"
    
    @staticmethod
    def validate_branches(
        uploaded_columns: List[str],
        mapping: Dict[str, str]
    ) -> Tuple[bool, str]:
        """branches 테이블 검증"""
        required = ['branch_name', 'headquarters', 'department']
        missing = [col for col in required if col not in mapping]
        
        if missing:
            return False, f"필수 컬럼 누락: {missing}"
        
        return True, "branches 검증 통과"
    
    @staticmethod
    def validate_employee_performance(
        uploaded_columns: List[str],
        mapping: Dict[str, str],
        sample_data: List[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """employee_performance 테이블 검증"""
        # 월별 컬럼 패턴 확인 (YYYYMM 또는 YYYYMM_목표)
        has_monthly_columns = any(
            re.fullmatch(r'\d{6}', str(col)) or '_목표' in str(col)
            for col in uploaded_columns
        )
        
        # 목표 관련 키워드 확인
        target_keywords = ['목표', 'target', '계획', 'plan', '예산']
        has_target_related = any(
            any(keyword in str(col).lower() for keyword in target_keywords)
            for col in uploaded_columns
        )
        
        # 직원 관련 컬럼 확인
        has_employee = any(
            col in ['대상', '담당자', '직원', '사원', '이름', '성명', '사번']
            for col in uploaded_columns
        )
        
        # 검증 조건
        if not (has_monthly_columns or has_target_related):
            return False, "월별 목표 데이터 또는 목표 관련 컬럼이 부족함"
        
        if not has_employee:
            return False, "직원 정보 컬럼이 없음"
        
        return True, "employee_performance 검증 통과"
    
    @staticmethod
    def validate_table(
        table_name: str,
        uploaded_columns: List[str],
        mapping: Dict[str, str],
        sample_data: List[Dict[str, Any]] = None,
        metrics: Dict[str, Any] = None
    ) -> Tuple[bool, str]:
        """테이블별 검증 라우터"""
        validators = {
            'sales_records': lambda cols, map, data=None: TableValidator.validate_sales_records(cols, map, data, metrics),
            'employee_info': lambda cols, map, data=None: TableValidator.validate_employee_info(cols, map),
            'customers': lambda cols, map, data=None: TableValidator.validate_customers(cols, map),
            'products': lambda cols, map, data=None: TableValidator.validate_products(cols, map),
            'branches': lambda cols, map, data=None: TableValidator.validate_branches(cols, map),
            'employee_performance': lambda cols, map, data=None: TableValidator.validate_employee_performance(cols, map, data),
        }
        
        validator = validators.get(table_name)
        if validator:
            return validator(uploaded_columns, mapping, sample_data)
        
        # 기본 검증 (기타 테이블)
        return True, f"{table_name} 기본 검증 통과"