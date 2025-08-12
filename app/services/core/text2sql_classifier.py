"""
Text2SQL 기반 테이블 분류 서비스
LLM을 사용하여 테이블 데이터를 분석하고 적절한 데이터베이스 테이블에 분류합니다.
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Callable, Tuple
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import asyncio

# 공통 OpenAI 서비스 import
from app.services.external.openai_service import openai_service

from app.services.core.vector_similarity_service import vector_similarity_service
from app.services.core.table_processors import get_table_processor
from app.services.core.table_validators import TableValidator
from app.services.core.prompt_templates import PromptTemplates


# 모델 import는 프로세서 클래스에서 처리됨

logger = logging.getLogger(__name__)

class Text2SQLTableClassifier:
    """Text2SQL 기반 테이블 분류기"""
    
    def __init__(self, db_session_factory: Optional[Callable] = None):
        """초기화"""
        self.db_session_factory = db_session_factory
        
    async def _validate_and_filter_target_tables(self, uploaded_columns: List[str], target_tables: List[Dict[str, Any]], sample_data: List[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """LLM 결과 테이블/매핑을 검증하여 정제 (단순화된 버전)"""
        validated: List[Dict[str, Any]] = []
        reasons: List[str] = []
        uploaded_set = set(str(c) for c in uploaded_columns)

        async with self._get_db_session() as session:
            for t in target_tables:
                table_name = t.get('table_name')
                mapping = t.get('column_mapping', {}) or {}
                metrics = t.get('metrics', {})
                
                # employee_performance 테이블 특별 처리
                if table_name == 'employee_performance':
                    # 월별 목표 패턴 컬럼이 있는지 확인
                    has_monthly_target = any('_목표' in str(col) for col in uploaded_columns)
                    if has_monthly_target:
                        # 컬럼 매핑 검증 스킵, 빈 매핑으로 처리
                        t['column_mapping'] = {}
                        validated.append(t)
                        logger.info(f"✅ {table_name} 검증 통과: 월별 목표 컬럼 자동 인식")
                        continue
                
                # sales_records 테이블 특별 처리
                if table_name == 'sales_records':
                    # 월별 매출 패턴 컬럼이 있는지 확인 (YYYYMM 형식)
                    has_monthly_sales = any(re.match(r'^\d{6}$', str(col)) for col in uploaded_columns)
                    if has_monthly_sales:
                        # 월별 컬럼은 자동 처리되므로 매핑에서 제거
                        cleaned_mapping = {}
                        for key, value in mapping.items():
                            # 콤마로 구분된 월별 컬럼이거나 YYYYMM 형식이면 제외
                            if ',' in str(value) or re.match(r'^\d{6}$', str(value)):
                                continue
                            # 실제 존재하는 컬럼만 포함
                            if str(value) in uploaded_set:
                                cleaned_mapping[key] = value
                        t['column_mapping'] = cleaned_mapping
                        validated.append(t)
                        logger.info(f"✅ {table_name} 검증 통과: 월별 매출 컬럼 자동 인식, 매핑: {cleaned_mapping}")
                        continue
                
                # 매핑된 소스 컬럼이 업로드 컬럼에 실제 존재하는지 확인
                nonexistent = [src for src in mapping.values() if str(src) not in uploaded_set]
                if nonexistent:
                    reasons.append(f"{table_name}: 존재하지 않는 소스 컬럼 매핑 {nonexistent}")
                    continue
                
                # 테이블별 검증 (새로운 검증 모듈 사용)
                is_valid, reason = TableValidator.validate_table(
                    table_name, uploaded_columns, mapping, sample_data, metrics
                )
                
                if not is_valid:
                    reasons.append(f"{table_name}: {reason}")
                    continue
                
                t['column_mapping'] = mapping
                validated.append(t)
                logger.info(f"✅ {table_name} 검증 통과: {reason}")

        validated.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
        return validated, reasons

    
    @asynccontextmanager
    async def _get_db_session(self):
        """데이터베이스 세션 비동기 컨텍스트 매니저"""
        if not self.db_session_factory:
            logger.warning("DB 세션 팩토리가 설정되지 않음")
            yield None
            return
            
        session = self.db_session_factory()
        try:
            # 트랜잭션 격리 레벨 설정으로 락 경합 방지
            await session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def classify_table_with_text2sql(self, table_data: List[Dict[str, Any]], table_description: str = "", document_id: Optional[int] = None, uploader_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Text2SQL을 사용하여 테이블 분류 및 SQL 생성
        """
        if not table_data:
            return {
                'success': False,
                'message': '테이블 데이터가 없습니다.',
                'target_table': None,
                'confidence': 0.0
            }
        
        try:
            # 1. 테이블 구조 분석
            columns = list(table_data[0].keys()) if table_data else []
            # 모든 컬럼명을 문자열로 변환 (안전장치)
            columns = [str(col) for col in columns]            

            # LLM 인식 강화를 위해 최대 30행까지 전달
            sample_data = table_data[:30] if len(table_data) >= 30 else table_data
            
            # 2. Text2SQL 분류 수행
            classification_result = await self._perform_llm_classification(
                columns=columns,
                sample_data=sample_data,
                table_description=table_description
            )
            
            # 3. 결과 검증 및 데이터 삽입
            if classification_result['success'] and classification_result['confidence'] > 0.3:
                # 3-1. 사전 검증 및 교차 검증으로 테이블/매핑 정제
                target_tables = classification_result.get('target_tables', [])
                if target_tables:
                    validated_tables, exclude_reasons = await self._validate_and_filter_target_tables(columns, target_tables, sample_data)
                    if exclude_reasons:
                        for reason in exclude_reasons:
                            logger.warning(f"사전검증 제외: {reason}")
                    # 검증 실패 시 중단
                    if not validated_tables:
                        return {
                            'success': False,
                            'message': '사전검증 결과, 생성 가능한 테이블이 없습니다.',
                            'target_table': None,
                            'confidence': 0.0
                        }
                    # 검증 통과한 테이블로 교체
                    classification_result['target_tables'] = validated_tables
                else:
                    # 단일 테이블 응답에 대해서도 최소한의 검증 적용 가능 (향후 확장)
                    pass
                
                # 다중 테이블 처리 지원
                target_tables = classification_result.get('target_tables', [])
                if target_tables:
                    # 3-2. 의존성 분석 및 저장 순서 결정
                    ordered_tables = self._analyze_table_dependencies(target_tables)
                    logger.info(f"📋 테이블 저장 순서: {[t['table_name'] for t in ordered_tables]}")
                    
                    # 3-3. 순차 저장 실행
                    all_results = []
                    total_processed = 0
                    total_created = 0
                    total_updated = 0
                    total_skipped = 0
                    
                    # 의존성 순서에 맞게 테이블 처리
                    for table_info in ordered_tables:
                        table_name = table_info['table_name']
                        column_mapping = table_info['column_mapping']
                        confidence = table_info['confidence']
                        
                        logger.info(f"🔄 테이블 처리 시작: {table_name} (신뢰도: {confidence:.2f})")
                        
                        insertion_result = await self._insert_data_to_target_table(
                            table_data=table_data,
                            target_table=table_name,
                            column_mapping=column_mapping,
                            document_id=document_id,
                            uploader_id=uploader_id
                        )
                        
                        if insertion_result['success']:
                            processed_count = insertion_result.get('processed_count', 0)
                            created_count = insertion_result.get('created_count', 0)
                            updated_count = insertion_result.get('updated_count', 0)
                            skipped_count = insertion_result.get('skipped_count', 0)
                            
                            total_processed += processed_count
                            total_created += created_count
                            total_updated += updated_count
                            total_skipped += skipped_count
                            
                            all_results.append({
                                'table_name': table_name,
                                'processed_count': processed_count,
                                'created_count': created_count,
                                'updated_count': updated_count,
                                'skipped_count': skipped_count,
                                'confidence': confidence
                            })
                        else:
                            logger.warning(f"❌ {table_name} 테이블 처리 실패: {insertion_result['message']}")
                    
                    if all_results:
                        # 통합 요약 로그 출력
                        self._log_consolidated_summary(all_results, document_id)
                        
                        # 결과 요약
                        result_summary = ', '.join([f"{r['table_name']}({r['processed_count']}건)" for r in all_results])
                        message = f"다중 테이블 분류 완료: {result_summary} 총 {total_processed}건 저장 (문서 ID: {document_id})"
                        
                        return {
                            'success': True,
                            'target_table': target_tables[0]['table_name'],  # 주요 테이블
                            'target_tables': all_results,  # 모든 테이블 결과
                            'confidence': target_tables[0]['confidence'],
                            'reasoning': target_tables[0]['reasoning'],
                            'column_mapping': target_tables[0]['column_mapping'],
                            'processed_count': total_processed,
                            'created_count': total_created,
                            'updated_count': total_updated,
                            'skipped_count': total_skipped,
                            'message': message
                        }
                else:
                    # 다중 테이블 결과가 없으면 단일 테이블 처리 (하위 호환성)
                    target_table = classification_result['target_table']
                    column_mapping = classification_result['column_mapping']
                    
                    insertion_result = await self._insert_data_to_target_table(
                        table_data=table_data,
                        target_table=target_table,
                        column_mapping=column_mapping,
                        document_id=document_id,
                        uploader_id=uploader_id
                    )
                    
                    if insertion_result['success']:
                        processed_count = insertion_result.get('processed_count', 0)
                        created_count = insertion_result.get('created_count', 0)
                        updated_count = insertion_result.get('updated_count', 0)
                        skipped_count = insertion_result.get('skipped_count', 0)
                        
                        # 단일 테이블 결과를 다중 테이블 형식으로 변환하여 통합 로깅 사용
                        single_result = [{
                            'table_name': target_table,
                            'processed_count': processed_count,
                            'created_count': created_count,
                            'updated_count': updated_count,
                            'skipped_count': skipped_count,
                            'confidence': classification_result['confidence']
                        }]
                        
                        # 통합 요약 로그 출력
                        self._log_consolidated_summary(single_result, document_id)
                        
                        if processed_count > 0:
                            message = f"Text2SQL 분류 완료: {target_table} 테이블에 {processed_count}건 저장 (문서 ID: {document_id})"
                        else:
                            message = f"Text2SQL 분류 완료: {target_table} 테이블로 분류되었지만 저장할 데이터가 없음 (문서 ID: {document_id})"
                        
                        return {
                            'success': True,
                            'target_table': target_table,
                            'confidence': classification_result['confidence'],
                            'reasoning': classification_result['reasoning'],
                            'column_mapping': column_mapping,
                            'processed_count': processed_count,
                            'created_count': created_count,
                            'updated_count': updated_count,
                            'skipped_count': skipped_count,
                            'message': message
                        }
                    else:
                        # 실제 오류가 발생한 경우만 실패 처리
                        return {
                            'success': False,
                            'message': f"데이터 삽입 중 오류 발생: {insertion_result['message']}",
                            'target_table': target_table,
                            'confidence': classification_result['confidence']
                        }
            else:
                return {
                    'success': False,
                    'message': f"Text2SQL 분류 실패: 신뢰도 {classification_result['confidence']:.2f}",
                    'target_table': classification_result.get('target_table'),
                    'confidence': classification_result['confidence']
                }
                
        except Exception as e:
            logger.error(f"Text2SQL 분류 중 오류: {e}")
            return {
                'success': False,
                'message': f'Text2SQL 분류 중 오류 발생: {str(e)}',
                'target_table': None,
                'confidence': 0.0
            }
    
    def _analyze_table_dependencies(self, target_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """테이블 간의 의존성을 분석하여 저장 순서를 결정"""
        dependency_levels = PromptTemplates.get_dependency_order()
        
        # 의존성 레벨에 따라 정렬
        ordered_tables = sorted(target_tables, key=lambda x: dependency_levels.get(x['table_name'], 999))
        
        dependency_info = [f"{t['table_name']}(Lv.{dependency_levels.get(t['table_name'], 999)})" for t in ordered_tables]
        logger.info(f"테이블 의존성 분석 완료: {dependency_info}")
        
        return ordered_tables
    

    async def _perform_llm_classification(self, columns: List[str], sample_data: List[Dict], table_description: str) -> Dict[str, Any]:
        """LLM을 사용한 테이블 분류 (다중 테이블 분석과 조합)"""
        try:
            # 1단계: 다중 테이블 분석 시도
            async with self._get_db_session() as session:
                # 유사도 임계치 상향을 위해 analyze 단계에서 필터 강화는 내부 서비스에서 수행됨
                multi_table_result = await vector_similarity_service.analyze_multi_table_capability(
                    session, columns, sample_data
                )
                
                if multi_table_result['success'] and multi_table_result['table_mappings']:
                    logger.info(f"다중 테이블 분석 성공: {len(multi_table_result['table_mappings'])}개 테이블 발견")
                    
                    # 가장 유사도가 높은 테이블을 주요 타겟으로 선택
                    best_mapping = max(multi_table_result['table_mappings'], 
                                     key=lambda x: x['similarity'])
                    
                    # 새로운 템플릿 시스템으로 프롬프트 생성
                    prompt = PromptTemplates.build_prompt(
                        columns=columns,
                        sample_data=sample_data,
                        description=table_description,
                        related_tables=multi_table_result['table_mappings']
                    )
                    
                    # 프롬프트 로깅 (디버깅용)
                    logger.info("="*80)
                    logger.info("🔍 LLM 프롬프트 구성:")
                    logger.info("-"*80)
                    logger.info(f"업로드된 컬럼: {columns}")
                    logger.info(f"샘플 데이터 (첫 2행): {sample_data[:2] if sample_data else 'None'}")
                    logger.info("-"*80)
                    logger.info("시스템 프롬프트:")
                    logger.info(PromptTemplates.SYSTEM_PROMPT)
                    logger.info("-"*80)
                    logger.info("사용자 프롬프트 (처음 1000자):")
                    logger.info(prompt[:1000] + "..." if len(prompt) > 1000 else prompt)
                    logger.info("="*80)
                    
                    # OpenAI API 호출
                    messages = [
                        {"role": "system", "content": PromptTemplates.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                    
                    result = openai_service.create_json_completion(
                        messages=messages,
                        model="gpt-4o-mini",
                        max_tokens=1500,
                        temperature=0.1
                    )
                    
                    # LLM 응답 로깅
                    logger.info("="*80)
                    logger.info("🤖 LLM 응답:")
                    logger.info("-"*80)
                    if result:
                        import json
                        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
                    else:
                        logger.info("응답 없음 또는 파싱 실패")
                    logger.info("="*80)
                    
                    # JSON 파싱 실패 시 명확히 실패 반환
                    if not result:
                        return {
                            'success': False,
                            'message': 'LLM JSON 파싱 실패',
                            'target_table': None,
                            'confidence': 0.0
                        }

                    if result and 'target_tables' in result:
                        logger.info(f"다중 테이블 LLM 분류 완료: {result.get('target_tables')}")
                        
                        # 모든 선택된 테이블 처리(LLM metrics 기반 1차 필터)
                        target_tables = result.get('target_tables', [])
                        if target_tables:
                            filtered = []
                            for t in target_tables:
                                table = t.get('table_name')
                                mapping = t.get('column_mapping', {}) or {}
                                if table == 'sales_records':
                                    metrics = t.get('metrics', {}) or {}
                                    amount_ratio = float(metrics.get('sale_amount_numeric_ratio', 0.0) or 0.0)
                                    date_ratio = float(metrics.get('sale_date_parse_ratio', 0.0) or 0.0)
                                    monthly_cols = metrics.get('monthly_columns', []) or []
                                    
                                    # 월별 컬럼 패턴 확인
                                    has_monthly_columns = any(re.fullmatch(r'\d{6}', str(col)) for col in columns)
                                    
                                    # 매출 관련 키워드 확인
                                    sales_related_keywords = ['매출', '매출액', '금액', '수량', '방문횟수', '예산', '환자수', '판매']
                                    has_sales_columns = any(
                                        any(keyword in str(col).lower() for keyword in sales_related_keywords)
                                        for col in columns
                                    )
                                    
                                    has_amount_date = ('sale_amount' in mapping) and ('sale_date' in mapping)
                                    cond_monthly = bool(monthly_cols) or has_monthly_columns
                                    cond_sales_related = has_sales_columns
                                    cond_amount_date = has_amount_date and (amount_ratio >= 0.7 and date_ratio >= 0.7)
                                    
                                    # 더 유연한 검증: 월별 데이터가 있거나 매출 관련 컬럼이 있으면 통과
                                    if not (cond_monthly or cond_sales_related or cond_amount_date):
                                        continue
                                filtered.append(t)

                            # 신뢰도 순으로 정렬
                            sorted_tables = sorted(filtered, key=lambda x: x.get('confidence', 0.0), reverse=True)
                            
                            return {
                                'success': True,
                                'target_tables': sorted_tables,  # 단일 테이블이 아닌 리스트로 반환
                                'target_table': sorted_tables[0].get('table_name'),  # 하위 호환성을 위해 유지
                                'confidence': sorted_tables[0].get('confidence', 0.0),
                                'reasoning': sorted_tables[0].get('reasoning', ''),
                                'column_mapping': sorted_tables[0].get('column_mapping', {}),
                                'method': 'multi_table_llm',
                                'table_mappings': multi_table_result['table_mappings']
                            }
            
            # 다중 테이블 분석 실패 시
            logger.warning("다중 테이블 분석 실패 - 관련 테이블을 찾을 수 없음")
            return {
                'success': False,
                'message': '관련된 테이블을 찾을 수 없습니다.',
                'target_table': None,
                'confidence': 0.0
            }
            
        except Exception as e:
            logger.error(f"LLM 분류 중 오류: {e}")
            return {
                'success': False,
                'message': f'LLM 분류 중 오류: {str(e)}',
                'target_table': None,
                'confidence': 0.0
            }
    



    async def _insert_data_to_target_table(self, table_data: List[Dict[str, Any]], target_table: str, column_mapping: Dict[str, str], document_id: Optional[int] = None, uploader_id: Optional[int] = None) -> Dict[str, Any]:
        """대상 테이블에 데이터 삽입 - 모든 테이블에 processor 사용"""
        try:
            # 모든 테이블에 대해 통합 processor 사용
            return await self._execute_with_session(self._insert_with_processor, table_data, target_table, column_mapping, document_id, uploader_id)
        except Exception as e:
            logger.error(f"데이터 삽입 중 오류: {e}")
            return {
                'success': False,
                'message': f'데이터 삽입 중 오류: {str(e)}',
                'processed_count': 0,
                'created_count': 0,
                'updated_count': 0,
                'skipped_count': 0
            }
    
    async def _execute_with_session(self, func: Callable[[AsyncSession], Dict[str, Any]], *args) -> Dict[str, Any]:
        """세션을 사용하여 함수 실행 (비동기)"""
        try:
            async with self._get_db_session() as session:
                if asyncio.iscoroutinefunction(func):
                    return await func(session, *args)
                else:
                    return func(session, *args)
        except SQLAlchemyError as e:
            logger.error(f"DB 오류: {e}")
            return {
                'success': False,
                'message': f'데이터베이스 오류: {str(e)}',
                'processed_count': 0
            }
        except Exception as e:
            logger.error(f"처리 중 예상치 못한 오류: {e}")
            return {
                'success': False,
                'message': f'처리 중 오류 발생: {str(e)}',
                'processed_count': 0
            }
    
    # === 데이터 삽입 메서드들 ===
    
    async def _insert_with_processor(self, session: AsyncSession, table_data: List[Dict[str, Any]], table_name: str, column_mapping: Dict[str, Any], document_id: Optional[int] = None, uploader_id: Optional[int] = None) -> Dict[str, Any]:
        """새로운 통합 처리기를 사용한 데이터 삽입"""
        try:
            logger.info(f"🔄 {table_name} 테이블 처리기 시작: {len(table_data)}행, 컬럼 매핑: {column_mapping}")
            processor = get_table_processor(table_name, session)
            result = await processor.process_batch(table_data, column_mapping, document_id, uploader_id)
            # 중복 로그 제거 - process_batch에서 이미 완료 메시지 출력
            return result
        except Exception as e:
            logger.error(f"❌ {table_name} 테이블 처리 중 오류: {e}")
            return {
                'success': False,
                'message': f'{table_name} 처리 중 오류: {str(e)}',
                'processed_count': 0,
                'created_count': 0,
                'updated_count': 0,
                'skipped_count': 0
            }
    
    # 모든 개별 insert 메서드들은 _insert_with_processor로 통합되어 더 이상 필요하지 않음
    # table_processors.py의 각 Processor 클래스가 처리를 담당
    

    

    
    def _log_consolidated_summary(self, all_results: List[Dict[str, Any]], document_id: Optional[int] = None):
        """모든 테이블 처리 완료 후 통합 요약 로그 출력"""
        if not all_results:
            return
        
        # 테이블별 단위 매핑
        table_units = {
            'branches': '개',
            'employee_info': '명',
            'customers': '건', 
            'products': '개',
            'sales_records': '건',
            'interaction_logs': '건',
            'assignment_map': '건',
            'documents': '건',
            'document_relations': '건'
        }
        
        # 전체 통계 계산
        total_processed = sum(r.get('processed_count', 0) for r in all_results)
        total_created = sum(r.get('created_count', 0) for r in all_results)
        total_updated = sum(r.get('updated_count', 0) for r in all_results)
        total_skipped = sum(r.get('skipped_count', 0) for r in all_results)
        
        # 개별 테이블 요약 구성
        table_summaries = []
        for result in all_results:
            table_name = result['table_name']
            unit = table_units.get(table_name, '건')
            
            processed = result.get('processed_count', 0)
            created = result.get('created_count', 0)
            updated = result.get('updated_count', 0)
            skipped = result.get('skipped_count', 0)
            
            # 모든 테이블을 요약에 포함 (processed_count가 0이어도)
            summary_parts = []
            if processed > 0:
                if created > 0:
                    summary_parts.append(f"{created}{unit} 생성")
                if updated > 0:
                    summary_parts.append(f"{updated}{unit} 업데이트")
                if skipped > 0:
                    summary_parts.append(f"{skipped}{unit} 건너뜀")
                
                if summary_parts:
                    # sales_records의 경우 실제 레코드 수를 명확히 표시
                    if table_name == 'sales_records' and created > 0:
                        table_summaries.append(f"{table_name}({created}{unit} 생성 - {processed}행에서 생성)")
                    else:
                        table_summaries.append(f"{table_name}({', '.join(summary_parts)})")
                else:
                    table_summaries.append(f"{table_name}({processed}행 처리됨)")
            else:
                # processed_count가 0인 경우도 표시
                table_summaries.append(f"{table_name}(0행 처리됨)")
        
        # 통합 요약 로그 출력
        if table_summaries:
            summary_message = f"📊 문서 처리 완료 (문서 ID: {document_id}): {' | '.join(table_summaries)}"
            if total_processed > 0:
                summary_message += f" | 총 {total_processed}건 처리됨"
            logger.info(summary_message)
        else:
            logger.info(f"📊 문서 처리 완료 (문서 ID: {document_id}): 저장할 데이터 없음")


# 싱글턴 인스턴스
from app.services.utils.db import AsyncSessionLocal
text2sql_classifier = Text2SQLTableClassifier(db_session_factory=AsyncSessionLocal) 