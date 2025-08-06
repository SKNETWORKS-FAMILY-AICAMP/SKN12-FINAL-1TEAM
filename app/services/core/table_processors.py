"""
구체적인 테이블 처리기들
"""

import logging
import re
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.employee_info import EmployeeInfo  
from app.models.customers import Customer
from app.models.products import Product
from app.models.sales_records import SalesRecord

from .base_table_processor import BaseTableProcessor

logger = logging.getLogger(__name__)

class EmployeeProcessor(BaseTableProcessor):
    """직원 정보 처리기"""
    
    def get_table_name(self) -> str:
        return "employee_info"
    
    def get_unit_name(self) -> str:
        return "명"
    
    def get_unique_fields(self) -> List[str]:
        return ["employee_number", "name"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """사번으로 기존 직원 조회"""
        employee_number = self.extract_required_field(row, column_mapping, "employee_number", required=True)
        if not employee_number:
            return None
        
        result = await self.session.execute(
            select(EmployeeInfo).filter(EmployeeInfo.employee_number == employee_number)
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 직원 레코드 생성"""
        # 필수 필드 검증
        name = self.extract_required_field(row, column_mapping, "name", required=True)
        employee_number = self.extract_required_field(row, column_mapping, "employee_number", required=True)
        
        if not name or not employee_number:
            raise ValueError(f"필수 필드 누락: name={name}, employee_number={employee_number}")
        
        # EmployeeInfo 모델의 유효한 필드들
        valid_fields = {
            'name', 'employee_number', 'team', 'position', 'business_unit', 
            'branch', 'contact_number', 'base_salary', 'incentive_pay', 
            'avg_monthly_budget', 'latest_evaluation', 'responsibilities'
        }
        
        employee_data = {
            'name': name,
            'employee_number': employee_number
        }
        
        # 다른 필드들 매핑
        for db_field, source_column in column_mapping.items():
            if db_field in valid_fields and source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    employee_data[db_field] = value
        
        return EmployeeInfo(**employee_data)
    
    def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 직원 레코드 업데이트"""
        for db_field, source_column in column_mapping.items():
            if source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    setattr(existing_record, db_field, value)

class CustomerProcessor(BaseTableProcessor):
    """고객 정보 처리기"""
    
    def get_table_name(self) -> str:
        return "customers"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["customer_name"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """고객명으로 기존 고객 조회"""
        customer_name = self.extract_required_field(row, column_mapping, "customer_name", required=True)
        if not customer_name:
            return None
        
        # 고객명으로만 조회
        result = await self.session.execute(
            select(Customer).filter(Customer.customer_name == customer_name)
        )
        
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 고객 레코드 생성"""
        customer_name = self.extract_required_field(row, column_mapping, "customer_name", required=True)
        if not customer_name:
            raise ValueError(f"필수 필드 누락: customer_name={customer_name}")
        
        customer_data = {
            'customer_name': customer_name,  # 원본 고객명 사용
        }
        
        # 다른 필드들 매핑
        valid_fields = {
            'customer_name', 'address', 'doctor_name', 'total_patients', 
            'customer_grade', 'notes'
        }
        
        for db_field, source_column in column_mapping.items():
            if db_field in valid_fields and source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    customer_data[db_field] = value
        
        return Customer(**customer_data)
    
    def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 고객 레코드 업데이트"""
        for db_field, source_column in column_mapping.items():
            if source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    setattr(existing_record, db_field, value)

class ProductProcessor(BaseTableProcessor):
    """제품 정보 처리기"""
    
    def get_table_name(self) -> str:
        return "products"
    
    def get_unit_name(self) -> str:
        return "개"
    
    def get_unique_fields(self) -> List[str]:
        return ["product_name"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """제품명으로 기존 제품 조회"""
        product_name = self.extract_required_field(row, column_mapping, "product_name", required=True)
        if not product_name:
            return None
        
        result = await self.session.execute(
            select(Product).filter(Product.product_name == product_name)
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 제품 레코드 생성"""
        product_name = self.extract_required_field(row, column_mapping, "product_name", required=True)
        if not product_name:
            raise ValueError(f"필수 필드 누락: product_name={product_name}")
        
        product_data = {
            'product_name': product_name,
        }
        
        # 다른 필드들 매핑
        valid_fields = {
            'product_name', 'description', 'category', 'is_active'
        }
        
        for db_field, source_column in column_mapping.items():
            if db_field in valid_fields and source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    product_data[db_field] = value
        
        return Product(**product_data)
    
    def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 제품 레코드 업데이트"""
        for db_field, source_column in column_mapping.items():
            if source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    setattr(existing_record, db_field, value)

class SalesRecordProcessor(BaseTableProcessor):
    """매출 기록 처리기"""
    
    def get_table_name(self) -> str:
        return "sales_records"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["sale_amount", "sale_date"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """매출 기록은 중복 체크 없이 항상 새로 생성"""
        return None  # 매출 기록은 중복 체크하지 않음
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 매출 기록 생성 (외래키 해결 포함)"""
        # 월별 매출 데이터 처리
        monthly_sales = self._extract_monthly_sales_data(row, column_mapping)
        if monthly_sales:
            # 월별 매출 데이터가 있으면 개별 매출 기록으로 변환
            return await self._create_monthly_sales_records(row, column_mapping, monthly_sales)
        
        # 일반 매출 데이터 처리
        sale_amount = None
        sale_date = None
        
        if 'sale_amount' in column_mapping and row.get(column_mapping['sale_amount']):
            sale_amount = str(row[column_mapping['sale_amount']]).strip()
        
        if 'sale_date' in column_mapping and row.get(column_mapping['sale_date']):
            sale_date = str(row[column_mapping['sale_date']]).strip()
        
        if not sale_amount or not sale_date or sale_amount == 'nan' or sale_date == 'nan':
            raise ValueError(f"필수 필드 누락: sale_amount={sale_amount}, sale_date={sale_date}")
        
        # 외래키 해결
        customer_id = await self._get_or_create_customer_id(row, column_mapping)
        employee_id = await self._get_or_create_employee_id(row, column_mapping)
        product_id = await self._get_or_create_product_id(row, column_mapping)
        
        # 매출 기록 생성 (employee_id와 customer_id는 필수)
        sales_data = {
            'sale_amount': float(sale_amount.replace(',', '').replace('₩', '').strip()),
            'sale_date': self._parse_date(sale_date),
            'customer_id': customer_id,  # 필수
            'employee_id': employee_id,  # 필수
            'product_id': product_id
        }
        
        # product_id만 None이 아닌 경우에만 포함
        if sales_data['product_id'] is None:
            del sales_data['product_id']
        
        return SalesRecord(**sales_data)
    
    def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """매출 기록은 업데이트하지 않음 (항상 새로 생성)"""
        pass
    
    async def _get_or_create_customer_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> int:
        """고객 ID를 안전하게 가져오거나 생성 (필수 값)"""
        try:
            # 고객명 추출
            customer_name = None
            if 'customer_name' in column_mapping and row.get(column_mapping['customer_name']):
                customer_name = str(row[column_mapping['customer_name']]).strip()
            
            # 디버깅을 위한 로깅 추가
            logger.info(f"고객명 추출 시도: column_mapping['customer_name']={column_mapping.get('customer_name')}, row[column_mapping['customer_name']]={row.get(column_mapping.get('customer_name'))}, 최종 customer_name={customer_name}")
            
            if not customer_name or customer_name == 'nan' or customer_name == '':
                logger.error(f"고객명이 유효하지 않음: customer_name='{customer_name}', row={row}, column_mapping={column_mapping}")
                raise ValueError("고객명이 필수입니다.")
            
            # 기존 고객 확인 (고객명으로만 조회)
            result = await self.session.execute(
                select(Customer).filter(Customer.customer_name == customer_name)
            )
            existing_customer = result.scalar_one_or_none()
            
            if existing_customer:
                return existing_customer.customer_id
            else:
                # 새 고객 생성 (CustomerProcessor 사용)
                processor = get_table_processor('customers', self.session)
                new_customer = await processor.create_new_record(row, column_mapping)
                new_customer.is_auto_created = True
                new_customer.approval_status = 'pending'
                self.session.add(new_customer)
                await self.session.flush()
                return new_customer.customer_id
                
        except Exception as e:
            logger.error(f"고객 ID 생성 중 오류: {e}")
            raise ValueError(f"고객 ID 생성 실패: {str(e)}")
    
    async def _get_or_create_employee_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> int:
        """직원 ID를 안전하게 가져오거나 생성 (필수 값)"""
        try:
            # 직원명 또는 사번 추출
            employee_name = None
            employee_number = None
            
            if 'employee_name' in column_mapping and row.get(column_mapping['employee_name']):
                employee_name = str(row[column_mapping['employee_name']]).strip()
            
            if 'employee_number' in column_mapping and row.get(column_mapping['employee_number']):
                employee_number = str(row[column_mapping['employee_number']]).strip()
            
            if not employee_name and not employee_number:
                raise ValueError("직원명 또는 사번이 필수입니다.")
            
            # 기존 직원 확인 (사번 우선, 없으면 이름으로)
            if employee_number and employee_number != 'nan':
                result = await self.session.execute(
                    select(EmployeeInfo).filter(EmployeeInfo.employee_number == employee_number)
                )
                existing_employee = result.scalar_one_or_none()
                
                if existing_employee:
                    return existing_employee.employee_info_id
            elif employee_name and employee_name != 'nan':
                result = await self.session.execute(
                    select(EmployeeInfo).filter(EmployeeInfo.name == employee_name)
                )
                existing_employee = result.scalar_one_or_none()
                
                if existing_employee:
                    return existing_employee.employee_info_id
            
            # 새 직원 생성 (EmployeeProcessor 사용)
            processor = get_table_processor('employee_info', self.session)
            new_employee = await processor.create_new_record(row, column_mapping)
            new_employee.is_auto_created = True
            new_employee.approval_status = 'pending'
            self.session.add(new_employee)
            await self.session.flush()
            return new_employee.employee_info_id
                
        except Exception as e:
            logger.error(f"직원 ID 생성 중 오류: {e}")
            raise ValueError(f"직원 ID 생성 실패: {str(e)}")
    
    async def _get_or_create_product_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """제품 ID를 안전하게 가져오거나 생성"""
        try:
            # 제품명 추출
            product_name = None
            if 'product_name' in column_mapping and row.get(column_mapping['product_name']):
                product_name = str(row[column_mapping['product_name']]).strip()
            
            if not product_name or product_name == 'nan':
                return None
            
            # 기존 제품 확인 (제품명으로만 조회)
            result = await self.session.execute(
                select(Product).filter(Product.product_name == product_name)
            )
            existing_product = result.scalar_one_or_none()
            
            if existing_product:
                return existing_product.product_id
            else:
                # 새 제품 생성 (ProductProcessor 사용)
                processor = get_table_processor('products', self.session)
                new_product = await processor.create_new_record(row, column_mapping)
                new_product.is_auto_created = True
                new_product.approval_status = 'pending'
                self.session.add(new_product)
                await self.session.flush()
                return new_product.product_id
                
        except Exception as e:
            logger.error(f"제품 ID 생성 중 오류: {e}")
            return None
    
    def _extract_monthly_sales_data(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """월별 매출 데이터 추출"""
        monthly_sales = []
        
        for source_column, value in row.items():
            # YYYYMM 형식 컬럼 확인 (예: 202212, 202301)
            if re.match(r'^\d{6}$', str(source_column)) and value is not None:
                try:
                    sale_amount = float(str(value).replace(',', '').strip())
                    if sale_amount > 0:  # 매출이 있는 경우만 처리
                        # YYYYMM → YYYY-MM-01 형식으로 변환
                        year = str(source_column)[:4]
                        month = str(source_column)[4:6]
                        sale_date = f"{year}-{month}-01"
                        
                        monthly_sales.append({
                            'sale_amount': sale_amount,
                            'sale_date': sale_date,
                            'source_column': source_column
                        })
                except (ValueError, TypeError):
                    continue
        
        return monthly_sales
    
    async def _create_monthly_sales_records(self, row: Dict[str, Any], column_mapping: Dict[str, str], monthly_sales: List[Dict[str, Any]]) -> List[SalesRecord]:
        """월별 매출 데이터를 개별 매출 기록으로 변환"""
        sales_records = []
        
        # 외래키 해결 (한 번만)
        customer_id = await self._get_or_create_customer_id(row, column_mapping)
        employee_id = await self._get_or_create_employee_id(row, column_mapping)
        product_id = await self._get_or_create_product_id(row, column_mapping)
        
        for monthly_sale in monthly_sales:
            sales_data = {
                'sale_amount': monthly_sale['sale_amount'],
                'sale_date': self._parse_date(monthly_sale['sale_date']),
                'customer_id': customer_id,  # 필수
                'employee_id': employee_id,  # 필수
                'product_id': product_id
            }
            
            # product_id만 None이 아닌 경우에만 포함
            if sales_data['product_id'] is None:
                del sales_data['product_id']
            
            if sales_data.get('sale_date') and sales_data.get('sale_amount'):
                sales_record = SalesRecord(**sales_data)
                sales_records.append(sales_record)
        
        return sales_records
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열을 datetime 객체로 변환"""
        
        if not date_str or date_str == 'nan':
            return None
        
        # 다양한 날짜 형식 처리
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
        ]
        
        for pattern in date_patterns:
            match = re.match(pattern, date_str)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    try:
                        if len(groups[0]) == 4:  # YYYY-MM-DD or YYYY/MM/DD
                            return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                        else:  # MM-DD-YYYY or MM/DD/YYYY
                            return datetime(int(groups[2]), int(groups[0]), int(groups[1]))
                    except ValueError:
                        continue
        
        # 패턴 매칭이 안되면 기본 파싱 시도
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"날짜 파싱 실패: {date_str}")
                return None

# 처리기 팩토리
def get_table_processor(table_name: str, session: AsyncSession) -> BaseTableProcessor:
    """테이블 이름에 따른 적절한 처리기 반환"""
    processors = {
        'employee_info': EmployeeProcessor,
        'customers': CustomerProcessor,
        'products': ProductProcessor,
        'sales_records': SalesRecordProcessor,
    }
    
    processor_class = processors.get(table_name)
    if not processor_class:
        raise ValueError(f"지원하지 않는 테이블: {table_name}")
    
    return processor_class(session)