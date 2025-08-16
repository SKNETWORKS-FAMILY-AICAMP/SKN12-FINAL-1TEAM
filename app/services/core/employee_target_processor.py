"""
직원 월간 목표 데이터 전용 처리기
LLM을 활용하여 컬럼을 분석하고 자동 매핑
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

# 공통 OpenAI 서비스 import
from app.services.external.openai_service import openai_service
from app.services.core.mv_refresh_service import mv_refresh_service
from app.services.utils.foreign_key_utils import get_employee_id
from app.models.employee_performance import EmployeePerformance
from app.models.employee_info import EmployeeInfo

logger = logging.getLogger(__name__)

class EmployeeTargetProcessor:
    """
    직원 월간 목표 데이터 전용 처리기
    LLM을 활용하여 컬럼을 분석하고 매핑
    """
    
    def __init__(self, db_session_factory: Optional[callable] = None):
        """초기화"""
        self.db_session_factory = db_session_factory
    
    @asynccontextmanager
    async def _get_db_session(self):
        """데이터베이스 세션 비동기 컨텍스트 매니저"""
        if not self.db_session_factory:
            raise ValueError("DB 세션 팩토리가 설정되지 않음")
        
        session = self.db_session_factory()
        try:
            # 트랜잭션 격리 레벨 설정
            await session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def analyze_and_process_targets(
        self, 
        table_data: List[Dict[str, Any]], 
        table_description: str = "",
        document_id: Optional[int] = None,
        uploader_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        메인 처리 함수 - LLM 기반 분석 및 처리
        """
        if not table_data:
            return {
                'success': False,
                'message': '테이블 데이터가 없습니다.'
            }
        
        try:
            # 1. 컬럼 분석 및 샘플 데이터 추출
            columns = list(table_data[0].keys())
            # 모든 컬럼명을 문자열로 변환 (안전장치)
            columns = [str(col) for col in columns]
            sample_data = table_data[:10] if len(table_data) >= 10 else table_data
            
            logger.info(f"📊 직원 목표 데이터 분석 시작")
            logger.info(f"  - 컬럼: {columns}")
            logger.info(f"  - 데이터 행 수: {len(table_data)}")
            
            # 2. LLM을 통한 컬럼 분류
            classification = await self._perform_llm_classification(
                columns, sample_data, table_description
            )
            
            if not classification:
                return {
                    'success': False,
                    'message': 'LLM 분류 실패'
                }
            
            # 3. 분류 결과 검증
            if not self._validate_classification(classification):
                return {
                    'success': False,
                    'message': '직원 목표 데이터 형식이 아닙니다. 사번 컬럼과 YYYYMM 형식의 월별 컬럼이 필요합니다.',
                    'details': classification
                }
            
            logger.info(f"✅ LLM 분류 성공")
            logger.info(f"  - 사번 컬럼: {classification['column_mapping'].get('employee_number')}")
            logger.info(f"  - 월별 목표 컬럼: {classification['column_mapping'].get('monthly_targets', [])}")
            
            # 4. 데이터 처리 및 저장
            result = await self._save_performance_data(
                table_data, 
                classification['column_mapping'],
                document_id,
                uploader_id
            )
            
            # 5. MV 갱신
            if result['success'] and (result.get('created_count', 0) > 0 or result.get('updated_count', 0) > 0):
                await self._refresh_mv()
                logger.info("✅ employee_performance_mv 갱신 완료")
            
            return result
            
        except Exception as e:
            logger.error(f"직원 목표 데이터 처리 중 오류: {e}")
            return {
                'success': False,
                'message': f'처리 중 오류 발생: {str(e)}'
            }
    
    async def _perform_llm_classification(self, columns: List[str], sample_data: List[Dict], description: str) -> Dict[str, Any]:
        """
        LLM을 사용하여 컬럼 분류
        """
        try:
            # 전용 프롬프트 구성
            system_prompt = """당신은 직원 월간 목표 데이터를 분석하는 전문가입니다.
업로드된 테이블에서 다음을 식별해주세요:
1. 사번 컬럼 (employee_number, 사번, 직원번호, emp_no, 사내번호 등)
2. 직원명 컬럼 (선택사항 - name, 이름, 성명, 직원명, 담당자 등)
3. YYYYMM 형식의 월별 목표 컬럼들 (예: 202401, 202402 등 6자리 숫자)

반드시 JSON 형식으로 응답하세요:
{
    "is_target_data": true/false,
    "column_mapping": {
        "employee_number": "실제 사번 컬럼명",
        "employee_name": "실제 직원명 컬럼명 (없으면 null)",
        "monthly_targets": ["202401", "202402", ...] // YYYYMM 형식 컬럼들
    },
    "confidence": 0.0-1.0,
    "reasoning": "분석 이유"
}

주의사항:
- YYYYMM 형식은 정확히 6자리 숫자여야 합니다 (예: 202401)
- 년도는 2000-2099, 월은 01-12 범위여야 합니다
- monthly_targets에는 실제 컬럼명을 그대로 넣어주세요"""
            
            # 샘플 데이터 포맷팅
            sample_str = ""
            for i, row in enumerate(sample_data[:3], 1):
                sample_str += f"행 {i}: {row}\n"
            
            user_prompt = f"""업로드된 데이터를 분석해주세요:

컬럼: {columns}

샘플 데이터:
{sample_str}

설명: {description if description else '없음'}

이 데이터가 직원 월간 목표 데이터인지 판단하고,
사번 컬럼과 YYYYMM 형식의 월별 목표 컬럼들을 찾아주세요."""
            
            # OpenAI API 호출
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            logger.info("🤖 LLM에 직원 목표 데이터 분석 요청")
            
            result = openai_service.create_json_completion(
                messages=messages,
                model="gpt-4o-mini",
                max_tokens=1000,
                temperature=0.1
            )
            
            if result:
                logger.info(f"🤖 LLM 응답: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM 분류 중 오류: {e}")
            return None
    
    def _validate_classification(self, classification: Dict[str, Any]) -> bool:
        """
        LLM 분류 결과 검증
        """
        if not classification:
            return False
        
        if not classification.get('is_target_data'):
            logger.warning("LLM이 직원 목표 데이터가 아니라고 판단")
            return False
        
        mapping = classification.get('column_mapping', {})
        
        # 사번 컬럼 필수
        if not mapping.get('employee_number'):
            logger.warning("사번 컬럼을 찾을 수 없음")
            return False
        
        # 월별 목표 컬럼 2개 이상 필수
        monthly_targets = mapping.get('monthly_targets', [])
        if len(monthly_targets) < 2:
            logger.warning(f"월별 목표 컬럼이 부족함: {len(monthly_targets)}개")
            return False
        
        # YYYYMM 형식 검증
        for month in monthly_targets:
            if not re.match(r'^20\d{2}(0[1-9]|1[0-2])$', str(month)):
                logger.warning(f"잘못된 YYYYMM 형식: {month}")
                return False
        
        return True
    
    async def _save_performance_data(
        self, 
        table_data: List[Dict[str, Any]], 
        column_mapping: Dict[str, str],
        document_id: Optional[int],
        uploader_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        employee_performance 테이블에 데이터 저장
        """
        employee_number_col = column_mapping['employee_number']
        employee_name_col = column_mapping.get('employee_name')
        monthly_targets = column_mapping['monthly_targets']
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_details = []
        
        logger.info(f"📝 직원 목표 데이터 저장 시작")
        logger.info(f"  - 사번 컬럼: {employee_number_col}")
        logger.info(f"  - 직원명 컬럼: {employee_name_col}")
        logger.info(f"  - 월별 목표 컬럼: {monthly_targets}")
        
        async with self._get_db_session() as session:
            for row_idx, row in enumerate(table_data, 1):
                # 사번 추출
                employee_number = row.get(employee_number_col)
                if not employee_number or str(employee_number).strip() == '' or str(employee_number) == 'nan':
                    skipped_count += 1
                    continue
                
                employee_number = str(employee_number).strip()
                
                # 직원명 추출 (선택사항)
                employee_name = None
                if employee_name_col:
                    employee_name = row.get(employee_name_col)
                    if employee_name and str(employee_name) != 'nan':
                        employee_name = str(employee_name).strip()
                
                # 사번으로 직원 ID 조회
                try:
                    employee_id = await get_employee_id(
                        session, 
                        employee_name=employee_name,
                        employee_number=employee_number
                    )
                    
                    if not employee_id:
                        # 직원 정보가 없는 경우 로그
                        error_msg = f"행 {row_idx}: 직원을 찾을 수 없음 - 사번: {employee_number}"
                        if employee_name:
                            error_msg += f", 이름: {employee_name}"
                        logger.warning(error_msg)
                        error_details.append(error_msg)
                        skipped_count += 1
                        continue
                    
                    # 직원 정보 로그
                    emp_result = await session.execute(
                        select(EmployeeInfo).filter(EmployeeInfo.employee_info_id == employee_id)
                    )
                    emp = emp_result.scalar_one_or_none()
                    if emp:
                        logger.debug(f"  직원 확인: {emp.name} (사번: {emp.employee_number})")
                    
                except Exception as e:
                    logger.error(f"행 {row_idx}: 직원 ID 조회 실패 - {e}")
                    skipped_count += 1
                    continue
                
                # 각 월별 목표 저장
                for month_col in monthly_targets:
                    target_amount = row.get(month_col)
                    
                    # 값 검증 및 변환
                    if target_amount is None or str(target_amount) in ['', 'nan', 'None', '-']:
                        continue
                    
                    try:
                        # 문자열로 변환 후 숫자만 추출
                        amount_str = str(target_amount).replace(',', '').replace('₩', '').replace(' ', '')
                        if amount_str.replace('.', '').replace('-', '').isdigit():
                            target_amount = float(amount_str)
                        else:
                            continue
                        
                        if target_amount <= 0:
                            continue
                        
                    except (ValueError, TypeError):
                        continue
                    
                    # YYYYMM -> YYYY-MM-01 변환
                    try:
                        year = int(str(month_col)[:4])
                        month = int(str(month_col)[4:6])
                        year_month = datetime(year, month, 1).date()
                    except (ValueError, TypeError) as e:
                        logger.error(f"날짜 변환 실패: {month_col} - {e}")
                        continue
                    
                    # Upsert 처리
                    try:
                        existing = await session.execute(
                            select(EmployeePerformance).filter(
                                EmployeePerformance.employee_id == employee_id,
                                EmployeePerformance.year_month == year_month
                            )
                        )
                        record = existing.scalar_one_or_none()
                        
                        if record:
                            # 기존 레코드 업데이트
                            old_amount = record.target_amount
                            record.target_amount = float(target_amount)
                            updated_count += 1
                            logger.debug(f"    목표 업데이트: {emp.name if emp else employee_id} - {year_month}: {old_amount:,.0f} → {target_amount:,.0f}")
                        else:
                            # 새 레코드 생성
                            new_record = EmployeePerformance(
                                employee_id=employee_id,
                                year_month=year_month,
                                target_amount=float(target_amount),
                                notes=f"문서 업로드 (ID: {document_id})" if document_id else None
                            )
                            session.add(new_record)
                            created_count += 1
                            logger.debug(f"    목표 생성: {emp.name if emp else employee_id} - {year_month}: {target_amount:,.0f}")
                    
                    except Exception as e:
                        logger.error(f"목표 저장 실패: 직원 {employee_id}, {year_month} - {e}")
                        continue
            
            # 커밋
            await session.commit()
        
        # 결과 요약
        total_processed = created_count + updated_count + skipped_count
        
        message = f"직원 목표 데이터 처리 완료: {created_count}개 생성, {updated_count}개 업데이트"
        if skipped_count > 0:
            message += f", {skipped_count}개 건너뜀"
        
        logger.info(f"📊 처리 완료 요약:")
        logger.info(f"  - 총 처리: {total_processed}행")
        logger.info(f"  - 생성: {created_count}건")
        logger.info(f"  - 업데이트: {updated_count}건")
        logger.info(f"  - 건너뜀: {skipped_count}행")
        
        result = {
            'success': True,
            'created_count': created_count,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'total_processed': total_processed,
            'message': message
        }
        
        if error_details:
            result['error_details'] = error_details[:10]  # 최대 10개만 반환
        
        return result
    
    async def _refresh_mv(self):
        """MV 갱신"""
        try:
            async with self._get_db_session() as session:
                logger.info("🔄 employee_performance_mv 갱신 시작...")
                await mv_refresh_service.refresh_employee_performance_mv(session)
                logger.info("✅ employee_performance_mv 갱신 완료")
        except Exception as e:
            logger.error(f"MV 갱신 실패: {e}")
            # MV 갱신 실패는 치명적이지 않으므로 에러를 발생시키지 않음


# 싱글톤 인스턴스
from app.services.utils.db import AsyncSessionLocal
employee_target_processor = EmployeeTargetProcessor(db_session_factory=AsyncSessionLocal)