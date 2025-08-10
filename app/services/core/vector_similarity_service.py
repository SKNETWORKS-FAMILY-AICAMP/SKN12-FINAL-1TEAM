"""
벡터 유사도 기반 테이블 매핑 서비스
pgvector를 사용하여 테이블 설명과 업로드된 문서의 유사도를 계산합니다.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, select

from app.models.table_descriptions import TableDescription
from app.services.external.openai_service import openai_service

logger = logging.getLogger(__name__)

class VectorSimilarityService:
    """벡터 유사도 기반 테이블 매핑 서비스"""
    
    def __init__(self):
        """초기화 - DB만을 단일 진실 소스로 사용"""
        pass
    
    # =============================================================================
    # 공통 유틸리티 메서드들
    # =============================================================================
    
    def _ensure_string_list(self, items: List[Any]) -> List[str]:
        """모든 아이템을 문자열로 변환하여 타입 안전성 보장"""
        return [str(item) for item in items]
    
    async def _create_embedding(self, text: str) -> List[float]:
        """임베딩 생성 (향후 캐싱 가능)"""
        return openai_service.create_embedding(text)
    
    async def _get_table_columns(self, session: Session, table_name: str) -> List[str]:
        """테이블의 컬럼 목록 조회"""
        try:
            stmt = select(TableDescription).where(TableDescription.table_name == table_name)
            result = await session.execute(stmt)
            table_desc = result.scalar_one_or_none()
            
            if not table_desc:
                logger.warning(f"테이블 설명을 찾을 수 없음: {table_name}")
                return []
            
            return self._ensure_string_list(table_desc.columns) if table_desc.columns else []
            
        except Exception as e:
            return self._handle_error(f"테이블 컬럼 조회 실패 ({table_name})", e, [])
    
    def _handle_error(self, message: str, error: Exception, default_return=None):
        """표준화된 에러 핸들링"""
        logger.error(f"{message}: {error}")
        logger.error(f"오류 타입: {type(error)}")
        logger.error(f"오류 상세: {str(error)}")
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        return default_return
    
    def _get_priority_boost(self, table_name: str) -> float:
        """기초 테이블 우선순위 가중치 반환"""
        # 기초 테이블들에 가중치 부여 (의존 관계 상 먼저 생성되어야 하는 테이블들)
        priority_weights = {
            'employee_info': 1.3,    # 담당자, 사번 정보 - 높은 우선순위
            'customers': 1.3,        # 거래처, ID 정보 - 높은 우선순위  
            'products': 1.3,         # 품목, 제품명 정보 - 높은 우선순위
            'sales_records': 1.0,    # 의존 테이블 - 기본 가중치
            'interaction_logs': 0.9, # 의존 테이블 - 낮은 우선순위
            'assignment_map': 0.9    # 의존 테이블 - 낮은 우선순위
        }
        return priority_weights.get(table_name, 1.0)
    
    async def update_table_description(self, session: Session, table_name: str, 
                                     description: str, columns: List[str], 
                                     sample_data: List[Any]) -> bool:
        """특정 테이블 설명을 업데이트 (수정/추가)"""
        try:
            # 기존 데이터 확인
            stmt = select(TableDescription).where(TableDescription.table_name == table_name)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            # 텍스트 생성 및 임베딩
            sample_data_str = self._ensure_string_list(sample_data)
            text_content = f"{description} 컬럼: {', '.join(columns)} 샘플: {', '.join(sample_data_str)}"
            embedding = await self._create_embedding(text_content)
            
            if existing:
                # 기존 데이터 업데이트
                existing.description = description
                existing.columns = columns
                existing.sample_data = sample_data
                existing.embedding = embedding
                logger.info(f"테이블 설명 업데이트: {table_name}")
            else:
                # 새 데이터 추가
                table_desc = TableDescription(
                    table_name=table_name,
                    description=description,
                    columns=columns,
                    sample_data=sample_data,
                    embedding=embedding
                )
                session.add(table_desc)
                logger.info(f"테이블 설명 추가: {table_name}")
            
            await session.commit()
            return True
            
        except Exception as e:
            await session.rollback()
            self._handle_error(f"테이블 설명 업데이트 실패 ({table_name})", e)
            return False
    
    async def delete_table_description(self, session: Session, table_name: str) -> bool:
        """특정 테이블 설명을 삭제"""
        try:
            stmt = select(TableDescription).where(TableDescription.table_name == table_name)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                session.delete(existing)
                await session.commit()
                logger.info(f"테이블 설명 삭제: {table_name}")
                return True
            else:
                logger.warning(f"삭제할 테이블 설명을 찾을 수 없음: {table_name}")
                return False
                
        except Exception as e:
            await session.rollback()
            self._handle_error(f"테이블 설명 삭제 실패 ({table_name})", e)
            return False
    
    async def refresh_all_table_descriptions(self, session: Session, table_descriptions: Dict[str, Any]) -> bool:
        """모든 테이블 설명을 새로 고침 (강제 업데이트)"""
        try:
            for table_name, info in table_descriptions.items():
                await self.update_table_description(
                    session, 
                    table_name, 
                    info['description'], 
                    info['columns'], 
                    info['sample_data']
                )
            
            logger.info("모든 테이블 설명 새로 고침 완료")
            return True
            
        except Exception as e:
            self._handle_error("테이블 설명 새로 고침 실패", e)
            return False
    
    async def initialize_table_descriptions_from_json(self, session: Session, table_descriptions: Dict[str, Any]):
        """JSON 데이터로부터 테이블 설명을 벡터 DB에 초기화 (외부에서 호출)"""
        try:
            for table_name, info in table_descriptions.items():
                # 기존 데이터 확인
                stmt = select(TableDescription).where(TableDescription.table_name == table_name)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    logger.info(f"테이블 설명 이미 존재: {table_name}")
                    continue
                
                # 텍스트 생성 (설명 + 컬럼 + 샘플 데이터)
                # sample_data의 모든 값을 문자열로 변환
                sample_data_str = []
                for item in info['sample_data']:
                    if isinstance(item, bool):
                        sample_data_str.append("true" if item else "false")
                    elif isinstance(item, (int, float)):
                        sample_data_str.append(str(item))
                    else:
                        sample_data_str.append(str(item))
                text_content = f"{info['description']} 컬럼: {', '.join(info['columns'])} 샘플: {', '.join(sample_data_str)}"
                
                # OpenAI 임베딩 생성
                embedding = await self._create_embedding(text_content)
                
                # 벡터 저장
                table_desc = TableDescription(
                    table_name=table_name,
                    description=info['description'],
                    columns=info['columns'],
                    sample_data=info['sample_data'],
                    embedding=embedding
                )
                
                session.add(table_desc)
                logger.info(f"테이블 설명 벡터 저장: {table_name}")
            
            await session.commit()
            logger.info("테이블 설명 벡터 초기화 완료")
            
        except Exception as e:
            await session.rollback()
            self._handle_error("테이블 설명 벡터 초기화 실패", e)
            raise
    
    async def find_relevant_tables(self, session: Session, columns: List[str], 
                                 similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        try:
            # 모든 컬럼명을 문자열로 변환 (안전장치)
            columns = self._ensure_string_list(columns)
            # 컬럼 정보를 텍스트로 변환
            columns_text = ", ".join(columns)
            logger.info(f"🔍 벡터 검색 입력: '{columns_text}' (임계값: {similarity_threshold})")
            
            # OpenAI 임베딩 생성
            query_embedding = await self._create_embedding(columns_text)
            logger.info(f"🔍 임베딩 생성 완료: 차원 {len(query_embedding)}")
            
            # 벡터 유사도 검색 (임계값 이상인 모든 테이블)
            query = text("""
                SELECT table_name, description, columns, sample_data,
                       1 - (embedding <=> :embedding) as similarity
                FROM table_descriptions 
                WHERE 1 - (embedding <=> :embedding) >= :threshold
                ORDER BY embedding <=> :embedding
            """)
            
            # 벡터를 pgvector 형식의 문자열로 변환
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            logger.info(f"🔍 벡터 문자열 길이: {len(embedding_str)} chars")
            
            result = await session.execute(query, {
                'embedding': embedding_str,
                'threshold': similarity_threshold
            })
            results = result.fetchall()
            logger.info(f"🔍 쿼리 결과: {len(results)}개 행 반환")
            
            relevant_tables = []
            for result in results:
                # 컬럼명을 모두 문자열로 변환
                columns_str = self._ensure_string_list(result.columns) if result.columns else []
                
                similarity_score = float(result.similarity)
                
                # 기초 테이블 우선순위 가중치 적용
                priority_boost = self._get_priority_boost(result.table_name)
                adjusted_similarity = similarity_score * priority_boost
                
                logger.info(f"🔍 테이블 '{result.table_name}' 유사도: {similarity_score:.3f} (가중치: {priority_boost}) → 조정된 유사도: {adjusted_similarity:.3f}")
                
                relevant_tables.append({
                    'table_name': result.table_name,
                    'description': result.description,
                    'columns': columns_str,
                    'sample_data': result.sample_data,
                    'similarity': adjusted_similarity  # 조정된 유사도 사용
                })
            
            logger.info(f"관련 테이블 {len(relevant_tables)}개 발견: {[t['table_name'] for t in relevant_tables]}")
            
            # 디버깅을 위한 로그 추가
            for table in relevant_tables:
                logger.debug(f"테이블 {table['table_name']}의 컬럼들: {table['columns']}")
                logger.debug(f"컬럼 타입들: {[type(col) for col in table['columns']]}")
            
            return relevant_tables
                
        except Exception as e:
            return self._handle_error("관련 테이블 검색 실패", e, [])
    
    async def analyze_multi_table_capability(self, session: Session, columns: List[str], 
                                           sample_data: List[Dict] = None) -> Dict[str, Any]:
        """업로드된 컬럼들로 어떤 테이블들에 데이터를 만들 수 있는지 분석"""
        try:
            # 1단계: 관련 테이블들 찾기
            relevant_tables = await self.find_relevant_tables(session, columns, similarity_threshold=0.3)
            
            if not relevant_tables:
                logger.warning("관련된 테이블을 찾을 수 없음")
                return {
                    'success': False,
                    'message': '관련된 테이블을 찾을 수 없습니다.',
                    'table_mappings': []
                }
            
            # 2단계: 유사도 기준으로 정렬 (가중치가 적용된 similarity 기준)
            relevant_tables.sort(key=lambda x: x['similarity'], reverse=True)
            sorted_tables = [(t['table_name'], f"{t['similarity']:.3f}") for t in relevant_tables]
            logger.info(f"🔄 유사도 기준 정렬 완료: {sorted_tables}")
            
            # 3단계: 관련 테이블 정보를 LLM에 전달 (상위 5개까지, 컬럼 매핑 없이)
            table_mappings = []
            for table_info in relevant_tables[:5]:  # 상위 5개만 분석
                table_name = table_info['table_name']
                table_columns = table_info['columns']
                
                logger.info(f"🔍 {table_name} LLM 분석 대상으로 추가 (유사도: {table_info['similarity']:.3f})")
                
                # 컬럼 매핑 없이 테이블 정보만 포함 (LLM이 직접 판단)
                table_mappings.append({
                    'table_name': table_name,
                    'description': table_info['description'],
                    'similarity': table_info['similarity'],
                    'columns': table_columns,
                    'sample_data': table_info.get('sample_data', [])
                })

            logger.info(f"📊 최종 테이블 매핑 순서: {table_mappings}")

            return {
                'success': True,
                'table_mappings': table_mappings,
                'total_tables': len(table_mappings)
            }
            
        except Exception as e:
            return self._handle_error("다중 테이블 분석 실패", e, {
                'success': False,
                'message': f'다중 테이블 분석 중 오류: {str(e)}',
                'table_mappings': []
            })
    
    async def find_column_mapping_for_table(self, session: Session, table_name: str, 
                                          uploaded_columns: List[str], 
                                          target_columns: List[str]) -> Dict[str, str]:
        """특정 테이블에 대한 컬럼 매핑 찾기 (통합된 메서드 호출)"""
        return await self.find_column_mapping(session, table_name, uploaded_columns, target_columns)
    
    def _create_prompt_info(self, table_mappings: List[Dict], uploaded_columns: List[str]) -> Dict[str, Any]:
        """LLM 프롬프트 구성용 정보 생성"""
        prompt_info = {
            'uploaded_columns': uploaded_columns,
            'relevant_tables': [],
            'total_tables': len(table_mappings)
        }
        
        for mapping in table_mappings:
            table_info = {
                'table_name': mapping['table_name'],
                'description': mapping['description'],
                'similarity': mapping['similarity'],
                'mapped_columns': mapping['mapped_columns'],
                'unmapped_columns': mapping['unmapped_columns']
            }
            prompt_info['relevant_tables'].append(table_info)
        
        return prompt_info
    
    async def find_similar_table(self, session: Session, columns: List[str], sample_data: List[Dict] = None) -> Tuple[str, float]:
        """업로드된 컬럼과 가장 유사한 테이블 찾기 (기존 메서드 - 호환성 유지)"""
        try:
            # 모든 컬럼명을 문자열로 변환 (안전장치)
            columns = self._ensure_string_list(columns)
            # 컬럼 정보를 텍스트로 변환
            columns_text = ", ".join(columns)
            
            # 샘플 데이터가 있으면 추가
            if sample_data:
                sample_text = " 샘플 데이터: " + str(sample_data)
                columns_text += sample_text
            
            # OpenAI 임베딩 생성
            query_embedding = await self._create_embedding(columns_text)
            
            # 벡터 유사도 검색 (코사인 유사도)
            query = text("""
                SELECT table_name, description, 
                       1 - (embedding <=> :embedding) as similarity
                FROM table_descriptions 
                ORDER BY embedding <=> :embedding
                LIMIT 1
            """)
            
            # 벡터를 pgvector 형식의 문자열로 변환
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            exec_result = await session.execute(query, {'embedding': embedding_str})
            result = exec_result.first()
            
            if result:
                table_name = result.table_name
                similarity = float(result.similarity)
                logger.info(f"벡터 유사도 검색 결과: {table_name} (유사도: {similarity:.3f})")
                return table_name, similarity
            else:
                logger.warning("유사한 테이블을 찾을 수 없음")
                return None, 0.0
                
        except Exception as e:
            return self._handle_error("벡터 유사도 검색 실패", e, (None, 0.0))
    
    async def find_column_mapping(self, session: Session, target_table: str, 
                                uploaded_columns: List[str], 
                                target_columns: Optional[List[str]] = None) -> Dict[str, str]:
        """통합된 컬럼 매핑 찾기 메서드"""
        try:
            # 모든 업로드된 컬럼명을 문자열로 변환 (안전장치)
            uploaded_columns = self._ensure_string_list(uploaded_columns)
            
            # target_columns가 제공되지 않은 경우 DB에서 가져오기
            if target_columns is None:
                target_columns = await self._get_table_columns(session, target_table)
                if not target_columns:
                    return {}
            else:
                target_columns = self._ensure_string_list(target_columns)
            
            # 컬럼 매핑 수행
            column_mapping = {}
            
            for uploaded_col in uploaded_columns:
                best_match = None
                best_similarity = 0.0
                
                for target_col in target_columns:
                    similarity = self._calculate_column_similarity(uploaded_col, target_col)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = target_col
                
                # 임계값 이상인 경우만 매핑
                if best_similarity > 0.1:  # 10% 이상 유사한 경우 (낮춤)
                    column_mapping[best_match] = uploaded_col
                    logger.info(f"컬럼 매핑 ({target_table}): {uploaded_col} → {best_match} (유사도: {best_similarity:.3f})")
            
            return column_mapping
            
        except Exception as e:
            return self._handle_error(f"컬럼 매핑 실패 ({target_table})", e, {})
    
    def _calculate_column_similarity(self, col1: str, col2: str) -> float:
        """컬럼명 유사도 계산 (간단한 문자열 유사도)"""
        # 입력값을 문자열로 변환
        col1_lower = str(col1).lower()
        col2_lower = str(col2).lower()
        
        # 정확히 일치
        if col1_lower == col2_lower:
            return 1.0
        
        # 포함 관계
        if col1_lower in col2_lower or col2_lower in col1_lower:
            return 0.8
        
        # 공통 단어 수 계산
        words1 = set(col1_lower.split('_'))
        words2 = set(col2_lower.split('_'))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union

# 싱글턴 인스턴스
vector_similarity_service = VectorSimilarityService() 