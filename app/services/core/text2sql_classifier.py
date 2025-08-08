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
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, select
from datetime import datetime, timezone
import asyncio

# 공통 OpenAI 서비스 import
from app.services.external.openai_service import openai_service

from app.services.core.vector_similarity_service import vector_similarity_service
from app.services.core.table_processors import get_table_processor

# 모델 import
from app.models.employee_info import EmployeeInfo
from app.models.customers import Customer
from app.models.sales_records import SalesRecord
from app.models.products import Product
from app.models.interaction_logs import InteractionLog
from app.models.assignment_map import AssignmentMap
from app.models.documents import Document
from app.models.document_relations import DocumentRelation

logger = logging.getLogger(__name__)

class Text2SQLTableClassifier:
    """Text2SQL 기반 테이블 분류기"""
    
    def __init__(self, db_session_factory: Optional[Callable] = None):
        """초기화"""
        self.db_session_factory = db_session_factory
        
    async def _validate_and_filter_target_tables(self, uploaded_columns: List[str], target_tables: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """LLM 결과 테이블/매핑을 필수 컬럼 및 로컬 매핑으로 검증하여 정제"""
        validated: List[Dict[str, Any]] = []
        reasons: List[str] = []
        uploaded_set = set(str(c) for c in uploaded_columns)

        # 테이블별 필수 컬럼 정의
        required = {
            'employee_info': ['name', 'employee_number'],
            'customers': ['customer_name'],
            'products': ['product_name'],
            'sales_records': ['employee_name', 'employee_number', 'customer_name']
        }

        async with self._get_db_session() as session:
            for t in target_tables:
                table = t.get('table_name')
                mapping = t.get('column_mapping', {}) or {}
                conf = t.get('confidence', 0.0)

                # 1) 필수 컬럼 키가 매핑에 존재하는지 확인(매출은 별도 규칙)
                req_cols = required.get(table, [])
                missing_keys = [rk for rk in req_cols if rk not in mapping]
                if missing_keys and table != 'sales_records':
                    reasons.append(f"{table}: 필수 컬럼 매핑 누락 {missing_keys}")
                    continue

                # 2) 매핑된 소스 컬럼이 업로드 컬럼에 실제 존재하는지 확인
                nonexistent = [src for src in mapping.values() if str(src) not in uploaded_set]
                if nonexistent:
                    reasons.append(f"{table}: 존재하지 않는 소스 컬럼 매핑 {nonexistent}")
                    continue

                # 3) 로컬 자동 매핑과 교차 검증(간단 동일 매칭)
                try:
                    local_map = await vector_similarity_service.find_column_mapping(session, table, uploaded_columns)
                except Exception:
                    local_map = {}
                filtered_map: Dict[str, Any] = {}
                for dst, src in mapping.items():
                    local_src = local_map.get(dst)
                    if local_src and str(local_src) == str(src):
                        filtered_map[dst] = src

                if req_cols and any(k not in filtered_map for k in req_cols) and table != 'sales_records':
                    reasons.append(f"{table}: 교차 검증 실패(필수 컬럼 불일치)")
                    continue

                # 4) sales_records 전용 규칙
                if table == 'sales_records':
                    has_monthly = any(re.fullmatch(r'\d{6}', str(col)) for col in uploaded_columns)
                    has_amount_date = ('sale_amount' in mapping) and ('sale_date' in mapping)
                    if not has_monthly and not has_amount_date:
                        reasons.append("sales_records: 월별 컬럼 또는 (sale_amount, sale_date) 매핑이 필요")
                        continue
                    base_keys = ['employee_name', 'employee_number', 'customer_name']
                    if any(k not in mapping for k in base_keys):
                        reasons.append("sales_records: 기본 필수 컬럼 매핑 누락(employee_name, employee_number, customer_name)")
                        continue
                    filtered_map = mapping if mapping else {}

                t['column_mapping'] = filtered_map or mapping
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
            

            sample_data = table_data[:3] if len(table_data) >= 3 else table_data
            
            # 2. Text2SQL 분류 수행
            classification_result = await self._perform_text2sql_classification(
                columns=columns,
                sample_data=sample_data,
                table_description=table_description
            )
            
            # 3. 결과 검증 및 데이터 삽입
            if classification_result['success'] and classification_result['confidence'] > 0.3:
                # 3-1. 사전 검증 및 교차 검증으로 테이블/매핑 정제
                target_tables = classification_result.get('target_tables', [])
                if target_tables:
                    validated_tables, exclude_reasons = await self._validate_and_filter_target_tables(columns, target_tables)
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
                    # 다중 테이블 순차 처리
                    all_results = []
                    total_processed = 0
                    total_created = 0
                    total_updated = 0
                    total_skipped = 0
                    
                    # 개별 테이블 처리 결과 수집
                    for table_info in target_tables:
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
    
    async def _perform_text2sql_classification(self, columns: List[str], sample_data: List[Dict], table_description: str) -> Dict[str, Any]:
        """
        LLM을 사용한 Text2SQL 분류 수행
        """
        if not openai_service.is_available():
            logger.error("OpenAI 클라이언트가 사용 불가능합니다.")
            return {
                'success': False,
                'message': 'OpenAI 클라이언트가 초기화되지 않았습니다.',
                'target_table': None,
                'confidence': 0.0
            }
        
        try:
            # LLM 기반 분류 수행
            llm_result = await self._perform_llm_classification(columns, sample_data, table_description)
            
            if llm_result['success']:
                return llm_result
            else:
                logger.error(f"LLM 분류 실패: {llm_result['message']}")
                return llm_result
                
        except Exception as e:
            logger.error(f"LLM 분류 중 오류: {e}")
            return {
                'success': False,
                'message': f'LLM 분류 중 오류: {str(e)}',
                'target_table': None,
                'confidence': 0.0
            }
    
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
                    
                    # 효율적인 LLM 프롬프트 구성
                    prompt = self._create_enhanced_llm_prompt(
                        columns, sample_data, table_description, multi_table_result
                    )
                    
                    # OpenAI API 호출
                    messages = [
                        {"role": "system", "content": "당신은 Excel 테이블 데이터를 분석하여 여러 데이터베이스 테이블에 데이터를 생성할 수 있는지 판단하는 전문가입니다."},
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
                        
                        # 모든 선택된 테이블 처리
                        target_tables = result.get('target_tables', [])
                        if target_tables:
                            # 신뢰도 순으로 정렬
                            sorted_tables = sorted(target_tables, key=lambda x: x.get('confidence', 0.0), reverse=True)
                            
                            return {
                                'success': True,
                                'target_tables': sorted_tables,  # 단일 테이블이 아닌 리스트로 반환
                                'target_table': sorted_tables[0].get('table_name'),  # 하위 호환성을 위해 유지
                                'confidence': sorted_tables[0].get('confidence', 0.0),
                                'reasoning': sorted_tables[0].get('reasoning', ''),
                                'column_mapping': sorted_tables[0].get('column_mapping', {}),
                                'method': 'multi_table_llm',
                                'table_mappings': multi_table_result['table_mappings'],
                                'dependency_analysis': multi_table_result['dependency_analysis']
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
    
    def _create_enhanced_llm_prompt(self, columns: List[str], sample_data: List[Dict], 
                                   table_description: str, multi_table_result: Dict[str, Any]) -> str:
        """다중 테이블 분석을 위한 향상된 LLM 프롬프트 생성"""
        prompt = f"""
업로드된 Excel 파일의 컬럼들을 분석하여 어떤 데이터베이스 테이블들에 데이터를 생성할 수 있는지 판단해주세요.

## 업로드된 컬럼들:
{', '.join(columns)}

## 샘플 데이터:
{json.dumps(sample_data[:3], ensure_ascii=False, indent=2) if sample_data else '없음'}

## 문서 설명:
{table_description if table_description else '없음'}

## 관련성이 높은 테이블들 (벡터 유사도 기반 선별):
"""
        
        for i, table_info in enumerate(multi_table_result['table_mappings'], 1):
            # 모든 컬럼명을 문자열로 변환
            table_columns_str = [str(col) for col in table_info['columns']] if table_info['columns'] else []
            sample_data_str = ', '.join([str(data) for data in table_info.get('sample_data', [])]) if table_info.get('sample_data') else '없음'
            
            prompt += f"""
{i}. {table_info['table_name']} (유사도: {table_info['similarity']:.3f})
   - 설명: {table_info['description']}
   - 테이블 컬럼들: {', '.join(table_columns_str)}
   - 샘플 데이터: {sample_data_str}
"""
        
        # 의존성 분석 결과도 문자열로 변환
        primary_tables_str = [str(table) for table in multi_table_result['dependency_analysis']['primary_tables']]
        dependent_tables_str = [str(table) for table in multi_table_result['dependency_analysis']['dependent_tables']]
        creation_order_str = [str(table) for table in multi_table_result['dependency_analysis']['creation_order']]
        
        prompt += f"""
        ## 테이블 의존성 분석:
        - 독립 테이블 (먼저 생성 가능): {', '.join(primary_tables_str)}
        - 의존 테이블 (다른 테이블 필요): {', '.join(dependent_tables_str)}
        - 권장 생성 순서: {', '.join(creation_order_str)}

        ## 컬럼 매핑 가이드라인:
        ### 한국어-영어 매핑 규칙:
        - 담당자/직원명 → name (employee_info, sales_records)
        - 사번 → employee_number (employee_info, sales_records) 
        - 거래처/거래처명/고객명/ID → customer_name (customers, sales_records)
        - 품목/제품명 → product_name (products, sales_records)

        ### 필수 컬럼 확인:
        - employee_info: name, employee_number 필수 (나머지는 선택)
        - customers: customer_name 필수 (나머지는 선택)
        - products: product_name 필수 (나머지는 선택)
        - sales_records: sale_amount, sale_date 필수 (employee_id, customer_id, product_id는 관계 테이블 존재 시 자동 매핑)
        - interaction_logs: employee_id, customer_id 필수 (관계 테이블 존재 시 자동 매핑)
        - assignment_map: employee_id, customer_id 필수 (관계 테이블 존재 시 자동 매핑)

        ## 분석 요청사항:
        1. **데이터 생성 가능성 판단**: 업로드된 컬럼으로 각 테이블의 필수 컬럼을 매핑할 수 있는지 확인
        2. **컬럼 매핑 수행**: 업로드 컬럼과 테이블 컬럼 간의 정확한 매핑 관계 설정
        3. **의존성 고려**: 독립 테이블(employee_info, customers, products)을 우선적으로 선택
        4. **매출 데이터 우선**: 매출 관련 컬럼이 있으면 반드시 sales_records 테이블을 포함해야 함
        5. **제외 기준**: 필수 컬럼을 매핑할 수 없는 테이블만 제외 (sales_records는 예외적으로 포함)
        6. **신뢰도 평가**: 필수 컬럼 매핑 가능성과 의존성 충족도를 기반으로 신뢰도 설정
        7. **월별 매출 데이터 특별 처리**: 
           - YYYYMM 형식 컬럼(예: 202212, 202301, 202302 등)은 월별 매출 데이터로 인식
           - 월별 매출 데이터가 있으면 반드시 sales_records 테이블을 포함해야 함
           - 월별 컬럼들은 sale_amount나 sale_date로 매핑하지 말고, 별도로 처리됨
           - sales_records의 column_mapping에는 기본 정보(employee_name, employee_number, customer_name, product_name)만 포함
           - 각 월별 컬럼은 개별 매출 기록으로 변환되어 저장됨
        8. **데이터 품질 검증**: 
           - "총합계", "합계", "소계" 등 요약 행은 유효한 고객명이 아니므로 제외
           - 숫자만으로 구성된 고객명이나 제품명은 유효하지 않으므로 제외
        9. **데이터 정리 규칙**:
           - 제외할 행 예시: "총합계", "합계", "소계", "12345", "99999" 과 같이 기존 고객명 형태와 상이한 행

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
        """대상 테이블에 데이터 삽입"""
        try:
            if target_table == 'employee_info':
                return await self._execute_with_session(self._insert_employee_info, table_data, column_mapping, document_id, uploader_id)
            elif target_table in ['customers', 'products', 'sales_records']:
                return await self._execute_with_session(self._insert_with_processor, table_data, target_table, column_mapping, document_id, uploader_id)
            elif target_table == 'interaction_logs':
                return await self._execute_with_session(self._insert_interaction_logs, table_data, column_mapping)
            elif target_table == 'assignment_map':
                return await self._execute_with_session(self._insert_assignment_map, table_data, column_mapping)
            elif target_table == 'documents':
                return await self._execute_with_session(self._insert_documents, table_data, column_mapping)
            elif target_table == 'document_relations':
                return await self._execute_with_session(self._insert_document_relations, table_data, column_mapping)
            else:
                return {
                    'success': False,
                    'message': f'지원하지 않는 테이블: {target_table}',
                    'processed_count': 0,
                    'created_count': 0,
                    'updated_count': 0,
                    'skipped_count': 0
                }
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
    
    async def _insert_with_processor(self, session: AsyncSession, table_data: List[Dict[str, Any]], table_name: str, column_mapping: Dict[str, str], document_id: Optional[int] = None, uploader_id: Optional[int] = None) -> Dict[str, Any]:
        """새로운 통합 처리기를 사용한 데이터 삽입"""
        try:
            processor = get_table_processor(table_name, session)
            return await processor.process_batch(table_data, column_mapping, document_id, uploader_id)
        except Exception as e:
            logger.error(f"{table_name} 테이블 처리 중 오류: {e}")
            return {
                'success': False,
                'message': f'{table_name} 처리 중 오류: {str(e)}',
                'processed_count': 0,
                'created_count': 0,
                'updated_count': 0,
                'skipped_count': 0
            }
    
    async def _insert_employee_info(self, session: AsyncSession, table_data: List[Dict[str, Any]], column_mapping: Dict[str, str], document_id: Optional[int] = None, uploader_id: Optional[int] = None) -> Dict[str, Any]:
        """직원 인사 정보 삽입 (사번으로만 조회)"""
        processed_count = 0
        skipped_count = 0
        created_count = 0
        updated_count = 0
        
        try:
            for row in table_data:
                # 사번 추출 (필수)
                employee_number = None
                if 'employee_number' in column_mapping and row.get(column_mapping['employee_number']):
                    employee_number = str(row[column_mapping['employee_number']]).strip()
                else:
                    pass
                
                if not employee_number or employee_number == 'nan':
                    skipped_count += 1
                    continue
                
                # 이름 추출
                name = str(row[column_mapping['name']]).strip() if 'name' in column_mapping and row.get(column_mapping['name']) else None
                
                if not name:
                    skipped_count += 1
                    continue
                
                # 사번으로만 기존 직원 확인
                result = await session.execute(
                    select(EmployeeInfo).filter(EmployeeInfo.employee_number == employee_number)
                )
                existing_employee = result.scalar_one_or_none()
                
                if existing_employee:
                    # 기존 데이터와 입력 데이터 비교
                    has_changes = self._compare_employee_data(existing_employee, row, column_mapping)
                    
                    if has_changes:
                        # 변경사항이 있으면 업데이트
                        self._update_employee_info(existing_employee, row, column_mapping)
                        updated_count += 1
                    else:
                        # 동일한 데이터면 건너뛰기
                        skipped_count += 1
                else:
                    # 새 직원 등록 (자동 생성)
                    new_employee = self._create_employee_info(row, column_mapping)
                    new_employee.is_auto_created = True  # 자동 생성 표시
                    new_employee.approval_status = 'pending'  # 승인 대기 상태
                    session.add(new_employee)
                    await session.flush()  # ID 생성
                    created_count += 1
                
                processed_count += 1
            
            return {
                'success': True,
                'message': f'직원 인사 정보 삽입 완료: {processed_count}명 처리됨, {created_count}명 생성, {updated_count}명 업데이트, {skipped_count}명 건너뜀',
                'processed_count': processed_count,
                'created_count': created_count,
                'updated_count': updated_count,
                'skipped_count': skipped_count
            }
            
        except SQLAlchemyError as e:
            logger.error(f"직원 인사 정보 삽입 중 DB 오류: {e}")
            raise
    
    def _create_employee_info(self, row: Dict[str, Any], column_mapping: Dict[str, str]) -> EmployeeInfo:
        """직원 정보 객체 생성"""
        employee_data = {}
        
        # EmployeeInfo 모델의 유효한 필드들
        valid_fields = {
            'name', 'employee_number', 'team', 'position', 'business_unit', 'branch',
            'contact_number', 'base_salary', 'incentive_pay', 'avg_monthly_budget',
            'latest_evaluation', 'responsibilities', 'is_auto_created', 'approval_status',
            'approved_by', 'approved_at', 'approval_notes'
        }
        
        # 매핑된 컬럼에서 데이터 추출
        for db_field, source_column in column_mapping.items():
            if source_column in row and row[source_column] is not None:
                value = str(row[source_column]).strip()
                
                # 숫자 필드 처리
                if db_field in ['base_salary', 'incentive_pay', 'avg_monthly_budget']:
                    try:
                        value = int(str(value).replace(',', '').replace('₩', '').strip())
                    except:
                        value = None
                
                # employee_name을 name으로 매핑
                if db_field == 'employee_name':
                    employee_data['name'] = value
                elif db_field in valid_fields:
                    # EmployeeInfo 모델에 존재하는 필드만 허용
                    employee_data[db_field] = value
                else:
                    # EmployeeInfo 모델에 존재하지 않는 필드는 무시
                    logger.debug(f"EmployeeInfo에 존재하지 않는 필드 무시: {db_field}")
        
        return EmployeeInfo(**employee_data)
    
    def _compare_employee_data(self, existing_employee: EmployeeInfo, row: Dict[str, Any], column_mapping: Dict[str, str]) -> bool:
        """기존 직원 데이터와 입력 데이터 비교하여 변경사항이 있는지 확인"""
        for db_field, source_column in column_mapping.items():
            if source_column in row and row[source_column] is not None:
                new_value = str(row[source_column]).strip()
                
                # 숫자 필드 처리
                if db_field in ['base_salary', 'incentive_pay', 'avg_monthly_budget']:
                    try:
                        new_value = int(str(new_value).replace(',', '').replace('₩', '').strip())
                    except:
                        new_value = None
                
                # 기존 값 가져오기
                existing_value = getattr(existing_employee, db_field, None)
                
                # 문자열 필드는 문자열로 비교
                if isinstance(existing_value, str):
                    existing_value = existing_value.strip()
                
                # 값이 다르면 변경사항 있음
                if existing_value != new_value:
                    logger.debug(f"변경사항 발견 - {db_field}: '{existing_value}' → '{new_value}'")
                    return True
        
        return False
    

    
    def _update_employee_info(self, employee: EmployeeInfo, row: Dict[str, Any], column_mapping: Dict[str, str]):
        """직원 정보 업데이트"""
        for db_field, source_column in column_mapping.items():
            if source_column in row and row[source_column] is not None:
                value = str(row[source_column]).strip()
                
                # 숫자 필드 처리
                if db_field in ['base_salary', 'incentive_pay', 'avg_monthly_budget']:
                    try:
                        value = int(str(value).replace(',', '').replace('₩', '').strip())
                    except:
                        value = None
                
                setattr(employee, db_field, value)
    
    # _create_customer과 _update_customer 메서드는 더 이상 사용되지 않음 (table_processors.py의 CustomerProcessor로 대체됨)
    
    # _insert_sales_records 메서드는 더 이상 사용되지 않음 (table_processors.py의 SalesRecordProcessor로 대체됨)
    
    async def _get_or_create_customer_id(self, session: AsyncSession, row: Dict[str, Any], column_mapping: Dict[str, str]) -> int:
        """고객 ID를 안전하게 가져오거나 생성 (필수 값)"""
        try:
            # 고객명 추출
            customer_name = None
            if 'customer_name' in column_mapping and row.get(column_mapping['customer_name']):
                customer_name = str(row[column_mapping['customer_name']]).strip()
            
            if not customer_name or customer_name == 'nan':
                raise ValueError("고객명이 필수입니다.")
            
            # 기존 고객 확인 (고객명으로만 조회)
            result = await session.execute(
                select(Customer).filter(Customer.customer_name == customer_name)
            )
            existing_customer = result.scalar_one_or_none()
            
            if existing_customer:
                return existing_customer.customer_id
            else:
                # 새 고객 생성 (CustomerProcessor 사용)
                from .table_processors import get_table_processor
                processor = get_table_processor('customers', session)
                new_customer = await processor.create_new_record(row, column_mapping)
                new_customer.is_auto_created = True
                new_customer.approval_status = 'pending'
                session.add(new_customer)
                await session.flush()
                return new_customer.customer_id
                
        except Exception as e:
            logger.error(f"고객 ID 생성 중 오류: {e}")
            raise ValueError(f"고객 ID 생성 실패: {str(e)}")

    async def _get_or_create_employee_id(self, session: AsyncSession, row: Dict[str, Any], column_mapping: Dict[str, str]) -> int:
        """직원 ID를 안전하게 가져오거나 생성 (필수 값)"""
        try:
            # 사번 추출
            employee_number = None
            if 'employee_number' in column_mapping and row.get(column_mapping['employee_number']):
                employee_number = str(row[column_mapping['employee_number']]).strip()
            
            if not employee_number or employee_number == 'nan':
                raise ValueError("사번이 필수입니다.")
            
            # 기존 직원 확인 (사번으로만 조회)
            result = await session.execute(
                select(EmployeeInfo).filter(EmployeeInfo.employee_number == employee_number)
            )
            existing_employee = result.scalar_one_or_none()
            
            if existing_employee:
                return existing_employee.employee_info_id
            else:
                # 새 직원 생성
                new_employee = self._create_employee_info(row, column_mapping)
                new_employee.is_auto_created = True
                new_employee.approval_status = 'pending'
                session.add(new_employee)
                await session.flush()
                return new_employee.employee_info_id
                
        except Exception as e:
            logger.error(f"직원 ID 생성 중 오류: {e}")
            raise ValueError(f"직원 ID 생성 실패: {str(e)}")

    async def _get_or_create_product_id(self, session: AsyncSession, row: Dict[str, Any], column_mapping: Dict[str, str]) -> Optional[int]:
        """제품 ID를 안전하게 가져오거나 생성 (제품명으로만 조회)"""
        try:
            # 제품명 추출
            product_name = None
            if 'product_name' in column_mapping and row.get(column_mapping['product_name']):
                product_name = str(row[column_mapping['product_name']]).strip()
            
            if not product_name or product_name == 'nan':
                return None
            
            # 기존 제품 확인 (제품명으로만 조회)
            result = await session.execute(
                select(Product).filter(Product.product_name == product_name)
            )
            existing_product = result.scalar_one_or_none()
            
            if existing_product:
                return existing_product.product_id
            else:
                # 새 제품 생성 (ProductProcessor 사용)
                from .table_processors import get_table_processor
                processor = get_table_processor('products', session)
                new_product = await processor.create_new_record(row, column_mapping)
                new_product.is_auto_created = True
                new_product.approval_status = 'pending'
                session.add(new_product)
                await session.flush()
                return new_product.product_id
                
        except Exception as e:
            logger.error(f"제품 ID 생성 중 오류: {e}")
            return None

    # _insert_products, _create_product, _update_product 메서드는 더 이상 사용되지 않음 (table_processors.py의 ProductProcessor로 대체됨)
    # _insert_sales_records 메서드도 table_processors.py의 SalesRecordProcessor로 대체됨

    def _insert_interaction_logs(self, session: AsyncSession, table_data: List[Dict[str, Any]], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """상호작용 로그 삽입"""
        processed_count = 0
        
        try:
            for row in table_data:
                # 날짜 추출
                interaction_date = None
                if 'interacted_at' in column_mapping and row.get(column_mapping['interacted_at']):
                    interaction_date = self._parse_date(str(row[column_mapping['interacted_at']]))
                
                if not interaction_date:
                    interaction_date = datetime.now(timezone.utc)
                
                # 고객 ID 찾기 (customer_name으로만 조회 - address 정보가 없으므로)
                customer_id = None
                if 'customer_name' in column_mapping and row.get(column_mapping['customer_name']):
                    customer_name = str(row[column_mapping['customer_name']]).strip()
                    customer = session.query(Customer).filter(
                        Customer.customer_name == customer_name
                    ).first()
                    if customer:
                        customer_id = customer.customer_id
                
                if not customer_id:
                    logger.warning(f"고객을 찾을 수 없는 행 건너뜀: {row}")
                    continue
                
                # 기본 직원 찾기 (employee_info에서)
                default_employee_info = session.query(EmployeeInfo).first()
                if not default_employee_info:
                    logger.warning("기본 직원이 없어 상호작용 로그를 생성할 수 없습니다.")
                    continue
                
                # 상호작용 로그 생성
                new_interaction = InteractionLog(
                    employee_id=default_employee_info.employee_info_id,
                    customer_id=customer_id,
                    interaction_type=row.get(column_mapping.get('interaction_type', ''), '방문'),
                    summary=row.get(column_mapping.get('summary', ''), ''),
                    sentiment=row.get(column_mapping.get('sentiment', ''), 'neutral'),
                    compliance_risk=row.get(column_mapping.get('compliance_risk', ''), 'low'),
                    interacted_at=interaction_date
                )
                session.add(new_interaction)
                processed_count += 1
            
            return {
                'success': True,
                'message': f'상호작용 로그 삽입 완료: {processed_count}건 처리됨',
                'processed_count': processed_count
            }
            
        except SQLAlchemyError as e:
            logger.error(f"상호작용 로그 삽입 중 DB 오류: {e}")
            raise
    
    def _insert_assignment_map(self, session: AsyncSession, table_data: List[Dict[str, Any]], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """직원-고객 배정 관계 삽입 (사번으로만 직원 조회)"""
        processed_count = 0
        skipped_count = 0
        
        try:
            for row in table_data:
                # 사번과 고객명 추출
                employee_number = str(row[column_mapping['employee_id']]).strip() if 'employee_id' in column_mapping and row.get(column_mapping['employee_id']) else None
                customer_name = str(row[column_mapping['customer_id']]).strip() if 'customer_id' in column_mapping and row.get(column_mapping['customer_id']) else None
                
                if not employee_number or not customer_name:
                    logger.warning(f"사번 또는 고객명을 찾을 수 없는 행 건너뜀: {row}")
                    skipped_count += 1
                    continue
                
                # 직원 ID 찾기 (사번으로만 조회)
                employee_info = session.query(EmployeeInfo).filter(
                    EmployeeInfo.employee_number == employee_number
                ).first()
                
                # 고객 ID 찾기 (customer_name으로만 조회 - address 정보가 없으므로)
                customer = session.query(Customer).filter(
                    Customer.customer_name == customer_name
                ).first()
                
                if not employee_info or not customer:
                    logger.warning(f"직원 또는 고객을 찾을 수 없음: 사번={employee_number}, 고객명={customer_name}")
                    skipped_count += 1
                    continue
                
                # 기존 배정 관계 확인
                existing_assignment = session.query(AssignmentMap).filter(
                    AssignmentMap.employee_id == employee_info.employee_info_id,
                    AssignmentMap.customer_id == customer.customer_id
                ).first()
                
                if existing_assignment:
                    logger.info(f"배정 관계가 이미 존재함: {employee_info.name} (사번: {employee_number}) - {customer_name}")
                    skipped_count += 1
                else:
                    # 새 배정 관계 생성
                    new_assignment = AssignmentMap(
                        employee_id=employee_info.employee_info_id,
                        customer_id=customer.customer_id
                    )
                    session.add(new_assignment)
                    logger.info(f"새 배정 관계 생성: {employee_info.name} (사번: {employee_number}) - {customer_name}")
                
                processed_count += 1
            
            return {
                'success': True,
                'message': f'배정 관계 삽입 완료: {processed_count}건 처리됨, {skipped_count}건 건너뜀',
                'processed_count': processed_count,
                'skipped_count': skipped_count
            }
            
        except SQLAlchemyError as e:
            logger.error(f"배정 관계 삽입 중 DB 오류: {e}")
            raise
    
    def _insert_documents(self, session: AsyncSession, table_data: List[Dict[str, Any]], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """문서 메타데이터 삽입"""
        processed_count = 0
        
        try:
            for row in table_data:
                # 필수 필드 추출
                doc_title = str(row[column_mapping['doc_title']]).strip() if 'doc_title' in column_mapping and row.get(column_mapping['doc_title']) else None
                uploader_id = int(row[column_mapping['uploader_id']]) if 'uploader_id' in column_mapping and row.get(column_mapping['uploader_id']) else None
                file_path = str(row[column_mapping['file_path']]).strip() if 'file_path' in column_mapping and row.get(column_mapping['file_path']) else None
                
                if not doc_title or not uploader_id or not file_path:
                    logger.warning(f"필수 필드가 없는 행 건너뜀: {row}")
                    continue
                
                # 선택 필드 추출
                doc_type = str(row[column_mapping['doc_type']]).strip() if 'doc_type' in column_mapping and row.get(column_mapping['doc_type']) else None
                version = str(row[column_mapping['version']]).strip() if 'version' in column_mapping and row.get(column_mapping['version']) else None
                
                # 새 문서 생성
                new_document = Document(
                    doc_title=doc_title,
                    uploader_id=uploader_id,
                    file_path=file_path,
                    doc_type=doc_type,
                    version=version
                )
                session.add(new_document)
                logger.info(f"새 문서 메타데이터 생성: {doc_title}")
                
                processed_count += 1
            
            return {
                'success': True,
                'message': f'문서 메타데이터 삽입 완료: {processed_count}건 처리됨',
                'processed_count': processed_count
            }
            
        except SQLAlchemyError as e:
            logger.error(f"문서 메타데이터 삽입 중 DB 오류: {e}")
            raise
    
    def _insert_document_relations(self, session: AsyncSession, table_data: List[Dict[str, Any]], column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """문서 관계 삽입"""
        processed_count = 0
        
        try:
            for row in table_data:
                # 필수 필드 추출
                doc_id = int(row[column_mapping['doc_id']]) if 'doc_id' in column_mapping and row.get(column_mapping['doc_id']) else None
                related_entity_type = str(row[column_mapping['related_entity_type']]).strip() if 'related_entity_type' in column_mapping and row.get(column_mapping['related_entity_type']) else None
                related_entity_id = int(row[column_mapping['related_entity_id']]) if 'related_entity_id' in column_mapping and row.get(column_mapping['related_entity_id']) else None
                
                if not doc_id or not related_entity_type or not related_entity_id:
                    logger.warning(f"필수 필드가 없는 행 건너뜀: {row}")
                    continue
                
                # 선택 필드 추출
                confidence_score = int(row[column_mapping['confidence_score']]) if 'confidence_score' in column_mapping and row.get(column_mapping['confidence_score']) else 100
                
                # 기존 관계 확인
                existing_relation = session.query(DocumentRelation).filter(
                    DocumentRelation.doc_id == doc_id,
                    DocumentRelation.related_entity_type == related_entity_type,
                    DocumentRelation.related_entity_id == related_entity_id
                ).first()
                
                if existing_relation:
                    logger.info(f"문서 관계가 이미 존재함: doc_id={doc_id}, entity_type={related_entity_type}, entity_id={related_entity_id}")
                    continue
                
                # 새 문서 관계 생성
                new_relation = DocumentRelation(
                    doc_id=doc_id,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id,
                    confidence_score=confidence_score
                )
                session.add(new_relation)
                logger.info(f"새 문서 관계 생성: doc_id={doc_id}, entity_type={related_entity_type}, entity_id={related_entity_id}")
                
                processed_count += 1
            
            return {
                'success': True,
                'message': f'문서 관계 삽입 완료: {processed_count}건 처리됨',
                'processed_count': processed_count
            }
            
        except SQLAlchemyError as e:
            logger.error(f"문서 관계 삽입 중 DB 오류: {e}")
            raise
    

    

    
    def _log_consolidated_summary(self, all_results: List[Dict[str, Any]], document_id: Optional[int] = None):
        """모든 테이블 처리 완료 후 통합 요약 로그 출력"""
        if not all_results:
            return
        
        # 테이블별 단위 매핑
        table_units = {
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
            
            if processed > 0:
                summary_parts = []
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