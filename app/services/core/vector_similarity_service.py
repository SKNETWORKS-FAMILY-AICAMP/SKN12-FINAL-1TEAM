"""
벡터 유사도 기반 테이블 매핑 서비스
pgvector를 사용하여 테이블 설명과 업로드된 문서의 유사도를 계산합니다.
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np

from app.models.table_descriptions import TableDescription
from app.services.external.openai_service import openai_service

logger = logging.getLogger(__name__)

class VectorSimilarityService:
    """벡터 유사도 기반 테이블 매핑 서비스"""
    
    def __init__(self):
        """초기화"""
        self.table_descriptions = self._load_table_descriptions()
    
    def _load_table_descriptions(self) -> Dict[str, Any]:
        """테이블 설명 JSON 파일 로드"""
        try:
            # 현재 파일의 디렉토리를 기준으로 상대 경로 계산
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, '..', '..', 'config', 'table_descriptions.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                table_descriptions = json.load(f)
            
            logger.info(f"테이블 설명 로드 완료: {len(table_descriptions)}개 테이블")
            return table_descriptions
            
        except FileNotFoundError:
            logger.error(f"테이블 설명 파일을 찾을 수 없음: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"테이블 설명 JSON 파싱 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"테이블 설명 로드 중 오류: {e}")
            raise
    
    def reload_table_descriptions(self):
        """테이블 설명을 다시 로드 (런타임 중 설정 변경 시 사용)"""
        try:
            self.table_descriptions = self._load_table_descriptions()
            logger.info("테이블 설명 리로드 완료")
        except Exception as e:
            logger.error(f"테이블 설명 리로드 실패: {e}")
            raise
    
    async def initialize_table_descriptions(self, session: Session):
        """테이블 설명을 벡터 DB에 초기화"""
        try:
            for table_name, info in self.table_descriptions.items():
                # 기존 데이터 확인
                existing = session.query(TableDescription).filter(
                    TableDescription.table_name == table_name
                ).first()
                
                if existing:
                    logger.info(f"테이블 설명 이미 존재: {table_name}")
                    continue
                
                # 텍스트 생성 (설명 + 컬럼 + 샘플 데이터)
                # sample_data의 모든 값을 문자열로 변환
                sample_data_str = [str(item) for item in info['sample_data']]
                text_content = f"{info['description']} 컬럼: {', '.join(info['columns'])} 샘플: {', '.join(sample_data_str)}"
                
                # OpenAI 임베딩 생성
                embedding = openai_service.create_embedding(text_content)
                
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
            
            session.commit()
            logger.info("테이블 설명 벡터 초기화 완료")
            
        except Exception as e:
            logger.error(f"테이블 설명 벡터 초기화 실패: {e}")
            session.rollback()
            raise
    
    async def find_relevant_tables(self, session: Session, columns: List[str], 
                                 similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """업로드된 컬럼과 관련된 테이블들을 찾아서 반환"""
        try:
            # 컬럼 정보를 텍스트로 변환
            columns_text = ", ".join(columns)
            
            # OpenAI 임베딩 생성
            query_embedding = openai_service.create_embedding(columns_text)
            
            # 벡터 유사도 검색 (임계값 이상인 모든 테이블)
            query = text("""
                SELECT table_name, description, columns, sample_data,
                       1 - (embedding <=> :embedding) as similarity
                FROM table_descriptions 
                WHERE 1 - (embedding <=> :embedding) >= :threshold
                ORDER BY embedding <=> :embedding
            """)
            
            results = session.execute(query, {
                'embedding': query_embedding,
                'threshold': similarity_threshold
            }).fetchall()
            
            relevant_tables = []
            for result in results:
                relevant_tables.append({
                    'table_name': result.table_name,
                    'description': result.description,
                    'columns': result.columns,
                    'sample_data': result.sample_data,
                    'similarity': float(result.similarity)
                })
            
            logger.info(f"관련 테이블 {len(relevant_tables)}개 발견: {[t['table_name'] for t in relevant_tables]}")
            return relevant_tables
                
        except Exception as e:
            logger.error(f"관련 테이블 검색 실패: {e}")
            return []
    
    async def analyze_multi_table_capability(self, session: Session, columns: List[str], 
                                           sample_data: List[Dict] = None) -> Dict[str, Any]:
        """업로드된 컬럼들로 어떤 테이블들에 데이터를 만들 수 있는지 분석"""
        try:
            # 1단계: 관련 테이블들 찾기
            relevant_tables = await self.find_relevant_tables(session, columns, similarity_threshold=0.2)
            
            if not relevant_tables:
                logger.warning("관련된 테이블을 찾을 수 없음")
                return {
                    'success': False,
                    'message': '관련된 테이블을 찾을 수 없습니다.',
                    'table_mappings': []
                }
            
            # 2단계: 각 테이블별 컬럼 매핑 분석
            table_mappings = []
            for table_info in relevant_tables:
                table_name = table_info['table_name']
                table_columns = table_info['columns']
                
                # 컬럼 매핑 찾기
                column_mapping = await self.find_column_mapping_for_table(
                    session, table_name, columns, table_columns
                )
                
                # 매핑된 컬럼이 있는 경우만 포함
                if column_mapping:
                    table_mappings.append({
                        'table_name': table_name,
                        'description': table_info['description'],
                        'similarity': table_info['similarity'],
                        'column_mapping': column_mapping,
                        'mapped_columns': list(column_mapping.keys()),
                        'unmapped_columns': [col for col in table_columns if col not in column_mapping]
                    })
            
            # 3단계: 테이블 간 의존성 분석
            dependency_analysis = self._analyze_table_dependencies(table_mappings)
            
            # 4단계: 효율적인 프롬프트 구성용 정보
            prompt_info = self._create_prompt_info(table_mappings, columns)
            
            return {
                'success': True,
                'table_mappings': table_mappings,
                'dependency_analysis': dependency_analysis,
                'prompt_info': prompt_info,
                'total_tables': len(table_mappings)
            }
            
        except Exception as e:
            logger.error(f"다중 테이블 분석 실패: {e}")
            return {
                'success': False,
                'message': f'다중 테이블 분석 중 오류: {str(e)}',
                'table_mappings': []
            }
    
    async def find_column_mapping_for_table(self, session: Session, table_name: str, 
                                          uploaded_columns: List[str], 
                                          target_columns: List[str]) -> Dict[str, str]:
        """특정 테이블에 대한 컬럼 매핑 찾기"""
        try:
            column_mapping = {}
            
            for uploaded_col in uploaded_columns:
                best_match = None
                best_similarity = 0.0
                
                for target_col in target_columns:
                    # 컬럼명 유사도 계산
                    similarity = self._calculate_column_similarity(uploaded_col, target_col)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = target_col
                
                # 임계값 이상인 경우만 매핑
                if best_similarity > 0.3:  # 30% 이상 유사한 경우
                    column_mapping[best_match] = uploaded_col
                    logger.info(f"컬럼 매핑 ({table_name}): {uploaded_col} → {best_match} (유사도: {best_similarity:.3f})")
            
            return column_mapping
            
        except Exception as e:
            logger.error(f"컬럼 매핑 실패 ({table_name}): {e}")
            return {}
    
    def _analyze_table_dependencies(self, table_mappings: List[Dict]) -> Dict[str, Any]:
        """테이블 간 의존성 분석"""
        dependencies = {
            'primary_tables': [],  # 독립적으로 생성 가능한 테이블
            'dependent_tables': [],  # 다른 테이블에 의존하는 테이블
            'creation_order': []  # 생성 순서 제안
        }
        
        # 테이블 의존성 정의
        table_deps = {
            'sales_records': ['employee_info', 'customers', 'products'],
            'interaction_logs': ['employee_info', 'customers'],
            'assignment_map': ['employee_info', 'customers']
        }
        
        # 독립 테이블들
        independent_tables = ['employee_info', 'customers', 'products']
        
        for mapping in table_mappings:
            table_name = mapping['table_name']
            
            if table_name in independent_tables:
                dependencies['primary_tables'].append(table_name)
            else:
                dependencies['dependent_tables'].append(table_name)
        
        # 생성 순서 제안
        dependencies['creation_order'] = dependencies['primary_tables'] + dependencies['dependent_tables']
        
        return dependencies
    
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
            # 컬럼 정보를 텍스트로 변환
            columns_text = ", ".join(columns)
            
            # 샘플 데이터가 있으면 추가
            if sample_data:
                sample_text = " 샘플 데이터: " + json.dumps(sample_data, ensure_ascii=False)
                columns_text += sample_text
            
            # OpenAI 임베딩 생성
            query_embedding = openai_service.create_embedding(columns_text)
            
            # 벡터 유사도 검색 (코사인 유사도)
            query = text("""
                SELECT table_name, description, 
                       1 - (embedding <=> :embedding) as similarity
                FROM table_descriptions 
                ORDER BY embedding <=> :embedding
                LIMIT 1
            """)
            
            result = session.execute(query, {'embedding': query_embedding}).first()
            
            if result:
                table_name = result.table_name
                similarity = float(result.similarity)
                logger.info(f"벡터 유사도 검색 결과: {table_name} (유사도: {similarity:.3f})")
                return table_name, similarity
            else:
                logger.warning("유사한 테이블을 찾을 수 없음")
                return None, 0.0
                
        except Exception as e:
            logger.error(f"벡터 유사도 검색 실패: {e}")
            return None, 0.0
    
    async def find_column_mapping(self, session: Session, target_table: str, uploaded_columns: List[str]) -> Dict[str, str]:
        """컬럼 매핑 찾기 (기존 메서드 - 호환성 유지)"""
        try:
            # 대상 테이블의 설명 가져오기
            table_desc = session.query(TableDescription).filter(
                TableDescription.table_name == target_table
            ).first()
            
            if not table_desc:
                logger.warning(f"테이블 설명을 찾을 수 없음: {target_table}")
                return {}
            
            # 각 업로드된 컬럼에 대해 가장 유사한 컬럼 찾기
            column_mapping = {}
            
            for uploaded_col in uploaded_columns:
                best_match = None
                best_similarity = 0.0
                
                for target_col in table_desc.columns:
                    # 컬럼명 유사도 계산 (간단한 문자열 유사도)
                    similarity = self._calculate_column_similarity(uploaded_col, target_col)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = target_col
                
                # 임계값 이상인 경우만 매핑
                if best_similarity > 0.3:  # 30% 이상 유사한 경우
                    column_mapping[best_match] = uploaded_col
                    logger.info(f"컬럼 매핑: {uploaded_col} → {best_match} (유사도: {best_similarity:.3f})")
            
            return column_mapping
            
        except Exception as e:
            logger.error(f"컬럼 매핑 실패: {e}")
            return {}
    
    def _calculate_column_similarity(self, col1: str, col2: str) -> float:
        """컬럼명 유사도 계산 (간단한 문자열 유사도)"""
        col1_lower = col1.lower()
        col2_lower = col2.lower()
        
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