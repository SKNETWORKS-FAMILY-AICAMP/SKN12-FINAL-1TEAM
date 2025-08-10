"""
기본 테이블 처리기 - 모든 테이블 처리기의 공통 기능 제공
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class BaseTableProcessor(ABC):
    """모든 테이블 처리기의 기본 클래스"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.processed_count = 0  # 처리된 행 수
        self.created_count = 0    # 생성된 레코드 수 (월별 데이터의 경우 여러 개)
        self.updated_count = 0
        self.skipped_count = 0
    
    @abstractmethod
    def get_table_name(self) -> str:
        """테이블 이름 반환"""
        pass
    
    def get_unit_name(self) -> str:
        """테이블별 단위명 반환 (명, 개, 건 등)"""
        pass
    
    @abstractmethod
    def get_unique_fields(self) -> List[str]:
        """유니크 키로 사용할 필드들 반환"""
        pass
    
    @abstractmethod
    async def find_existing_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 레코드 조회"""
        pass
    
    @abstractmethod
    async def create_new_record(self, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """새 레코드 생성"""
        pass
    
    @abstractmethod
    def update_existing_record(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """기존 레코드 업데이트"""
        pass
    
    def extract_required_field(self, row: Dict[str, Any], column_mapping: Dict[str, str], 
                              field_name: str, required: bool = True) -> Optional[str]:
        """필수 필드 추출 및 검증"""
        if field_name not in column_mapping:
            if required:
                logger.warning(f"❌ {field_name} 매핑이 없음")
                return None
            return None
        
        source_column = column_mapping[field_name]
        if source_column not in row or not row[source_column]:
            if required:
                logger.warning(f"❌ {field_name} 값이 없음: 컬럼={source_column}")
                return None
            return None
        
        value = str(row[source_column]).strip()
        if not value or value == 'nan':
            if required:
                logger.warning(f"❌ {field_name} 값이 유효하지 않음: '{value}'")
                return None
            return None
        
        logger.debug(f"✅ {field_name} 추출 성공: {value}")
        return value
    
    def transform_field_value(self, field_name: str, raw_value: Any) -> Any:
        """필드별 데이터 변환"""
        if raw_value is None:
            return None
        
        value = str(raw_value).strip()
        
        # 숫자 필드 변환
        if field_name in ['base_salary', 'incentive_pay', 'avg_monthly_budget', 'total_patients']:
            try:
                return int(value.replace(',', '').replace('₩', '').strip())
            except:
                return None
        
        # 불린 필드 변환
        if field_name in ['is_active', 'is_auto_created']:
            return value.lower() in ['true', '1', 'yes', 'active', '활성', 'y']
        
        # 기본적으로 문자열 반환
        return value
    
    def is_valid_data_row(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> bool:
        """데이터 행이 유효한지 검증"""
        # 요약 행 제외
        summary_keywords = ['총합계', '합계', '소계', 'total', 'sum', '합']
        
        for source_column in row.values():
            if source_column and str(source_column).strip():
                value = str(source_column).strip().lower()
                if any(keyword in value for keyword in summary_keywords):
                    return False
        
        # 숫자만으로 구성된 값 제외 (고객명, 제품명 등)
        name_fields = ['customer_name', 'product_name', 'name']
        for db_field, source_column in column_mapping.items():
            if db_field in name_fields and source_column in row and row[source_column]:
                value = str(row[source_column]).strip()
                # 숫자만으로 구성된 경우 제외
                if value.isdigit():
                    return False
                # 숫자로 시작하는 경우도 제외 (예: "12345병원")
                if value and value[0].isdigit():
                    return False
        
        return True
    
    def compare_field_values(self, existing_value: Any, new_value: Any) -> bool:
        """두 필드 값 비교"""
        # 문자열 정규화
        if isinstance(existing_value, str):
            existing_value = existing_value.strip()
        if isinstance(new_value, str):
            new_value = new_value.strip()
        
        return existing_value != new_value
    
    def compare_records(self, existing_record, row: Dict[str, Any], column_mapping: Dict[str, str]) -> bool:
        """기존 레코드와 입력 데이터 비교"""
        for db_field, source_column in column_mapping.items():
            if source_column in row and row[source_column] is not None:
                # 새 값 변환
                raw_new_value = row[source_column]
                new_value = self.transform_field_value(db_field, raw_new_value)
                
                # 기존 값 가져오기
                existing_value = getattr(existing_record, db_field, None)
                
                # 값 비교
                if self.compare_field_values(existing_value, new_value):
                    logger.debug(f"변경사항 발견 - {self.get_table_name()}.{db_field}: '{existing_value}' → '{new_value}'")
                    return True
        
        return False
    
    def log_operation(self, operation: str, record_key: str, details: str = ""):
        """작업 로깅"""
        table_name = self.get_table_name()
        if operation == "created":
            logger.info(f"🆕 {table_name} 생성: {record_key} {details}")
        elif operation == "updated":
            logger.info(f"📝 {table_name} 업데이트: {record_key} - 변경사항 발견 {details}")
        elif operation == "skipped":
            logger.info(f"🔄 {table_name} 건너뜀: {record_key} - 기존 데이터와 동일 {details}")
        elif operation == "error":
            logger.warning(f"❌ {table_name} 오류: {record_key} {details}")
    
    def increment_counter(self, operation: str, record_count: int = 1):
        """카운터 증가"""
        if operation == "created":
            self.created_count += record_count  # 실제 생성된 레코드 수
        elif operation == "updated":
            self.updated_count += record_count
        elif operation == "skipped":
            self.skipped_count += record_count
        self.processed_count += 1  # 행 수는 항상 1씩 증가
    
    async def process_single_record(self, row: Dict[str, Any], column_mapping: Dict[str, str], 
                                   document_id: Optional[int] = None, uploader_id: Optional[int] = None) -> str:
        """단일 레코드 처리"""
        try:
            # 0. 데이터 유효성 검증
            if not self.is_valid_data_row(row, column_mapping):
                self.increment_counter("skipped")
                return "skipped"
            
            # 1. 기존 레코드 조회
            existing_record = await self.find_existing_record(row, column_mapping)
            
            # 2. 레코드 키 생성 (로깅용)
            unique_fields = self.get_unique_fields()
            record_key_parts = []
            for field in unique_fields:
                value = self.extract_required_field(row, column_mapping, field, required=False)
                if value:
                    record_key_parts.append(f"{field}={value}")
            record_key = ", ".join(record_key_parts)
            
            if existing_record:
                # 3-A. 기존 레코드와 비교
                has_changes = self.compare_records(existing_record, row, column_mapping)
                
                if has_changes:
                    # 업데이트
                    self.update_existing_record(existing_record, row, column_mapping)
                    self.increment_counter("updated")
                    return "updated"
                else:
                    # 건너뛰기
                    self.increment_counter("skipped")
                    return "skipped"
            else:
                # 3-B. 새 레코드 생성
                new_records = await self.create_new_record(row, column_mapping)
                
                # 월별 매출 데이터의 경우 여러 레코드가 반환될 수 있음
                if isinstance(new_records, list):
                    for record in new_records:
                        record.is_auto_created = True
                        record.approval_status = 'pending'
                        self.session.add(record)
                    await self.session.flush()
                    self.increment_counter("created", len(new_records))  # 실제 생성된 레코드 수
                    return "created"
                else:
                    # 단일 레코드인 경우
                    new_records.is_auto_created = True
                    new_records.approval_status = 'pending'
                    self.session.add(new_records)
                    await self.session.flush()  # ID 생성
                    
                    self.increment_counter("created", 1)  # 단일 레코드
                    return "created"
                
        except Exception as e:
            logger.error(f"레코드 처리 중 오류: {e}")
            return "error"
    
    async def process_batch(self, table_data: List[Dict[str, Any]], column_mapping: Dict[str, str],
                           document_id: Optional[int] = None, uploader_id: Optional[int] = None) -> Dict[str, Any]:
        """배치 처리"""
        table_name = self.get_table_name()
        
        try:
            for row in table_data:
                await self.process_single_record(row, column_mapping, document_id, uploader_id)
            
            return {
                'success': True,
                'message': f'{table_name} 처리 완료: {self.processed_count}행 처리됨, {self.created_count}{self.get_unit_name()} 생성, {self.updated_count}{self.get_unit_name()} 업데이트, {self.skipped_count}{self.get_unit_name()} 건너뜀',
                'processed_count': self.processed_count,
                'created_count': self.created_count,
                'updated_count': self.updated_count,
                'skipped_count': self.skipped_count
            }
            
        except Exception as e:
            logger.error(f"{table_name} 배치 처리 중 오류: {e}")
            return {
                'success': False,
                'message': f'{table_name} 처리 중 오류: {str(e)}',
                'processed_count': self.processed_count,
                'created_count': self.created_count,
                'updated_count': self.updated_count,
                'skipped_count': self.skipped_count
            }