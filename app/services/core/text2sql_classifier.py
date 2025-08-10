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


# 모델 import는 프로세서 클래스에서 처리됨

logger = logging.getLogger(__name__)

class Text2SQLTableClassifier:
    """Text2SQL 기반 테이블 분류기"""
    
    def __init__(self, db_session_factory: Optional[Callable] = None):
        """초기화"""
        self.db_session_factory = db_session_factory
        
    async def _validate_and_filter_target_tables(self, uploaded_columns: List[str], target_tables: List[Dict[str, Any]], sample_data: List[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """LLM 결과 테이블/매핑을 필수 컬럼 및 로컬 매핑으로 검증하여 정제"""
        validated: List[Dict[str, Any]] = []
        reasons: List[str] = []
        uploaded_set = set(str(c) for c in uploaded_columns)

        # 테이블별 필수 컬럼 정의
        required = {
            'employee_info': ['name', 'employee_number'],
            'customers': ['customer_name'],
            'products': ['product_name'],
            'sales_records': ['customer_name', 'employee_name', 'employee_number'],  # sales_records 필수 필드 복원
            'branches': ['branch_name', 'headquarters', 'department'],  # 지점 필수 필드 추가
            'branch_targets': []  # 목표/실적 데이터는 필수 컬럼 없음 (월별 패턴으로 감지)
        }

        async with self._get_db_session() as session:
            for t in target_tables:
                table = t.get('table_name')
                mapping = t.get('column_mapping', {}) or {}
                conf = t.get('confidence', 0.0)

                # 1) 필수 컬럼 키가 매핑에 존재하는지 확인
                req_cols = required.get(table, [])
                missing_keys = [rk for rk in req_cols if rk not in mapping]
                
                # 2) 누락된 필수 컬럼이 있다면 실패 처리 (sales_records 제외)
                if missing_keys and table != 'sales_records':
                    reasons.append(f"{table}: 필수 컬럼 매핑 누락 {missing_keys}")
                    continue

                # 3) 매핑된 소스 컬럼이 업로드 컬럼에 실제 존재하는지 확인
                nonexistent = [src for src in mapping.values() if str(src) not in uploaded_set]
                if nonexistent:
                    reasons.append(f"{table}: 존재하지 않는 소스 컬럼 매핑 {nonexistent}")
                    continue

                # 4) branch_targets 전용 규칙 - 목표/실적 패턴 확인
                if table == 'branch_targets':
                    # 목표, 실적, 달성률 관련 컬럼 확인
                    has_target_columns = any('목표' in str(col) for col in uploaded_columns)
                    has_actual_columns = any('실적' in str(col) for col in uploaded_columns)
                    has_achievement_columns = any('달성률' in str(col) for col in uploaded_columns)
                    
                    # 월별 컬럼 패턴 확인
                    has_monthly_columns = any(re.fullmatch(r'\d{6}', str(col)) for col in uploaded_columns)
                    
                    if not (has_target_columns or has_actual_columns or has_achievement_columns or has_monthly_columns):
                        reasons.append("branch_targets: 목표/실적 관련 컬럼이 없음")
                        continue
                    
                    logger.info(f"branch_targets 검증 통과: 목표={has_target_columns}, 실적={has_actual_columns}, 월별={has_monthly_columns}")
                
                # 5) sales_records 전용 규칙
                elif table == 'sales_records':
                    # 잘못된 매핑 키 수정 (customer_id -> customer_name, employee_id -> employee_number, product_id -> product_name)
                    if 'customer_id' in mapping:
                        mapping['customer_name'] = mapping.pop('customer_id')
                        logger.info(f"✅ sales_records 매핑 수정: customer_id -> customer_name = {mapping['customer_name']}")
                    
                    if 'employee_id' in mapping:
                        # employee_id는 employee_number로 매핑
                        mapping['employee_number'] = mapping.pop('employee_id')
                        logger.info(f"✅ sales_records 매핑 수정: employee_id -> employee_number = {mapping['employee_number']}")
                    
                    if 'product_id' in mapping:
                        mapping['product_name'] = mapping.pop('product_id')
                        logger.info(f"✅ sales_records 매핑 수정: product_id -> product_name = {mapping['product_name']}")
                    
                    # 월별 컬럼 패턴 확인 (더 유연하게)
                    has_monthly_columns = any(re.fullmatch(r'\d{6}', str(col)) for col in uploaded_columns)
                    
                    # 월별 행 데이터 확인 (데이터 값에 월 정보가 있는지)
                    has_monthly_rows = False
                    if sample_data:
                        for row in sample_data[:5]:  # 처음 5행만 확인
                            for val in row.values():
                                if re.fullmatch(r'\d{6}', str(val)):
                                    has_monthly_rows = True
                                    break
                            if has_monthly_rows:
                                break
                    
                    # 매출 관련 키워드 확인
                    sales_related_keywords = ['매출', '매출액', '금액', '수량', '방문횟수', '예산', '환자수', '판매']
                    has_sales_related = any(
                        any(keyword in str(col).lower() for keyword in sales_related_keywords)
                        for col in uploaded_columns
                    )
                    
                    # LLM metrics 기반 판단
                    metrics = t.get('metrics', {}) or {}
                    amount_ratio = float(metrics.get('sale_amount_numeric_ratio', 0.0) or 0.0)
                    date_ratio = float(metrics.get('sale_date_parse_ratio', 0.0) or 0.0)
                    monthly_cols = metrics.get('monthly_columns', []) or []
                    
                    # 기존 sale_amount/sale_date 매핑 확인
                    has_amount_date = ('sale_amount' in mapping) and ('sale_date' in mapping)
                    
                    # 조건들 계산
                    cond_monthly = bool(monthly_cols) or has_monthly_columns or has_monthly_rows
                    cond_sales_related = has_sales_related
                    cond_amount_date = has_amount_date and (amount_ratio >= 0.7 and date_ratio >= 0.7)
                    
                    # 디버그 로그 제거 - 불필요한 상세 정보
                    # 매핑 결과 최종 로그만 남김
                    logger.info(f"sales_records 최종 매핑: {mapping}")
                    
                    # 더 유연한 검증: 월별 데이터가 있거나 매출 관련 컬럼이 있으면 통과
                    if not (cond_monthly or cond_sales_related or cond_amount_date):
                        reasons.append("sales_records: 월별 데이터 또는 매출 관련 컬럼이 부족함")
                        continue

                t['column_mapping'] = mapping
                validated.append(t)

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
        """
        테이블 간의 의존성을 분석하여 저장 순서를 결정
        
        의존성 순서:
        1. branches (독립적)
        2. customers (독립적)
        3. employee_info (branches에 의존) 
        4. products (독립적)
        5. sales_records (customers, employee_info, products에 의존)
        6. interaction_logs (customers, employee_info에 의존)
        7. assignment_map (employee_info에 의존)
        """
        # 테이블별 의존성 레벨 정의
        dependency_levels = {
            'branches': 1,  # 최우선 생성
            'customers': 1,
            'products': 1,
            'employee_info': 2,  # branches 생성 후
            'branch_targets': 3,  # branches, employee_info 생성 후
            'sales_records': 3,
            'interaction_logs': 3,
            'assignment_map': 3,
            'documents': 4,
            'document_relations': 5
        }
        
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
                    
                    # 효율적인 LLM 프롬프트 구성(대표 컬럼 + 샘플 N행 + metrics 요청)
                    prompt = self._create_enhanced_llm_prompt(
                        columns, sample_data, table_description, multi_table_result
                    )
                    
                    # OpenAI API 호출
                    messages = [
                        {"role": "system", "content": "당신은 Excel 테이블 데이터를 분석하여 여러 데이터베이스 테이블에 어떤 데이터를 생성할 수 있는지 판단하는 전문가입니다."},
                        {"role": "user", "content": prompt}
                    ]
                    
                    result = openai_service.create_json_completion(
                        messages=messages,
                        model="gpt-4o-mini",
                        max_tokens=1500,
                        temperature=0.1
                    )
                    
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
    
    def _get_uploadable_columns(self, table_name: str) -> List[str]:
        """문서 업로드로 저장 가능한 컬럼만 반환"""
        uploadable_columns = {
            'branches': ['branch_name', 'headquarters', 'department', 'contact_number', 'status', 'notes'],  # 지점 정보
            'branch_targets': ['branch_id', 'employee_info_id', 'target_year', 'target_month', 
                              'target_amount', 'actual_amount', 'achievement_rate'],  # 지점 목표
            'employee_info': ['name', 'employee_number', 'position', 'branch_id',
                              'contact_number', 'base_salary', 'incentive_pay', 'avg_monthly_budget', 'latest_evaluation', 
                              'responsibilities'],  
            'customers': ['customer_name', 'address', 'doctor_name', 'total_patients', 'customer_grade', 
                          'notes'],               # 고객 정보
            'products': ['product_name', 'description', 'category'],                 # 제품 정보
            'sales_records': ['sale_amount', 'sale_date', 'employee_id', 'customer_id', 'product_id'], # 매출 정보
            'interaction_logs': ['employee_id', 'customer_id', 'interaction_type', 'summary', 'sentiment', 
                                'compliance_risk', 'interacted_at'], # 상담 기록
            'assignment_map': ['employee_id', 'customer_id']   # 담당 정보
        }
        return uploadable_columns.get(table_name, [])

    def _create_enhanced_llm_prompt(self, columns: List[str], sample_data: List[Dict], 
                                   table_description: str, multi_table_result: Dict[str, Any]) -> str:
        """향상된 LLM 프롬프트 생성"""
        prompt = f"""
        업로드된 Excel 파일의 컬럼들을 분석하여 어떤 데이터베이스 테이블들에 어떤 데이터를 생성할 수 있는지 판단해주세요.
        ## 업로드된 문서 정보:
        - 컬럼: {', '.join(columns)}
        - 샘플 데이터: {sample_data[:3] if sample_data else '없음'}
        - 문서 설명: {table_description if table_description else '없음'}

        ## 관련성이 높은 테이블들 (벡터 유사도 기반 선별):
        """
        
        for i, table_info in enumerate(multi_table_result['table_mappings'], 1):
            # 문서 업로드로 저장 가능한 컬럼만 필터링
            uploadable_columns = self._get_uploadable_columns(table_info['table_name'])
            table_columns_str = [str(col) for col in uploadable_columns] if uploadable_columns else []
            sample_data_str = ', '.join([str(data) for data in table_info.get('sample_data', [])]) if table_info.get('sample_data') else '없음'
            
            prompt += f"""
            {i}. {table_info['table_name']} (유사도: {table_info['similarity']:.3f})
            - 설명: {table_info['description']}
            - 테이블 컬럼들: {', '.join(table_columns_str)}
            - 샘플 데이터: {sample_data_str}
            """
        
        prompt += f"""

        ## 컬럼 매핑 가이드라인:
        ### 한국어-영어 매핑 규칙:
        - 지점/지점명/지사 → branch_name (branches)
        - 본부/사업부 → headquarters (branches)
        - 부서/팀 → department (branches)
        - 담당자/직원명 → name (employee_info, sales_records)
        - 사번 → employee_number (employee_info, sales_records) 
        - 거래처/거래처명/고객명/ID → customer_name (customers, sales_records)
        - 품목/제품명 → product_name (products, sales_records)

        ### 필수 컬럼 확인:
        - branches: branch_name, headquarters, department 필수 (나머지는 선택)
        - branch_targets: 목표/실적 관련 컬럼과 YYYYMM 형식 컬럼 필요 (월별 목표 데이터)
        - employee_info: name, employee_number 필수 (나머지는 선택)
        - customers: customer_name 필수 (나머지는 선택)
        - products: product_name 필수 (나머지는 선택)
        - sales_records: sale_amount, sale_date 필수 (employee_id, customer_id, product_id는 관계 테이블 존재 시 자동 매핑)
        - interaction_logs: employee_id, customer_id, interacted_at 필수 (관계 테이블 존재 시 자동 매핑)
        - assignment_map: employee_id, customer_id 필수 (관계 테이블 존재 시 자동 매핑)

        ## 분석 요청사항:
        1. **데이터 생성 가능성 판단**: 업로드된 컬럼으로 각 테이블의 필수 컬럼을 매핑할 수 있는지 확인
        2. **컬럼 매핑 수행**: 업로드 컬럼과 테이블 컬럼 간의 정확한 매핑 관계 설정
        3. **의존성 고려**: 독립 테이블(branches, customers, products)을 우선적으로 선택, employee_info는 branches 생성 후
        4. **지점 데이터 우선**: 지점/본부/부서 관련 컬럼이 있으면 branches 테이블을 최우선으로 포함
        5. **목표 데이터 우선**: 목표/실적/달성률 컬럼과 YYYYMM 패턴이 있으면 branch_targets 테이블 포함
        6. **매출 데이터 우선**: 매출 관련 컬럼이 있으면 반드시 sales_records 테이블을 포함해야 함
        7. **제외 기준**: 필수 컬럼을 매핑할 수 없는 테이블만 제외 (sales_records, branch_targets는 예외적으로 포함)
        8. **신뢰도 평가**: 필수 컬럼 매핑 가능성과 의존성 충족도를 기반으로 신뢰도 설정
        7. **월별 매출 데이터 특별 처리**: 
           - YYYYMM 형식 컬럼(예: 202212, 202301, 202302 등)의 값이 매출 형태의 값(예: 48200, 50000 등)이라면 월별 매출 데이터로 인식
           - 월별 컬럼들은 sale_amount나 sale_date로 매핑하지 말고, 별도로 처리됨
           - sales_records의 column_mapping에는 기본 정보(employee_name, employee_number, customer_name, product_name)만 포함
           - 각 월별 컬럼은 개별 매출 기록으로 변환되어 저장됨
        8. **데이터 품질 검증**: 
           - "총합계", "합계", "소계" 등 요약 행은 유효한 고객명이 아니므로 제외
           - 숫자만으로 구성된 고객명이나 제품명은 유효하지 않으므로 제외
        9. **데이터 정리 규칙**:
           - 제외할 행 예시: "총합계", "합계", "소계", "12345", "99999" 과 같이 기존 고객명 형태와 상이한 행

        **sales_records 테이블 판단 기준:**
        1. 월별 매출 데이터: 컬럼명이 6자리 숫자(예: 202212, 202301)로 월을 나타내는 경우
        2. 월별 행 데이터: '월' 컬럼에 6자리 숫자(예: 202212, 202301)가 있는 경우
        3. 매출 관련 컬럼: '매출', '매출액', '금액', '수량', '방문횟수', '예산', '환자수' 등의 컬럼이 있는 경우
        
        **주의사항:**
        - 월별 컬럼 구조: 사번/담당자/거래처 + 월별 컬럼들
        - 월별 행 구조: 거래처 + 월 + 매출 관련 컬럼들
        - 두 구조 모두 sales_records에 적합함

        ## 응답 형식:
        {{
            "target_tables": [
                {{
                    "table_name": "employee_info",
                    "confidence": 0.95,
                    "column_mapping": {{
                        "name": "담당자",
                        "employee_number": "사번"
                    }},
                    "reasoning": "필수 컬럼 name(담당자)과 employee_number(사번) 모두 매핑 가능하여 직원 정보 생성 가능"
                }},
                {{
                    "table_name": "products", 
                    "confidence": 0.90,
                    "column_mapping": {{
                        "product_name": "품목"
                    }},
                    "reasoning": "필수 컬럼 product_name이 품목에 매핑 가능하여 제품 정보 생성 가능"
                }},
                {{
                    "table_name": "customers", 
                    "confidence": 0.85,
                    "column_mapping": {{
                        "customer_name": "ID"
                    }},
                    "reasoning": "필수 컬럼 customer_name이 ID(거래처명)에 매핑 가능하여 고객 정보 생성 가능"
                }},
                {{
                    "table_name": "sales_records",
                    "confidence": 0.90,
                    "column_mapping": {{
                        "employee_name": "담당자",
                        "employee_number": "사번",
                        "customer_name": "ID",
                        "product_name": "품목"
                    }},
                    "reasoning": "월별 매출 데이터(202212, 202301 등)가 있어 sales_records 테이블에 매출 기록 생성 가능. 월별 컬럼들은 별도 처리됨"
                }}
            ],
            "confidence": 0.90,
            "reasoning": "기초 테이블(employee_info, products, customers) 생성 후 sales_records 생성 가능"
        }}

        **중요**: 필수 컬럼을 매핑할 수 없는 테이블은 절대 포함하지 마세요. JSON 형식으로만 응답해주세요.
        """
        return prompt


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