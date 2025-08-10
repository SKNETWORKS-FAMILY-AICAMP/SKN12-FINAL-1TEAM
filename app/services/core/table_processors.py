"""
구체적인 테이블 처리기들
"""

import logging
import pandas as pd
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.employee_info import EmployeeInfo
from app.models.customers import Customer
from app.models.products import Product
from app.models.sales_records import SalesRecord

from .base_table_processor import BaseTableProcessor
from app.models.documents import Document
from app.models.document_relations import DocumentRelation
from app.models.interaction_logs import InteractionLog
from app.models.assignment_map import AssignmentMap
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
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, Any]):
        """새 매출 기록 생성 (외래키 해결 포함)"""
        # 상세 row 데이터 로그 제거 - 너무 길고 반복적
        
        # 월별 매출 데이터 처리
        monthly_sales = self._extract_monthly_sales_data(row, column_mapping)
        if monthly_sales:
            logger.info(f"월별 매출 데이터 발견: {len(monthly_sales)}개")
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
        
        # 일반 매출 기록 생성 로그 제거 - 반복적
        return SalesRecord(**sales_data)
    
    def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """매출 기록은 업데이트하지 않음 (항상 새로 생성)"""
        pass
    
    async def _get_or_create_customer_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> int:
        """고객 ID를 가져오기 (기존 고객만 조회, 생성하지 않음)"""
        try:
            # 고객명 추출
            customer_name = None
            if 'customer_name' in column_mapping and row.get(column_mapping['customer_name']):
                customer_name = str(row[column_mapping['customer_name']]).strip()
            
            # 디버깅 로그 제거 - 너무 상세하고 반복적
            
            if not customer_name or customer_name == 'nan' or customer_name == '':
                logger.error(f"고객명이 유효하지 않음: customer_name='{customer_name}', row={row}, column_mapping={column_mapping}")
                raise ValueError("고객명이 필수입니다.")
            
            # 공통 유틸리티 사용
            return await get_customer_id(self.session, customer_name)
                
        except Exception as e:
            logger.error(f"고객 ID 조회 중 오류: {e}")
            raise ValueError(f"고객 ID 조회 실패: {str(e)}")
    
    async def _get_or_create_employee_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> int:
        """직원 ID를 가져오기 (기존 직원만 조회, 생성하지 않음)"""
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
            
            # 공통 유틸리티 사용
            return await get_employee_id(self.session, employee_name, employee_number)
                
        except Exception as e:
            logger.error(f"직원 ID 조회 중 오류: {e}")
            raise ValueError(f"직원 ID 조회 실패: {str(e)}")
    
    async def _get_or_create_product_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """제품 ID를 가져오기 (기존 제품만 조회, 생성하지 않음)"""
        try:
            # 제품명 추출
            product_name = None
            if 'product_name' in column_mapping and row.get(column_mapping['product_name']):
                product_name = str(row[column_mapping['product_name']]).strip()
            
            if not product_name or product_name == 'nan':
                return None
            
            # 공통 유틸리티 사용
            return await get_product_id(self.session, product_name)
                
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
        
        logger.info(f"총 {len(monthly_sales)}개의 월별 매출 데이터 추출됨")
        return monthly_sales
    
    async def _create_monthly_sales_records(self, row: Dict[str, Any], column_mapping: Dict[str, Any], monthly_sales: List[Dict[str, Any]]) -> List[SalesRecord]:
        """월별 매출 데이터를 개별 매출 기록으로 변환"""
        sales_records = []
        
        if not monthly_sales:
            logger.warning("월별 매출 데이터가 없습니다.")
            return []
        
        try:
            # 외래키 해결 (한 번만)
            customer_id = await self._get_or_create_customer_id(row, column_mapping)
            employee_id = await self._get_or_create_employee_id(row, column_mapping)
            product_id = await self._get_or_create_product_id(row, column_mapping)
            
            # 외래키 해결 완료 로그 제거 - 반복적
            
            for monthly_sale in monthly_sales:
                try:
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
                    
                    # 필수 필드 검증
                    if sales_data.get('sale_date') and sales_data.get('sale_amount') and sales_data.get('customer_id') and sales_data.get('employee_id'):
                        sales_record = SalesRecord(**sales_data)
                        sales_records.append(sales_record)
                        # 개별 매출 기록 생성 로그 제거 - 너무 많은 로그 생성
                    else:
                        logger.warning(f"필수 필드 누락으로 매출 기록 생성 실패: {sales_data}")
                        
                except Exception as e:
                    logger.error(f"개별 매출 기록 생성 실패: {monthly_sale}, 오류: {e}")
                    continue
            
            logger.info(f"총 {len(sales_records)}개의 매출 기록 생성 완료")
            return sales_records
            
        except Exception as e:
            logger.error(f"월별 매출 기록 생성 중 오류: {e}")
            return []
    
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

class DocumentProcessor(BaseTableProcessor):
    """문서 정보 처리 클래스"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.table_name = "documents"
    
    def get_table_name(self) -> str:
        return "documents"
    
    def get_unit_name(self) -> str:
        return "개"
    
    def get_unique_fields(self) -> List[str]:
        return ["document_title"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """문서명으로 기존 문서 조회"""
        document_title = self.extract_required_field(row, column_mapping, "document_title", required=True)
        if not document_title:
            return None
        
        result = await self.session.execute(
            select(Document).filter(Document.document_title == document_title)
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새로운 문서 레코드 생성"""
        try:
            # 유효한 필드들 정의
            valid_fields = [
                'document_title', 'document_type', 'file_path', 'file_size',
                'upload_date', 'uploader_id', 'status', 'notes'
            ]
            
            # column_mapping을 사용하여 데이터 추출
            document_data = {}
            for field in valid_fields:
                if field in column_mapping and column_mapping[field] in row:
                    value = row[column_mapping[field]]
                    if pd.notna(value) and value != '':
                        document_data[field] = value
            
            # 필수 필드 검증
            if 'document_title' not in document_data:
                document_data['document_title'] = f"Document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if 'document_type' not in document_data:
                document_data['document_type'] = 'unknown'
            
            if 'upload_date' not in document_data:
                document_data['upload_date'] = datetime.now()
            
            logger.info(f"문서 레코드 생성: {document_data}")
            return document_data
            
        except Exception as e:
            logger.error(f"문서 레코드 생성 중 오류: {e}")
            raise


class DocumentRelationProcessor(BaseTableProcessor):
    """문서 관계 처리 클래스"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.table_name = "document_relations"
    
    def get_table_name(self) -> str:
        return "document_relations"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["source_document_id", "target_document_id"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """문서 관계 조회"""
        source_document_id = self.extract_required_field(row, column_mapping, "source_document_id", required=True)
        target_document_id = self.extract_required_field(row, column_mapping, "target_document_id", required=True)
        
        if not source_document_id or not target_document_id:
            return None
        
        result = await self.session.execute(
            select(DocumentRelation).filter(
                DocumentRelation.source_document_id == source_document_id,
                DocumentRelation.target_document_id == target_document_id
            )
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """새로운 문서 관계 레코드 생성"""
        try:
            # 유효한 필드들 정의
            valid_fields = [
                'source_document_id', 'target_document_id', 'relation_type',
                'relation_description', 'created_date'
            ]
            
            # column_mapping을 사용하여 데이터 추출
            relation_data = {}
            for field in valid_fields:
                if field in column_mapping and column_mapping[field] in row:
                    value = row[column_mapping[field]]
                    if pd.notna(value) and value != '':
                        relation_data[field] = value
            
            # 필수 필드 검증
            if 'relation_type' not in relation_data:
                relation_data['relation_type'] = 'related'
            
            if 'created_date' not in relation_data:
                relation_data['created_date'] = datetime.now()
            
            logger.info(f"문서 관계 레코드 생성: {relation_data}")
            return relation_data
            
        except Exception as e:
            logger.error(f"문서 관계 레코드 생성 중 오류: {e}")
            raise


class InteractionLogProcessor(BaseTableProcessor):
    """상호작용 로그 처리 클래스"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.table_name = "interaction_logs"
    
    def get_table_name(self) -> str:
        return "interaction_logs"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["customer_id", "employee_id", "interaction_date"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """상호작용 로그 조회"""
        customer_id = self.extract_required_field(row, column_mapping, "customer_id", required=True)
        employee_id = self.extract_required_field(row, column_mapping, "employee_id", required=True)
        interaction_date = self.extract_required_field(row, column_mapping, "interaction_date", required=True)
        
        if not customer_id or not employee_id or not interaction_date:
            return None
        
        result = await self.session.execute(
            select(InteractionLog).filter(
                InteractionLog.customer_id == customer_id,
                InteractionLog.employee_id == employee_id,
                InteractionLog.interaction_date == interaction_date
            )
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """새로운 상호작용 로그 레코드 생성"""
        try:
            # 유효한 필드들 정의
            valid_fields = [
                'customer_id', 'employee_id', 'interaction_type', 'interaction_date',
                'interaction_notes', 'follow_up_required', 'follow_up_date'
            ]
            
            # column_mapping을 사용하여 데이터 추출
            interaction_data = {}
            for field in valid_fields:
                if field in column_mapping and column_mapping[field] in row:
                    value = row[column_mapping[field]]
                    if pd.notna(value) and value != '':
                        interaction_data[field] = value
            
            # 필수 필드 검증
            if 'interaction_type' not in interaction_data:
                interaction_data['interaction_type'] = 'general'
            
            if 'interaction_date' not in interaction_data:
                interaction_data['interaction_date'] = datetime.now()
            
            logger.info(f"상호작용 로그 레코드 생성: {interaction_data}")
            return interaction_data
            
        except Exception as e:
            logger.error(f"상호작용 로그 레코드 생성 중 오류: {e}")
            raise


class AssignmentMapProcessor(BaseTableProcessor):
    """담당자 배정 처리 클래스"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.table_name = "assignment_map"
    
    def get_table_name(self) -> str:
        return "assignment_map"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["employee_id", "customer_id"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """담당자 배정 조회"""
        employee_id = self.extract_required_field(row, column_mapping, "employee_id", required=True)
        customer_id = self.extract_required_field(row, column_mapping, "customer_id", required=True)
        
        if not employee_id or not customer_id:
            return None
        
        result = await self.session.execute(
            select(AssignmentMap).filter(
                AssignmentMap.employee_id == employee_id,
                AssignmentMap.customer_id == customer_id
            )
        )
        return result.scalar_one_or_none()
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """새로운 담당자 배정 레코드 생성"""
        try:
            # 유효한 필드들 정의
            valid_fields = [
                'employee_id', 'customer_id', 'assignment_date', 'assignment_type',
                'assignment_notes', 'is_active'
            ]
            
            # column_mapping을 사용하여 데이터 추출
            assignment_data = {}
            for field in valid_fields:
                if field in column_mapping and column_mapping[field] in row:
                    value = row[column_mapping[field]]
                    if pd.notna(value) and value != '':
                        assignment_data[field] = value
            
            # 필수 필드 검증
            if 'assignment_date' not in assignment_data:
                assignment_data['assignment_date'] = datetime.now()
            
            if 'assignment_type' not in assignment_data:
                assignment_data['assignment_type'] = 'primary'
            
            if 'is_active' not in assignment_data:
                assignment_data['is_active'] = True
            
            logger.info(f"담당자 배정 레코드 생성: {assignment_data}")
            return assignment_data
            
        except Exception as e:
            logger.error(f"담당자 배정 레코드 생성 중 오류: {e}")
            raise

class BranchTargetProcessor(BaseTableProcessor):
    """지점별 목표 및 실적 처리기"""
    
    def get_table_name(self) -> str:
        return "branch_targets"
    
    def get_unit_name(self) -> str:
        return "건"
    
    def get_unique_fields(self) -> List[str]:
        return ["branch_id", "employee_info_id", "target_year", "target_month"]
    
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """지점, 직원, 년월로 기존 목표 조회"""
        # branch_targets는 중복 체크 없이 항상 새로 생성
        return None
    
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, Any]):
        """지점별 목표 레코드 생성 (월별 데이터 처리)"""
        logger.info(f"지점 목표 데이터 처리 시작")
        
        # 월별 목표/실적 데이터 추출
        monthly_targets = self._extract_monthly_target_data(row, column_mapping)
        if not monthly_targets:
            logger.warning("월별 목표 데이터가 없습니다")
            return []
        
        # 지점 ID 조회 또는 생성
        branch_id = await self._get_or_create_branch_id(row, column_mapping)
        # 직원 ID 조회 또는 생성  
        employee_info_id = await self._get_or_create_employee_info_id(row, column_mapping)
        
        if not branch_id or not employee_info_id:
            logger.error(f"지점 또는 직원 정보를 찾을 수 없음: branch_id={branch_id}, employee_info_id={employee_info_id}")
            return []
        
        # 월별 목표 레코드 생성
        from app.models.branch_targets import BranchTarget
        target_records = []
        
        for monthly_data in monthly_targets:
            try:
                # 달성률 계산
                achievement_rate = 0.0
                if monthly_data['target_amount'] and monthly_data['target_amount'] > 0:
                    achievement_rate = (monthly_data['actual_amount'] / monthly_data['target_amount']) * 100
                
                target_data = {
                    'branch_id': branch_id,
                    'employee_info_id': employee_info_id,
                    'target_year': monthly_data['year'],
                    'target_month': monthly_data['month'],
                    'target_date': monthly_data['target_date'],
                    'target_amount': monthly_data['target_amount'],
                    'actual_amount': monthly_data['actual_amount'],
                    'achievement_rate': achievement_rate
                }
                
                target_record = BranchTarget(**target_data)
                target_records.append(target_record)
                logger.info(f"목표 레코드 생성: {monthly_data['year']}-{monthly_data['month']:02d} (목표: {monthly_data['target_amount']}, 실적: {monthly_data['actual_amount']})")
                
            except Exception as e:
                logger.error(f"개별 목표 레코드 생성 실패: {monthly_data}, 오류: {e}")
                continue
        
        return target_records if target_records else None
    
    def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """목표 기록은 업데이트하지 않음"""
        pass
    
    def _extract_monthly_target_data(self, row: Dict[str, Any], column_mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """월별 목표/실적 데이터 추출"""
        monthly_targets = []
        
        for column_name, value in row.items():
            # YYYYMM 형식의 컬럼 확인
            if re.match(r'^\d{6}$', str(column_name)):
                try:
                    year = int(str(column_name)[:4])
                    month = int(str(column_name)[4:6])
                    
                    # 해당 월의 목표, 실적, 달성률 컬럼 찾기
                    target_col = f"{column_name}_목표"
                    actual_col = f"{column_name}_실적"
                    
                    # 실제 데이터 구조에 맞게 수정 필요
                    # 예: "202312" 컬럼 다음에 "목표", "실적", "달성률" 순서로 나온다면
                    target_amount = 0.0
                    actual_amount = 0.0
                    
                    # 컬럼 인덱스 기반으로 목표/실적 추출 (실제 구조에 맞게 조정 필요)
                    columns = list(row.keys())
                    col_idx = columns.index(column_name)
                    
                    # 목표 값 추출 (다음 컬럼)
                    if col_idx + 1 < len(columns):
                        target_val = row[columns[col_idx + 1]]
                        if target_val and str(target_val).replace(',', '').replace('.', '').isdigit():
                            target_amount = float(str(target_val).replace(',', ''))
                    
                    # 실적 값 추출 (다다음 컬럼)
                    if col_idx + 2 < len(columns):
                        actual_val = row[columns[col_idx + 2]]
                        if actual_val and str(actual_val).replace(',', '').replace('.', '').isdigit():
                            actual_amount = float(str(actual_val).replace(',', ''))
                    
                    if target_amount > 0 or actual_amount > 0:
                        from datetime import datetime
                        target_date = datetime(year, month, 1)
                        
                        monthly_targets.append({
                            'year': year,
                            'month': month,
                            'target_date': target_date,
                            'target_amount': target_amount,
                            'actual_amount': actual_amount
                        })
                        
                except Exception as e:
                    logger.warning(f"월별 목표 데이터 파싱 실패: {column_name}, 오류: {e}")
                    continue
        
        return monthly_targets
    
    async def _get_or_create_branch_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """지점 ID 조회 또는 생성"""
        try:
            branch_name = None
            if 'branch_name' in column_mapping and row.get(column_mapping['branch_name']):
                branch_name = str(row[column_mapping['branch_name']]).strip()
            elif '지점' in column_mapping and row.get(column_mapping['지점']):
                branch_name = str(row[column_mapping['지점']]).strip()
            
            if not branch_name or branch_name == 'nan':
                return None
            
            from app.models.branches import Branch
            result = await self.session.execute(
                select(Branch).filter(Branch.branch_name == branch_name)
            )
            branch = result.scalar_one_or_none()
            
            if branch:
                return branch.branch_id
            else:
                # 지점이 없으면 생성
                new_branch = Branch(
                    branch_name=branch_name,
                    headquarters="미지정",  # 기본값
                    department="미지정"      # 기본값
                )
                self.session.add(new_branch)
                await self.session.flush()
                return new_branch.branch_id
                
        except Exception as e:
            logger.error(f"지점 ID 조회 중 오류: {e}")
            return None
    
    async def _get_or_create_employee_info_id(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """직원 정보 ID 조회 또는 생성"""
        try:
            employee_name = None
            if 'employee_name' in column_mapping and row.get(column_mapping['employee_name']):
                employee_name = str(row[column_mapping['employee_name']]).strip()
            elif '담당자' in column_mapping and row.get(column_mapping['담당자']):
                employee_name = str(row[column_mapping['담당자']]).strip()
            
            if not employee_name or employee_name == 'nan':
                return None
            
            from app.models.employee_info import EmployeeInfo
            result = await self.session.execute(
                select(EmployeeInfo).filter(EmployeeInfo.name == employee_name)
            )
            employee = result.scalar_one_or_none()
            
            if employee:
                return employee.employee_info_id
            else:
                # 직원이 없으면 생성
                new_employee = EmployeeInfo(
                    name=employee_name,
                    employee_number=f"AUTO_{employee_name}"  # 자동 생성 사번
                )
                self.session.add(new_employee)
                await self.session.flush()
                return new_employee.employee_info_id
                
        except Exception as e:
            logger.error(f"직원 ID 조회 중 오류: {e}")
            return None

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
        'branches': BranchProcessor,  # 지점 처리기 추가
        'branch_targets': BranchTargetProcessor,  # 지점 목표 처리기 추가
    }
    
    processor_class = processors.get(table_name)
    if not processor_class:
        raise ValueError(f"지원하지 않는 테이블: {table_name}")
    
    return processor_class(session)