"""
테이블별 데이터 처리기 모듈
각 테이블에 특화된 처리 로직을 구현
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee_info import EmployeeInfo
from app.models.customers import Customer
from app.models.products import Product
from app.models.sales_records import SalesRecord
from app.models.documents import Document
from app.models.document_relations import DocumentRelation
from app.models.interaction_logs import InteractionLog
from app.models.assignment_map import AssignmentMap
from app.models.employee_performance import EmployeePerformance
from app.models.customer_monthly_status import CustomerMonthlyStatus
from app.services.core.base_table_processor import BaseTableProcessor
from app.services.utils.foreign_key_utils import get_customer_id, get_employee_id, get_product_id

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
        
        # EmployeeInfo 모델의 유효한 필드들 (branch_id 추가)
        valid_fields = {
            'name', 'employee_number', 'position', 'branch_id',
            'contact_number', 'base_salary', 'incentive_pay', 
            'avg_monthly_budget', 'latest_evaluation', 'responsibilities'
        }
        
        employee_data = {
            'name': name,
            'employee_number': employee_number
        }
        
        # branch_id 특별 처리
        if 'branch_id' in column_mapping:
            branch_name = row.get(column_mapping['branch_id'])
            if branch_name and str(branch_name).strip() and str(branch_name) != 'nan':
                branch_id = await self._get_branch_id(str(branch_name).strip())
                if branch_id:
                    employee_data['branch_id'] = branch_id
        
        # 다른 필드들 매핑
        for db_field, source_column in column_mapping.items():
            if db_field in valid_fields and db_field != 'branch_id' and source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    employee_data[db_field] = value
        
        return EmployeeInfo(**employee_data)
    
    async def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 직원 레코드 업데이트"""
        # branch_id 특별 처리
        if 'branch_id' in column_mapping:
            branch_name = row.get(column_mapping['branch_id'])
            if branch_name and str(branch_name).strip() and str(branch_name) != 'nan':
                branch_id = await self._get_branch_id(str(branch_name).strip())
                if branch_id:
                    setattr(existing_record, 'branch_id', branch_id)
        
        # 다른 필드들 업데이트
        for db_field, source_column in column_mapping.items():
            if db_field != 'branch_id' and source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    setattr(existing_record, db_field, value)
    
    async def _get_branch_id(self, branch_name: str) -> Optional[int]:
        """지점명으로 branch_id 조회"""
        try:
            from app.models.branches import Branch
            result = await self.session.execute(
                select(Branch).filter(Branch.branch_name == branch_name)
            )
            branch = result.scalar_one_or_none()
            if branch:
                return branch.branch_id
            else:
                logger.warning(f"지점을 찾을 수 없음: {branch_name}")
                return None
        except Exception as e:
            logger.error(f"지점 ID 조회 중 오류: {e}")
            return None

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
            'customer_name', 'address', 'doctor_name', 'contact_number', 'total_patients', 
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
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.total_records_created = 0  # 전체 배치에서 생성된 총 레코드 수
        self.total_records_updated = 0  # 전체 배치에서 업데이트된 총 레코드 수
    
    def get_table_name(self) -> str:
        return "sales_records"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["sale_amount", "sale_date"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """직원ID + 고객ID + 제품ID + 날짜로 기존 매출 레코드 조회"""
        try:
            # 날짜 추출
            sale_date = None
            if 'sale_date' in column_mapping:
                source_col = column_mapping['sale_date']
                if source_col in row and row[source_col] is not None:
                    sale_date = str(row[source_col]).strip()
            
            if not sale_date:
                # 자동 인식: 날짜 관련 컬럼 찾기
                date_keywords = ['월', '날짜', '일자', '기간', '년월']
                for col_name, value in row.items():
                    if any(keyword in str(col_name) for keyword in date_keywords):
                        if value and str(value).strip() != 'nan':
                            sale_date = str(value).strip()
                            break
            
            if not sale_date:
                return None
            
            # 직원ID, 고객ID, 제품ID 해결
            try:
                employee_id = await self._get_or_create_employee_id(row, column_mapping)
                customer_id = await self._get_or_create_customer_id(row, column_mapping)
                product_id = await self._get_or_create_product_id(row, column_mapping)
                parsed_date = self._parse_date(sale_date)
                
                # 제품ID가 없으면 조회하지 않음 (저장도 안 할 것이므로)
                if not employee_id or not customer_id or not product_id or not parsed_date:
                    return None
                
                # 동일한 직원+고객+제품+날짜 조합의 기존 레코드 조회
                result = await self.session.execute(
                    select(SalesRecord).filter(
                        SalesRecord.employee_id == employee_id,
                        SalesRecord.customer_id == customer_id,
                        SalesRecord.product_id == product_id,
                        SalesRecord.sale_date == parsed_date
                    )
                )
                return result.scalar_one_or_none()
                
            except Exception as e:
                logger.debug(f"외래키 해결 실패, 새 레코드로 처리: {e}")
                return None
                
        except Exception as e:
            logger.error(f"기존 매출 레코드 조회 중 오류: {e}")
            return None
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, Any]):
        """새 매출 기록 생성 (외래키 해결 포함)"""
        # 상세 row 데이터 로그 제거 - 너무 길고 반복적
        
        # 월별 매출 데이터 처리
        monthly_sales = self._extract_monthly_sales_data(row, column_mapping)
        if monthly_sales:
            logger.debug(f"월별 매출 데이터 발견: {len(monthly_sales)}개")
            # 월별 매출 데이터가 있으면 개별 매출 기록으로 변환
            return await self._create_monthly_sales_records(row, column_mapping, monthly_sales)
        
        # 일반 매출 데이터 처리
        sale_amount = None
        sale_date = None
        
        # sale_amount 추출 (매핑 또는 자동 인식)
        if 'sale_amount' in column_mapping:
            source_col = column_mapping['sale_amount']
            if source_col in row and row[source_col] is not None:
                sale_amount = str(row[source_col]).strip()
                logger.debug(f"매출 매핑으로 추출: {source_col} = {sale_amount}")
        
        if not sale_amount:
            # 자동 인식: 매출 관련 컬럼 찾기 (사용 예산은 제외)
            amount_keywords = ['매출', '매출액', '금액', '수량', '판매액', '판매량']
            for col_name, value in row.items():
                if '예산' not in str(col_name) and any(keyword in str(col_name) for keyword in amount_keywords):
                    if value and str(value).strip() != 'nan':
                        try:
                            # 숫자인지 확인
                            test_value = str(value).replace(',', '').replace('₩', '').strip()
                            float(test_value)  # 숫자 변환 가능한지 테스트
                            sale_amount = str(value).strip()
                            logger.debug(f"매출 컬럼 자동 인식: {col_name} → sale_amount")
                            break
                        except ValueError:
                            continue
        
        # sale_date 추출 (매핑 또는 자동 인식)
        if 'sale_date' in column_mapping:
            source_col = column_mapping['sale_date']
            if source_col in row and row[source_col] is not None:
                sale_date = str(row[source_col]).strip()
                logger.debug(f"날짜 매핑으로 추출: {source_col} = {sale_date}")
        
        if not sale_date:
            # 자동 인식: 날짜 관련 컬럼 찾기
            date_keywords = ['월', '날짜', '일자', '기간', '년월']
            for col_name, value in row.items():
                if any(keyword in str(col_name) for keyword in date_keywords):
                    if value and str(value).strip() != 'nan':
                        sale_date = str(value).strip()
                        logger.debug(f"날짜 컬럼 자동 인식: {col_name} → sale_date")
                        break
        
        if not sale_amount or not sale_date or sale_amount == 'nan' or sale_date == 'nan':
            raise ValueError(f"필수 필드 누락: sale_amount={sale_amount}, sale_date={sale_date}")
        
        
        # 매출액 숫자로 변환
        sale_amount_float = float(sale_amount.replace(',', '').replace('₩', '').strip())
        
        # 매출이 0이거나 없으면 건너뛰기 (정상 케이스)
        if sale_amount_float <= 0:
            # 건너뛰기 신호를 위해 None 반환
            return None
        
        # 외래키 해결
        customer_id = await self._get_or_create_customer_id(row, column_mapping)
        employee_id = await self._get_or_create_employee_id(row, column_mapping)
        product_id = await self._get_or_create_product_id(row, column_mapping)
        
        # 제품 정보가 없으면 건너뛰기
        if not product_id:
            logger.warning(f"제품 정보가 없어 매출 데이터를 건너뜁니다. (직원: {row.get(column_mapping.get('name'))}, 고객: {row.get(column_mapping.get('customer_name'))}, 날짜: {sale_date})")
            return None
        
        # 매출 기록 생성 (employee_id, customer_id, product_id 모두 필수)
        sales_data = {
            'sale_amount': sale_amount_float,
            'sale_date': self._parse_date(sale_date),
            'customer_id': customer_id,  # 필수
            'employee_id': employee_id,  # 필수
            'product_id': product_id     # 필수
        }
        
        # 일반 매출 기록 생성 로그 제거 - 반복적
        return SalesRecord(**sales_data)
    
    async def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 매출 레코드 업데이트 (매출액과 사용예산만 업데이트)"""
        try:
            update_made = False
            update_details = []
            
            # 매출액 추출 및 업데이트
            sale_amount = None
            if 'sale_amount' in column_mapping:
                source_col = column_mapping['sale_amount']
                if source_col in row and row[source_col] is not None:
                    sale_amount = str(row[source_col]).strip()
            
            if sale_amount:
                try:
                    sale_amount_float = float(sale_amount.replace(',', '').replace('₩', '').strip())
                    existing_amount = float(existing_record.sale_amount)
                    
                    # 소수점 둘째자리까지 비교하여 실제 차이가 있을 때만 업데이트
                    if sale_amount_float > 0 and abs(sale_amount_float - existing_amount) > 0.01:
                        update_details.append(f"매출액: {existing_amount:,.0f} → {sale_amount_float:,.0f}")
                        logger.info(f"  📝 매출액 업데이트: {existing_amount:,.0f} → {sale_amount_float:,.0f} (레코드ID: {existing_record.record_id})")
                        existing_record.sale_amount = sale_amount_float
                        update_made = True
                except ValueError:
                    pass
            
            # product_id는 더 이상 업데이트하지 않음 (필수 필드이므로)
            
            # 업데이트 내용 요약
            if update_made and update_details:
                logger.info(f"  ✅ 일반 매출 업데이트 완료: {', '.join(update_details)}")
            
            # 업데이트 시각 기록
            if update_made:
                existing_record.updated_at = datetime.now()
            
        except Exception as e:
            logger.error(f"매출 레코드 업데이트 중 오류: {e}")
    
    async def process_batch(self, table_data: List[Dict[str, Any]], column_mapping: Dict[str, str],
                           document_id: Optional[int] = None, uploader_id: Optional[int] = None) -> Dict[str, Any]:
        """배치 처리 (오버라이드 - 총 레코드 수 표시)"""
        # 부모 클래스의 process_batch 호출
        result = await super().process_batch(table_data, column_mapping, document_id, uploader_id)
        
        # 총 생성/업데이트된 레코드 수 로그
        if self.total_records_created > 0 or self.total_records_updated > 0:
            logger.info(f"📊 sales_records 총 결과: {len(table_data)}행에서 {self.total_records_created}건 생성, {self.total_records_updated}건 업데이트")
        
        # 결과에 총 레코드 수 추가
        result['total_records_created'] = self.total_records_created
        result['total_records_updated'] = self.total_records_updated
        
        # 업데이트 카운트 반영
        if self.total_records_updated > 0:
            result['updated_count'] = self.total_records_updated
        
        return result
    
    async def _get_or_create_customer_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> int:
        """고객 ID를 가져오기 (기존 고객만 조회, 생성하지 않음)"""
        try:
            # 고객명 추출 - 실제 DB 컬럼명 사용
            customer_name = None
            if 'customer_name' in column_mapping and row.get(column_mapping['customer_name']):
                customer_name = str(row[column_mapping['customer_name']]).strip()
            
            # 디버깅 로그 제거 - 너무 상세하고 반복적
            
            if not customer_name or customer_name == 'nan' or customer_name == '':
                logger.error(f"고객명이 유효하지 않음: customer_name='{customer_name}', column_mapping={column_mapping}")
                raise ValueError("고객명이 필수입니다.")
            
            # 공통 유틸리티 사용
            return await get_customer_id(self.session, customer_name)
                
        except Exception as e:
            logger.error(f"고객 ID 조회 중 오류: {e}")
            raise ValueError(f"고객 ID 조회 실패: {str(e)}")
    
    async def _get_or_create_employee_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> int:
        """직원 ID를 가져오기 (기존 직원만 조회, 생성하지 않음)"""
        try:
            # 직원명 또는 사번 추출 - 실제 DB 컬럼명 사용
            employee_name = None
            employee_number = None
            
            # employee_info 테이블의 실제 컬럼명 사용
            if 'name' in column_mapping and row.get(column_mapping['name']):
                employee_name = str(row[column_mapping['name']]).strip()
            
            if 'employee_number' in column_mapping and row.get(column_mapping['employee_number']):
                employee_number = str(row[column_mapping['employee_number']]).strip()
            
            if not employee_name and not employee_number:
                raise ValueError("직원명(name) 또는 사번(employee_number)이 필수입니다.")
            
            # 공통 유틸리티 사용
            return await get_employee_id(self.session, employee_name, employee_number)
                
        except Exception as e:
            logger.error(f"직원 ID 조회 중 오류: {e}")
            raise ValueError(f"직원 ID 조회 실패: {str(e)}")
    
    async def _get_or_create_product_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """제품 ID를 가져오기 (products 테이블의 매핑 정보 활용)"""
        try:
            product_name = None
            
            # text2sql_classifier에서 전달받은 product_column 정보 확인
            if '_product_column' in column_mapping:
                product_column = column_mapping['_product_column']
                if product_column in row and row[product_column]:
                    product_name = str(row[product_column]).strip()
                    logger.debug(f"products 테이블 매핑 정보로 제품명 추출: {product_column} = {product_name}")
            
            if not product_name or product_name == 'nan':
                return None
            
            # 공통 유틸리티 사용하여 product_id 조회
            product_id = await get_product_id(self.session, product_name)
            if product_id:
                logger.debug(f"제품 ID 조회 성공: {product_name} → {product_id}")
            else:
                logger.debug(f"제품 ID 조회 실패 (제품이 등록되지 않음): {product_name}")
            
            return product_id
                
        except Exception as e:
            logger.error(f"제품 ID 조회 중 오류: {e}")
            return None
    
    def _extract_monthly_sales_data(self, row: Dict[str, Any], column_mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """월별 매출 데이터 추출"""
        monthly_sales = []
        
        for source_column, value in row.items():
            # YYYYMM 형식 컬럼 확인 (예: 202212, 202301)
            if re.match(r'^\d{6}$', str(source_column)) and value is not None:
                try:
                    # 숫자가 아닌 값은 건너뛰기
                    if not str(value).replace('.', '').replace(',', '').isdigit():
                        continue
                        
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
                        
                        # 개별 매출 추출 로그 제거 - 너무 많은 로그 생성
                except (ValueError, TypeError) as e:
                    logger.warning(f"월별 매출 데이터 파싱 실패: {source_column} = {value}, 오류: {e}")
                    continue
        
        logger.debug(f"총 {len(monthly_sales)}개의 월별 매출 데이터 추출됨")
        return monthly_sales
    
    async def _create_monthly_sales_records(self, row: Dict[str, Any], column_mapping: Dict[str, Any], monthly_sales: List[Dict[str, Any]]) -> List[SalesRecord]:
        """월별 매출 데이터를 개별 매출 기록으로 변환 (기존 레코드 확인 및 업데이트 포함)"""
        sales_records = []
        updated_count = 0
        created_count = 0
        skipped_count = 0
        
        if not monthly_sales:
            logger.warning("월별 매출 데이터가 없습니다.")
            return []
        
        try:
            # 외래키 해결 (한 번만)
            customer_id = await self._get_or_create_customer_id(row, column_mapping)
            employee_id = await self._get_or_create_employee_id(row, column_mapping)
            product_id = await self._get_or_create_product_id(row, column_mapping)
            
            # 제품 정보가 없으면 건너뛰기
            if not product_id:
                logger.warning(f"제품 정보가 없어 월별 매출 데이터를 건너뜁니다. (직원: {row.get(column_mapping.get('name'))}, 고객: {row.get(column_mapping.get('customer_name'))})")
                return []
            
            # 외래키 해결 완료 로그 제거 - 반복적
            
            for monthly_sale in monthly_sales:
                try:
                    sale_amount = monthly_sale['sale_amount']
                    parsed_date = self._parse_date(monthly_sale['sale_date'])
                    
                    # 매출이 0이거나 없으면 건너뛰기
                    if sale_amount <= 0:
                        logger.debug(f"월별 데이터 - 매출과 사용 예산이 모두 0, 건너뛰기: {monthly_sale['source_column']}")
                        continue
                    
                    # 기존 레코드 확인 (직원+고객+제품+날짜 조합)
                    existing_result = await self.session.execute(
                        select(SalesRecord).filter(
                            SalesRecord.employee_id == employee_id,
                            SalesRecord.customer_id == customer_id,
                            SalesRecord.product_id == product_id,
                            SalesRecord.sale_date == parsed_date
                        )
                    )
                    existing_record = existing_result.scalar_one_or_none()
                    
                    if existing_record:
                        # 기존 레코드 업데이트 (매출액과 사용예산만)
                        update_made = False
                        update_details = []
                        
                        # 매출액 업데이트 (새 값이 다르면 - 소수점 둘째자리까지 비교)
                        existing_amount = float(existing_record.sale_amount)
                        if sale_amount > 0 and abs(sale_amount - existing_amount) > 0.01:
                            update_details.append(f"매출액: {existing_amount:,.0f} → {sale_amount:,.0f}")
                            logger.info(f"  📝 매출액 업데이트: {existing_amount:,.0f} → {sale_amount:,.0f} (날짜: {parsed_date}, 제품: {product_id}, 고객: {customer_id})")
                            existing_record.sale_amount = sale_amount
                            update_made = True
                        
                        # 업데이트 내용 요약 로그
                        if update_made:
                            # 직원, 고객, 제품 정보 조회 (디버깅용)
                            from app.models.employee_info import EmployeeInfo
                            from app.models.customers import Customer
                            from app.models.products import Product
                            
                            emp_result = await self.session.execute(
                                select(EmployeeInfo).filter(EmployeeInfo.employee_info_id == employee_id)
                            )
                            emp = emp_result.scalar_one_or_none()
                            
                            cust_result = await self.session.execute(
                                select(Customer).filter(Customer.customer_id == customer_id)
                            )
                            cust = cust_result.scalar_one_or_none()
                            
                            prod_result = await self.session.execute(
                                select(Product).filter(Product.product_id == product_id)
                            )
                            prod = prod_result.scalar_one_or_none()
                            
                            logger.info(f"  ✅ 업데이트 완료: {emp.name if emp else 'Unknown'} | {cust.customer_name if cust else 'Unknown'} | {prod.product_name if prod else 'Unknown'} | {parsed_date} | {', '.join(update_details)}")
                        
                        if update_made:
                            updated_count += 1
                            self.total_records_updated += 1  # 전체 업데이트 카운트 증가
                    else:
                        # 새 레코드 생성 (product_id 필수)
                        sales_data = {
                            'sale_amount': sale_amount,
                            'sale_date': parsed_date,
                            'customer_id': customer_id,  # 필수
                            'employee_id': employee_id,  # 필수
                            'product_id': product_id     # 필수
                        }
                        
                        # 필수 필드 검증 (product_id 포함)
                        if sales_data.get('sale_date') and sales_data.get('sale_amount') and sales_data.get('customer_id') and sales_data.get('employee_id') and sales_data.get('product_id'):
                            record = SalesRecord(**sales_data)
                            sales_records.append(record)
                            self.total_records_created += 1  # 총 레코드 수 증가
                            created_count += 1
                            
                            # 개별 레코드 생성 로그 제거 - 반복적
                        else:
                            logger.warning(f"필수 필드 누락 - 건너뜀: {sales_data}")
                        
                except Exception as e:
                    logger.error(f"월별 매출 레코드 처리 실패: {monthly_sale}, 오류: {e}")
                    continue
            
            if created_count > 0 or updated_count > 0:
                logger.info(f"월별 매출 처리 완료: {created_count}개 생성, {updated_count}개 업데이트")
            
            return sales_records
            
        except Exception as e:
            logger.error(f"월별 매출 레코드 처리 중 전체 오류: {e}")
            return []
    
    def _parse_date(self, date_str: str):
        """날짜 문자열 파싱"""
        try:
            # 특수 형식 먼저 처리 (YYYYMM은 %Y%m%d보다 먼저 체크해야 함)
            if len(date_str) == 6 and date_str.isdigit():  # YYYYMM
                year = int(date_str[:4])
                month = int(date_str[4:6])
                if 1 <= month <= 12:
                    return datetime(year, month, 1).date()
            
            # 8자리 날짜 (YYYYMMDD)
            if len(date_str) == 8 and date_str.isdigit():
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return datetime(year, month, day).date()
            
            # 다양한 날짜 형식 처리 (%Y%m%d는 제외 - 위에서 처리)
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y-%m', '%Y/%m', '%Y.%m']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    # 월까지만 있는 경우 1일로 설정
                    if fmt in ['%Y-%m', '%Y/%m', '%Y.%m']:
                        return datetime(parsed_date.year, parsed_date.month, 1).date()
                    return parsed_date.date()
                except ValueError:
                    continue
            
            # 기타 특수 형식 처리
            if len(date_str) <= 2:  # 월만 있는 경우 (1, 01, 12 등)
                try:
                    month = int(date_str)
                    if 1 <= month <= 12:
                        # 현재 연도 사용
                        current_year = datetime.now().year
                        return datetime(current_year, month, 1).date()
                except ValueError:
                    pass
            elif '월' in date_str:  # '1월', '12월' 형식
                try:
                    month_str = date_str.replace('월', '').strip()
                    month = int(month_str)
                    if 1 <= month <= 12:
                        current_year = datetime.now().year
                        return datetime(current_year, month, 1).date()
                except ValueError:
                    pass
            
            raise ValueError(f"날짜 형식을 인식할 수 없음: {date_str}")
            
        except Exception as e:
            logger.error(f"날짜 파싱 실패: {date_str}, 오류: {e}")
            raise

class DocumentProcessor(BaseTableProcessor):
    """문서 정보 처리기"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.table_name = "documents"
    
    def get_table_name(self) -> str:
        return "documents"
    
    def get_unit_name(self) -> str:
        return "개"
    
    def get_unique_fields(self) -> List[str]:
        return ["document_id"]

class DocumentRelationProcessor(BaseTableProcessor):
    """문서 관계 정보 처리기"""
    
    def get_table_name(self) -> str:
        return "document_relations"
    
    def get_unit_name(self) -> str:
        return "개"
    
    def get_unique_fields(self) -> List[str]:
        return ["parent_document_id", "child_document_id"]

class InteractionLogProcessor(BaseTableProcessor):
    """상호작용 로그 처리기"""
    
    def get_table_name(self) -> str:
        return "interaction_logs"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["customer_id", "employee_id", "interaction_date"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """상호작용 로그는 중복 체크 없이 항상 새로 생성"""
        return None
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 상호작용 로그 생성"""
        # 필수 필드 추출
        customer_id = await self._get_customer_id(row, column_mapping)
        employee_id = await self._get_employee_id(row, column_mapping)
        interaction_date = self._parse_date(
            self.extract_required_field(row, column_mapping, "interaction_date", required=True)
        )
        
        if not customer_id or not employee_id or not interaction_date:
            raise ValueError(f"필수 필드 누락: customer_id={customer_id}, employee_id={employee_id}, interaction_date={interaction_date}")
        
        log_data = {
            'customer_id': customer_id,
            'employee_id': employee_id,
            'interaction_date': interaction_date
        }
        
        # 선택 필드들 매핑
        optional_fields = ['interaction_type', 'notes', 'sales_opportunity']
        for field in optional_fields:
            if field in column_mapping:
                value = row.get(column_mapping[field])
                if value:
                    log_data[field] = self.transform_field_value(field, value)
        
        return InteractionLog(**log_data)
    
    async def _get_customer_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """고객 ID 조회"""
        customer_name = self.extract_required_field(row, column_mapping, "customer_name", required=False)
        if not customer_name:
            return None
        return await get_customer_id(self.session, customer_name)
    
    async def _get_employee_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """직원 ID 조회"""
        employee_name = self.extract_required_field(row, column_mapping, "employee_name", required=False)
        employee_number = self.extract_required_field(row, column_mapping, "employee_number", required=False)
        if not employee_name and not employee_number:
            return None
        return await get_employee_id(self.session, employee_name, employee_number)
    
    def _parse_date(self, date_str: str):
        """날짜 문자열 파싱"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y/%m/%d').date()
            except ValueError:
                return None

class AssignmentMapProcessor(BaseTableProcessor):
    """담당자 배정 정보 처리기"""
    
    def get_table_name(self) -> str:
        return "assignment_map"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["employee_id", "customer_id"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """담당자 배정은 중복 체크"""
        employee_id = await self._get_employee_id(row, column_mapping)
        customer_id = await self._get_customer_id(row, column_mapping)
        
        if not employee_id or not customer_id:
            return None
        
        result = await self.session.execute(
            select(AssignmentMap).filter(
                AssignmentMap.employee_id == employee_id,
                AssignmentMap.customer_id == customer_id
            )
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 담당자 배정 생성"""
        try:
            # 직원 ID 조회 또는 생성
            employee_id = await self._get_employee_id(row, column_mapping)
            # 고객 ID 조회 또는 생성  
            customer_id = await self._get_customer_id(row, column_mapping)
            
            if not employee_id or not customer_id:
                raise ValueError(f"필수 ID 누락: employee_id={employee_id}, customer_id={customer_id}")
            
            assignment_data = {
                'employee_id': employee_id,
                'customer_id': customer_id
            }
            
            logger.info(f"담당자 배정 레코드 생성: {assignment_data}")
            return assignment_data
            
        except Exception as e:
            logger.error(f"담당자 배정 레코드 생성 중 오류: {e}")
            raise

class EmployeePerformanceProcessor(BaseTableProcessor):
    """직원 실적 목표 처리기"""
    
    def get_table_name(self) -> str:
        return "employee_performance"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["employee_id", "year_month"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """직원 ID와 년월로 기존 목표 조회"""
        from app.models.employee_performance import EmployeePerformance
        
        # 직원 ID 조회
        employee_id = await self._get_employee_id(row, column_mapping)
        if not employee_id:
            return None
        
        # 년월 추출
        year_month = self._extract_year_month(row, column_mapping)
        if not year_month:
            return None
        
        result = await self.session.execute(
            select(EmployeePerformance).filter(
                EmployeePerformance.employee_id == employee_id,
                EmployeePerformance.year_month == year_month
            )
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 목표 레코드 생성 (월별 컬럼 처리 포함)"""
        from app.models.employee_performance import EmployeePerformance
        
        # 월별 목표 데이터 추출 (YYYYMM 형식 컬럼들)
        monthly_targets = self._extract_monthly_targets(row)
        
        if monthly_targets:
            # 월별 목표가 있는 경우 개별 레코드 생성
            records = []
            employee_id = await self._get_employee_id(row, column_mapping)
            
            if not employee_id:
                raise ValueError("직원 정보를 찾을 수 없습니다")
            
            for month_data in monthly_targets:
                record = EmployeePerformance(
                    employee_id=employee_id,
                    year_month=month_data['year_month'],
                    target_amount=month_data['target_amount'],
                    notes=month_data.get('notes')
                )
                records.append(record)
                logger.info(f"목표 생성: 직원 {employee_id}, {month_data['year_month']}, 목표: {month_data['target_amount']:,.0f}")
            
            return records if records else None
        
        else:
            # 단일 목표 데이터 처리
            employee_id = await self._get_employee_id(row, column_mapping)
            year_month = self._extract_year_month(row, column_mapping)
            target_amount = self._extract_target_amount(row, column_mapping)
            
            if not employee_id or not year_month:
                raise ValueError(f"필수 필드 누락: employee_id={employee_id}, year_month={year_month}")
            
            return EmployeePerformance(
                employee_id=employee_id,
                year_month=year_month,
                target_amount=target_amount,
                notes=row.get(column_mapping.get('notes'))
            )
    
    async def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 목표 레코드 업데이트"""
        target_amount = self._extract_target_amount(row, column_mapping)
        if target_amount is not None:
            existing_record.target_amount = target_amount
        
        if 'notes' in column_mapping:
            notes = row.get(column_mapping['notes'])
            if notes:
                existing_record.notes = notes
    
    async def _get_employee_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """직원 ID 조회"""
        from app.services.utils.foreign_key_utils import get_employee_id
        
        employee_name = None
        employee_number = None
        
        # 직원명 또는 사번 추출
        if 'employee_name' in column_mapping:
            employee_name = str(row.get(column_mapping['employee_name'], '')).strip()
        if 'employee_number' in column_mapping:
            employee_number = str(row.get(column_mapping['employee_number'], '')).strip()
        
        # 컬럼명으로 직접 확인 (인코딩 문제 대응)
        columns = list(row.keys())
        
        # 두 번째 컬럼이 담당자일 가능성 (index 1)
        if not employee_name and len(columns) > 1:
            # '담당자' 또는 두 번째 컬럼
            for col in columns:
                if '담당' in col or '직원' in col or '성명' in col:
                    value = str(row.get(col, '')).strip()
                    if value and value not in ['', 'nan', 'None', '계', '합계', '총계']:
                        employee_name = value
                        break
            
            # 그래도 없으면 두 번째 컬럼 시도
            if not employee_name:
                value = str(row.get(columns[1], '')).strip()
                if value and value not in ['', 'nan', 'None', '계', '합계', '총계']:
                    employee_name = value
        
        # 세 번째 컬럼이 사번일 가능성 (index 2)
        if not employee_number and len(columns) > 2:
            # '사번' 또는 세 번째 컬럼
            for col in columns:
                if '사번' in col or '번호' in col:
                    value = str(row.get(col, '')).strip()
                    if value and value not in ['', 'nan', 'None']:
                        employee_number = value
                        break
            
            # 그래도 없으면 세 번째 컬럼 시도 (MR- 패턴 확인)
            if not employee_number:
                value = str(row.get(columns[2], '')).strip()
                if value and (value.startswith('MR-') or value.startswith('mr-') or 
                             value not in ['', 'nan', 'None']):
                    employee_number = value
        
        if not employee_name and not employee_number:
            logger.debug(f"직원 정보를 찾을 수 없음: {list(row.items())[:5]}")
            return None
        
        try:
            logger.debug(f"직원 조회: 이름={employee_name}, 사번={employee_number}")
            return await get_employee_id(self.session, employee_name, employee_number)
        except Exception as e:
            logger.warning(f"직원 ID 조회 실패 (이름: {employee_name}, 사번: {employee_number}): {e}")
            return None
    
    def _extract_year_month(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """년월 정보 추출"""
        from datetime import datetime
        
        # 매핑된 year_month 필드 확인
        if 'year_month' in column_mapping:
            value = row.get(column_mapping['year_month'])
            if value:
                try:
                    return datetime.strptime(str(value), '%Y-%m-%d').date()
                except:
                    try:
                        return datetime.strptime(str(value), '%Y%m').replace(day=1).date()
                    except:
                        pass
        
        # 월별 컬럼이 있는지 확인
        for col_name in row.keys():
            if re.match(r'^\d{6}$', str(col_name)):  # YYYYMM 형식
                year = int(str(col_name)[:4])
                month = int(str(col_name)[4:6])
                return datetime(year, month, 1).date()
        
        return None
    
    def _extract_target_amount(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> float:
        """목표 금액 추출"""
        if 'target_amount' in column_mapping:
            value = row.get(column_mapping['target_amount'])
            if value:
                try:
                    return float(str(value).replace(',', '').replace('₩', ''))
                except:
                    pass
        return 0.0
    
    def _extract_monthly_targets(self, row: Dict[str, Any]) -> List[Dict[str, Any]]:
        """월별 목표 데이터 추출 (YYYYMM 형식 컬럼들)"""
        from datetime import datetime
        monthly_targets = []
        
        for col_name, value in row.items():
            # YYYYMM_목표 형식 우선 처리
            if '_목표' in str(col_name):
                month_str = str(col_name).split('_')[0]
                if re.match(r'^\d{6}$', month_str):
                    try:
                        year = int(month_str[:4])
                        month = int(month_str[4:6])
                        
                        # 값 변환 처리
                        if value and str(value) not in ['', 'nan', 'None']:
                            # 문자열로 변환 후 숫자만 추출
                            value_str = str(value).replace(',', '').replace('₩', '').replace(' ', '')
                            if value_str.replace('.', '').replace('-', '').isdigit():
                                target_amount = float(value_str)
                                
                                if target_amount > 0:
                                    monthly_targets.append({
                                        'year_month': datetime(year, month, 1).date(),
                                        'target_amount': target_amount,
                                        'notes': f"{year}년 {month}월 목표"
                                    })
                                    logger.debug(f"목표 추출: {month_str} = {target_amount:,.0f}")
                    except Exception as e:
                        logger.debug(f"목표 추출 실패: {col_name} = {value}, 오류: {e}")
                        continue
        
        # 목표 컬럼이 없는 경우 로그
        if not monthly_targets:
            logger.debug(f"월별 목표 데이터를 찾을 수 없음. 컬럼: {list(row.keys())[:10]}")
        
        return monthly_targets
    
    async def process_batch(self, table_data: List[Dict[str, Any]], column_mapping: Dict[str, str],
                           document_id: Optional[int] = None, uploader_id: Optional[int] = None) -> Dict[str, Any]:
        """배치 처리 (월별 목표 데이터 특별 처리)"""
        try:
            total_created = 0
            total_updated = 0
            total_skipped = 0
            
            for row in table_data:
                # 계, 합계 등 집계 행 제외
                first_value = str(list(row.values())[0]) if row else ""
                if first_value in ['계', '합계', '총계', '']:
                    total_skipped += 1
                    continue
                
                # 월별 목표 데이터 처리
                records = await self.create_new_record(row, column_mapping)
                
                if isinstance(records, list):
                    # 여러 개의 월별 레코드
                    for record in records:
                        # 기존 레코드 확인
                        existing = await self.session.execute(
                            select(EmployeePerformance).filter(
                                EmployeePerformance.employee_id == record.employee_id,
                                EmployeePerformance.year_month == record.year_month
                            )
                        )
                        existing_record = existing.scalar_one_or_none()
                        
                        if existing_record:
                            # 업데이트
                            existing_record.target_amount = record.target_amount
                            if record.notes:
                                existing_record.notes = record.notes
                            total_updated += 1
                        else:
                            # 신규 생성
                            self.session.add(record)
                            total_created += 1
                
                elif records:
                    # 단일 레코드
                    existing = await self.find_existing_record(row, column_mapping)
                    if existing:
                        await self.update_existing_record(existing, row, column_mapping)
                        total_updated += 1
                    else:
                        self.session.add(records)
                        total_created += 1
            
            await self.session.flush()
            
            logger.info(f"✅ employee_performance 처리 완료: 생성 {total_created}건, 업데이트 {total_updated}건")
            
            return {
                'success': True,
                'processed_count': len(table_data),
                'created_count': total_created,
                'updated_count': total_updated,
                'skipped_count': total_skipped
            }
            
        except Exception as e:
            logger.error(f"employee_performance 배치 처리 중 오류: {e}")
            raise

class BranchProcessor(BaseTableProcessor):
    """지점 정보 처리기"""
    
    def get_table_name(self) -> str:
        return "branches"
    
    def get_unit_name(self) -> str:
        return "개"
    
    def get_unique_fields(self) -> List[str]:
        return ["branch_name"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """지점명으로 기존 지점 조회"""
        branch_name = self.extract_required_field(row, column_mapping, "branch_name", required=True)
        if not branch_name:
            return None
        
        from app.models.branches import Branch
        result = await self.session.execute(
            select(Branch).filter(Branch.branch_name == branch_name)
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 지점 레코드 생성"""
        branch_name = self.extract_required_field(row, column_mapping, "branch_name", required=True)
        headquarters = self.extract_required_field(row, column_mapping, "headquarters", required=True)
        department = self.extract_required_field(row, column_mapping, "department", required=True)
        
        if not branch_name or not headquarters or not department:
            raise ValueError(f"필수 필드 누락: branch_name={branch_name}, headquarters={headquarters}, department={department}")
        
        from app.models.branches import Branch
        branch_data = {
            'branch_name': branch_name,
            'headquarters': headquarters,
            'department': department
        }
        
        # 선택 필드들 매핑
        valid_fields = {
            'branch_name', 'headquarters', 'department', 
            'contact_number', 'status', 'notes'
        }
        
        for db_field, source_column in column_mapping.items():
            if db_field in valid_fields and source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    branch_data[db_field] = value
        
        return Branch(**branch_data)
    
    def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 지점 레코드 업데이트"""
        for db_field, source_column in column_mapping.items():
            if source_column in row and row[source_column] is not None:
                value = self.transform_field_value(db_field, row[source_column])
                if value is not None:
                    setattr(existing_record, db_field, value)

class CustomerMonthlyStatusProcessor(BaseTableProcessor):
    """거래처별 월간 상태 처리기 (환자수, 사용예산)"""
    
    def get_table_name(self) -> str:
        return "customer_monthly_status"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["customer_id", "year_month"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 월별 상태 레코드 조회"""
        customer_id = await self._get_customer_id(row, column_mapping)
        year_month = self._extract_year_month(row, column_mapping)
        
        if not customer_id or not year_month:
            return None
        
        result = await self.session.execute(
            select(CustomerMonthlyStatus).filter(
                CustomerMonthlyStatus.customer_id == customer_id,
                CustomerMonthlyStatus.year_month == year_month
            )
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 월별 상태 레코드 생성 (환자수, 사용예산)"""
        # 월별 데이터 추출 (YYYYMM 형식 컬럼들)
        monthly_data = self._extract_monthly_data(row)
        
        if monthly_data:
            # 월별 데이터가 있는 경우 개별 레코드 생성
            records = []
            customer_id = await self._get_customer_id(row, column_mapping)
            
            if not customer_id:
                raise ValueError("거래처 정보를 찾을 수 없습니다")
            
            for month_data in monthly_data:
                record = CustomerMonthlyStatus(
                    customer_id=customer_id,
                    year_month=month_data['year_month'],
                    patient_count=month_data.get('patient_count', 0),
                    used_budget=month_data.get('used_budget')
                )
                records.append(record)
                logger.info(f"월별 상태 생성: 거래처 {customer_id}, {month_data['year_month']}, 환자수: {month_data.get('patient_count', 0):,}, 예산: {month_data.get('used_budget', 0):,.0f}")
            
            return records if records else None
        
        else:
            # 단일 데이터 처리
            customer_id = await self._get_customer_id(row, column_mapping)
            year_month = self._extract_year_month(row, column_mapping)
            patient_count = self._extract_patient_count(row, column_mapping)
            used_budget = self._extract_used_budget(row, column_mapping)
            
            if not customer_id or not year_month:
                raise ValueError(f"필수 필드 누락: customer_id={customer_id}, year_month={year_month}")
            
            return CustomerMonthlyStatus(
                customer_id=customer_id,
                year_month=year_month,
                patient_count=patient_count,
                used_budget=used_budget
            )
    
    async def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 상태 레코드 업데이트"""
        patient_count = self._extract_patient_count(row, column_mapping)
        if patient_count is not None:
            existing_record.patient_count = patient_count
        
        used_budget = self._extract_used_budget(row, column_mapping)
        if used_budget is not None:
            existing_record.used_budget = used_budget
    
    async def _get_customer_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """거래처 ID 조회"""
        from app.services.utils.foreign_key_utils import get_customer_id
        
        customer_name = None
        
        # 거래처명 추출
        if 'customer_name' in column_mapping:
            customer_name = str(row.get(column_mapping['customer_name'], '')).strip()
        
        # 컬럼명으로 직접 확인
        if not customer_name:
            for col in row.keys():
                if any(keyword in str(col) for keyword in ['거래처', '고객', '병원', '약국', 'ID']):
                    value = str(row.get(col, '')).strip()
                    if value and value not in ['', 'nan', 'None', '계', '합계', '총계']:
                        customer_name = value
                        break
        
        if not customer_name:
            logger.debug(f"거래처 정보를 찾을 수 없음: {list(row.items())[:5]}")
            return None
        
        try:
            logger.debug(f"거래처 조회: 이름={customer_name}")
            return await get_customer_id(self.session, customer_name)
        except Exception as e:
            logger.warning(f"거래처 ID 조회 실패 (이름: {customer_name}): {e}")
            return None
    
    def _extract_year_month(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[str]:
        """년월 정보 추출 (YYYY-MM 형식으로 변환)"""
        from datetime import datetime
        
        # 매핑된 year_month 필드 확인
        if 'year_month' in column_mapping:
            value = row.get(column_mapping['year_month'])
            if value:
                value_str = str(value).strip()
                
                # YYYYMM 형식
                if re.match(r'^\d{6}$', value_str):
                    return f"{value_str[:4]}-{value_str[4:6]}"
                
                # YYYY-MM 형식
                elif re.match(r'^\d{4}-\d{2}$', value_str):
                    return value_str
                
                # YYYY/MM 형식
                elif re.match(r'^\d{4}/\d{2}$', value_str):
                    return value_str.replace('/', '-')
                
                # YYYY.MM 형식
                elif re.match(r'^\d{4}\.\d{2}$', value_str):
                    return value_str.replace('.', '-')
                
                # YYYY년 MM월 형식
                elif re.match(r'^\d{4}년\s*\d{1,2}월$', value_str):
                    year = re.search(r'(\d{4})년', value_str).group(1)
                    month = re.search(r'(\d{1,2})월', value_str).group(1).zfill(2)
                    return f"{year}-{month}"
                
                # MM월 형식 (현재 년도 사용)
                elif re.match(r'^\d{1,2}월$', value_str):
                    month = re.search(r'(\d{1,2})월', value_str).group(1).zfill(2)
                    current_year = datetime.now().year
                    return f"{current_year}-{month}"
                
                # 날짜 형식 (YYYY-MM-DD 등) - 년월만 추출
                try:
                    # 다양한 날짜 형식 시도
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y%m%d']:
                        try:
                            date_obj = datetime.strptime(value_str[:10] if len(value_str) >= 10 else value_str, fmt)
                            return f"{date_obj.year:04d}-{date_obj.month:02d}"
                        except:
                            continue
                except:
                    pass
        
        # 월별 컬럼이 있는지 확인 (YYYYMM 형식)
        for col_name in row.keys():
            col_str = str(col_name).strip()
            if re.match(r'^\d{6}$', col_str):  # YYYYMM 형식
                return f"{col_str[:4]}-{col_str[4:6]}"
        
        return None
    
    def _extract_patient_count(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> int:
        """환자수 추출"""
        if 'patient_count' in column_mapping:
            value = row.get(column_mapping['patient_count'])
            if value:
                try:
                    return int(float(str(value).replace(',', '').replace('명', '')))
                except:
                    pass
        return 0
    
    def _extract_used_budget(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[float]:
        """사용예산 추출"""
        if 'used_budget' in column_mapping:
            value = row.get(column_mapping['used_budget'])
            if value:
                try:
                    return float(str(value).replace(',', '').replace('₩', '').replace('원', ''))
                except:
                    pass
        return None
    
    def _extract_monthly_data(self, row: Dict[str, Any]) -> List[Dict[str, Any]]:
        """월별 상태 데이터 추출 (환자수, 사용예산)"""
        monthly_data = {}
        
        # 월별 컬럼 처리
        for col_name, value in row.items():
            col_str = str(col_name).strip()
            
            # YYYYMM_환자수 형식
            if '환자' in col_str or '방문' in col_str:
                month_match = re.search(r'(\d{6})', col_str)
                if month_match:
                    month_str = month_match.group(1)
                    year_month = f"{month_str[:4]}-{month_str[4:6]}"
                    
                    if year_month not in monthly_data:
                        monthly_data[year_month] = {}
                    
                    if value and str(value) not in ['', 'nan', 'None']:
                        try:
                            patient_count = int(float(str(value).replace(',', '').replace('명', '')))
                            monthly_data[year_month]['patient_count'] = patient_count
                        except:
                            pass
            
            # YYYYMM_예산 형식
            elif '예산' in col_str or '사용' in col_str:
                month_match = re.search(r'(\d{6})', col_str)
                if month_match:
                    month_str = month_match.group(1)
                    year_month = f"{month_str[:4]}-{month_str[4:6]}"
                    
                    if year_month not in monthly_data:
                        monthly_data[year_month] = {}
                    
                    if value and str(value) not in ['', 'nan', 'None']:
                        try:
                            used_budget = float(str(value).replace(',', '').replace('₩', '').replace('원', ''))
                            monthly_data[year_month]['used_budget'] = used_budget
                        except:
                            pass
        
        # 결과 리스트로 변환
        result = []
        for year_month, data in monthly_data.items():
            if data:  # 데이터가 있는 경우만
                result.append({
                    'year_month': year_month,
                    'patient_count': data.get('patient_count', 0),
                    'used_budget': data.get('used_budget')
                })
        
        return result
    
    def _extract_monthly_patients(self, row: Dict[str, Any]) -> List[Dict[str, Any]]:
        """월별 환자수 데이터 추출 (YYYYMM 형식 컬럼들) - 하위 호환성용"""
        monthly_patients = []
        
        for col_name, value in row.items():
            col_str = str(col_name).strip()
            
            # YYYYMM_환자수 형식 처리
            if '환자' in col_str or '방문' in col_str:
                # 컬럼명에서 월 정보 추출
                month_match = re.search(r'(\d{6})', col_str)
                if month_match:
                    month_str = month_match.group(1)
                    year_month = f"{month_str[:4]}-{month_str[4:6]}"
                    
                    if value and str(value) not in ['', 'nan', 'None']:
                        try:
                            patient_count = int(float(str(value).replace(',', '').replace('명', '')))
                            if patient_count > 0:
                                monthly_patients.append({
                                    'year_month': year_month,
                                    'patient_count': patient_count
                                })
                                logger.debug(f"환자수 추출: {year_month} = {patient_count:,}명")
                        except Exception as e:
                            logger.debug(f"환자수 추출 실패: {col_name} = {value}, 오류: {e}")
            
            # YYYYMM 형식의 컬럼명 자체가 환자수를 나타내는 경우
            elif re.match(r'^\d{6}$', col_str):
                year_month = f"{col_str[:4]}-{col_str[4:6]}"
                if value and str(value) not in ['', 'nan', 'None']:
                    try:
                        # 값이 환자수인지 확인 (매출과 구분)
                        value_float = float(str(value).replace(',', ''))
                        # 환자수는 보통 10000 미만
                        if value_float < 10000:
                            patient_count = int(value_float)
                            if patient_count > 0:
                                monthly_patients.append({
                                    'year_month': year_month,
                                    'patient_count': patient_count
                                })
                                logger.debug(f"환자수 추출: {year_month} = {patient_count:,}명")
                    except Exception as e:
                        logger.debug(f"환자수 추출 실패: {col_name} = {value}, 오류: {e}")
        
        return monthly_patients

# 처리기 팩토리
def get_table_processor(table_name: str, session: AsyncSession) -> BaseTableProcessor:
    """테이블 이름에 따른 적절한 처리기 반환"""
    processors = {
        'employee_info': EmployeeProcessor,
        'customers': CustomerProcessor,
        'products': ProductProcessor,
        'sales_records': SalesRecordProcessor,
        'documents': DocumentProcessor,
        'document_relations': DocumentRelationProcessor,
        'interaction_logs': InteractionLogProcessor,
        'assignment_map': AssignmentMapProcessor,
        'branches': BranchProcessor,
        'employee_performance': EmployeePerformanceProcessor,  # 직원 실적 목표 처리기
        'customer_monthly_status': CustomerMonthlyStatusProcessor,  # 거래처별 월간 상태 처리기
    }
    
    processor_class = processors.get(table_name)
    if not processor_class:
        raise ValueError(f"지원하지 않는 테이블: {table_name}")
    
    return processor_class(session)