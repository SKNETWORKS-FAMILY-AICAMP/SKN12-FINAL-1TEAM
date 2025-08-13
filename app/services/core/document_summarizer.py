"""
문서 요약 생성 서비스
OpenAI GPT를 사용하여 문서 내용을 요약합니다.
"""

import logging
from typing import Optional, List, Dict, Any
from app.services.external.openai_service import openai_service

logger = logging.getLogger(__name__)

class DocumentSummarizer:
    """문서 요약 생성기"""
    
    def __init__(self):
        self.max_text_length = 5000  # 요약할 텍스트 최대 길이
        self.summary_length = 300  # 목표 요약 길이 (한글 기준)
    
    def summarize_text_document(self, text: str, doc_title: str, doc_type: str) -> Optional[str]:
        """
        텍스트 문서를 요약합니다.
        
        Args:
            text: 문서 전체 텍스트
            doc_title: 문서 제목
            doc_type: 문서 타입 (regulation, law, report 등)
            
        Returns:
            Optional[str]: 요약 텍스트 (실패 시 None)
        """
        try:
            if not text or len(text.strip()) < 50:
                logger.warning(f"문서 텍스트가 너무 짧습니다: {doc_title}")
                return None
            
            # 텍스트 길이 제한
            truncated_text = text[:self.max_text_length] if len(text) > self.max_text_length else text
            
            # 문서 타입별 프롬프트 조정
            doc_type_context = self._get_doc_type_context(doc_type)
            
            # 요약 프롬프트 생성
            prompt = self._create_text_summary_prompt(truncated_text, doc_title, doc_type_context)
            
            # OpenAI API 호출
            response = openai_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": "당신은 전문적인 문서 요약 전문가입니다. 핵심 내용을 간결하고 명확하게 요약해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            if response and response.strip():
                summary = response.strip()
                logger.info(f"텍스트 문서 요약 생성 완료: {doc_title} (길이: {len(summary)}자)")
                return summary
            else:
                logger.warning(f"요약 생성 응답이 비어있음: {doc_title}")
                return None
                
        except Exception as e:
            logger.error(f"텍스트 문서 요약 생성 실패 ({doc_title}): {e}")
            return None
    
    def summarize_table_document(self, table_data: List[Dict], doc_title: str, doc_type: str) -> Optional[str]:
        """
        테이블 문서를 요약합니다.
        
        Args:
            table_data: 테이블 데이터 (레코드 리스트)
            doc_title: 문서 제목
            doc_type: 문서 타입 (text2sql_sales_records 등)
            
        Returns:
            Optional[str]: 요약 텍스트 (실패 시 None)
        """
        try:
            if not table_data:
                logger.warning(f"테이블 데이터가 비어있습니다: {doc_title}")
                return None
            
            # 테이블 데이터 분석
            num_rows = len(table_data)
            columns = list(table_data[0].keys()) if table_data else []
            
            # 샘플 데이터 추출 (최대 10개 행)
            sample_data = table_data[:10] if len(table_data) > 10 else table_data
            
            # 요약 프롬프트 생성
            prompt = self._create_table_summary_prompt(
                sample_data=sample_data,
                num_rows=num_rows,
                columns=columns,
                doc_title=doc_title,
                doc_type=doc_type
            )
            
            # OpenAI API 호출
            response = openai_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": "당신은 데이터 분석 전문가입니다. 테이블 데이터의 구조와 내용을 간결하게 요약해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            if response and response.strip():
                summary = response.strip()
                logger.info(f"테이블 문서 요약 생성 완료: {doc_title} (길이: {len(summary)}자)")
                return summary
            else:
                logger.warning(f"요약 생성 응답이 비어있음: {doc_title}")
                return None
                
        except Exception as e:
            logger.error(f"테이블 문서 요약 생성 실패 ({doc_title}): {e}")
            return None
    
    def _get_doc_type_context(self, doc_type: str) -> str:
        """문서 타입에 따른 컨텍스트 정보 반환"""
        contexts = {
            "regulation": "회사 내부 규정 문서",
            "law": "법률 및 법령 문서",
            "report": "분석 보고서",
            "performance_data": "실적 데이터",
            "customer_info": "거래처 정보",
            "hr_data": "인사 자료"
        }
        
        # text2sql_ 접두사 처리
        if doc_type and doc_type.startswith("text2sql_"):
            base_type = doc_type.replace("text2sql_", "")
            if base_type == "sales_records":
                return "매출 실적 데이터"
            elif base_type == "employee_performance":
                return "직원 성과 목표 데이터"
            elif base_type == "customer_monthly_status":
                return "거래처 월간 상태 데이터"
            else:
                return "업무 데이터"
        
        return contexts.get(doc_type, "일반 문서")
    
    def _create_text_summary_prompt(self, text: str, doc_title: str, doc_type_context: str) -> str:
        """텍스트 문서 요약을 위한 프롬프트 생성"""
        return f"""
다음 {doc_type_context}를 200-300자 내외로 요약해주세요.

문서 제목: {doc_title}
문서 내용: {text}

요약 작성 지침:
1. 문서의 핵심 목적과 주요 내용을 포함
2. 중요한 정책, 규정, 또는 데이터 포인트 언급
3. 구체적이고 명확한 한국어로 작성
4. 불필요한 수식어나 반복 제거
5. 비즈니스 관점에서 중요한 정보 위주로 요약

요약:
"""
    
    def _create_table_summary_prompt(self, sample_data: List[Dict], num_rows: int, 
                                    columns: List[str], doc_title: str, doc_type: str) -> str:
        """테이블 문서 요약을 위한 프롬프트 생성"""
        
        # 샘플 데이터를 문자열로 변환
        sample_str = "\n".join([str(row) for row in sample_data[:5]])
        
        return f"""
다음 테이블 데이터를 200-300자 내외로 요약해주세요.

문서 제목: {doc_title}
데이터 타입: {self._get_doc_type_context(doc_type)}
전체 행 수: {num_rows}개
컬럼 목록: {', '.join(columns)}

샘플 데이터:
{sample_str}

요약 작성 지침:
1. 데이터의 유형과 목적 설명
2. 주요 컬럼과 데이터 범위 언급
3. 데이터의 시간적 범위나 특징 포함 (있는 경우)
4. 비즈니스 관점에서의 활용 가능성 언급
5. 구체적인 수치나 통계 포함 (가능한 경우)

요약:
"""

# 싱글턴 인스턴스
document_summarizer = DocumentSummarizer()