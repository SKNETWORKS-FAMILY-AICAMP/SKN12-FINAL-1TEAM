"""
문서 타입 자동 분석 서비스
LLM을 사용하여 문서 내용을 분석하여 자동으로 타입을 분류합니다.
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from enum import Enum
from app.services.external.openai_service import openai_service

logger = logging.getLogger(__name__)

class DocumentCategory(Enum):
    """문서 카테고리"""
    TABLE = "table"
    TEXT = "text"

class DocumentType(Enum):
    """문서 타입"""
    # 테이블 문서
    PERFORMANCE_DATA = "performance_data"    # 실적 자료
    CUSTOMER_INFO = "customer_info"          # 거래처 정보
    HR_DATA = "hr_data"                      # 인사 자료
    BRANCH_TARGET = "branch_target"          # 지점별 목표
    
    # 텍스트 문서
    REGULATION = "regulation"                # 내부 규정
    LAW = "law"                              # 법률
    REPORT = "report"                        # 보고서

class DocumentAnalyzer:
    """문서 타입 자동 분석기"""
    
    def __init__(self):
        # 지원하는 파일 확장자
        self.supported_extensions = {
            "text": [".txt", ".docx", ".pdf"],
            "table": [".csv", ".xlsx", ".xls"]
        }
    
    def analyze_document(self, text: str, filename: str) -> str:
        """
        LLM을 사용하여 문서를 분석하여 타입을 자동으로 분류합니다.
        
        Args:
            text: 문서 내용
            filename: 파일명
            
        Returns:
            문서 타입 문자열 (doc_type에 저장될 값)
        """
        try:
            logger.info(f"LLM 기반 문서 분석 시작: {filename}")
            
            # 1. 파일 확장자 확인
            file_extension = self._get_file_extension(filename)
            
            if not file_extension:
                logger.warning(f"지원하지 않는 파일 형식: {filename}")
                return DocumentType.REPORT.value  # 기본값
            
            # 2. LLM 기반 문서 분류
            if file_extension in self.supported_extensions["table"]:
                # 테이블 문서 분석
                return self._analyze_table_document_with_llm(text, filename)
            else:
                # 텍스트 문서 분석
                return self._analyze_text_document_with_llm(text, filename)
            
        except Exception as e:
            logger.error(f"LLM 문서 분석 중 오류 발생: {e}")
            return DocumentType.REPORT.value  # 기본값
    
    def _get_file_extension(self, filename: str) -> str:
        """파일 확장자를 추출합니다."""
        if not filename:
            return ""
        
        # 파일명에서 확장자 추출
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return ""
    
    def _analyze_table_document_with_llm(self, text: str, filename: str) -> str:
        """LLM을 사용한 테이블 문서 분석"""
        logger.info("LLM 기반 테이블 문서 분석 시작")
        
        try:
            # LLM 프롬프트 생성
            prompt = self._create_table_document_prompt(text, filename)
            
            # LLM 호출
            response = openai_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": "당신은 문서 분류 전문가입니다. 주어진 문서를 정확히 분류해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            if response and response.strip():
                # 응답에서 문서 타입 추출
                doc_type = self._extract_document_type_from_llm_response(response)
                logger.info(f"LLM 테이블 문서 분류 결과: {doc_type}")
                return doc_type
            else:
                logger.warning("LLM 응답이 비어있음, 기본값 사용")
                return DocumentType.PERFORMANCE_DATA.value
                
        except Exception as e:
            logger.error(f"LLM 테이블 문서 분석 실패: {e}")
            return DocumentType.PERFORMANCE_DATA.value  # 기본값
    
    def _analyze_text_document_with_llm(self, text: str, filename: str) -> str:
        """LLM을 사용한 텍스트 문서 분석"""
        logger.info("LLM 기반 텍스트 문서 분석 시작")
        
        try:
            # LLM 프롬프트 생성
            prompt = self._create_text_document_prompt(text, filename)
            
            # LLM 호출
            response = openai_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": "당신은 문서 분류 전문가입니다. 주어진 문서를 정확히 분류해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            if response and response.strip():
                # 응답에서 문서 타입 추출
                doc_type = self._extract_document_type_from_llm_response(response)
                logger.info(f"LLM 텍스트 문서 분류 결과: {doc_type}")
                return doc_type
            else:
                logger.warning("LLM 응답이 비어있음, 기본값 사용")
                return DocumentType.REPORT.value
                
        except Exception as e:
            logger.error(f"LLM 텍스트 문서 분석 실패: {e}")
            return DocumentType.REPORT.value  # 기본값
    
    def _create_table_document_prompt(self, text: str, filename: str) -> str:
        """테이블 문서 분류를 위한 LLM 프롬프트 생성"""
        return f"""
다음 테이블 데이터를 분석하여 문서 타입을 분류해주세요.

파일명: {filename}
데이터 내용: {text[:2000]}  # 처음 2000자만 사용

분류 가능한 타입:
1. performance_data - 실적 자료 (매출, 판매, 성과 관련 데이터)
2. customer_info - 거래처 정보 (고객, 병원, 의료기관 정보)
3. hr_data - 인사 자료 (직원, 인사, 조직 관련 데이터)

분류 기준:
- performance_data: 매출액, 판매량, 실적, 성과, 매출 관련 컬럼이 있는 경우
- customer_info: 고객명, 병원명, 의료기관, 환자수, 주소 등이 있는 경우
- hr_data: 사번, 직원명, 부서, 직급, 급여, 인사 관련 데이터가 있는 경우

응답 형식: 정확히 다음 중 하나만 답변해주세요.
- performance_data
- customer_info
- hr_data

분류 결과:
"""
    
    def _create_text_document_prompt(self, text: str, filename: str) -> str:
        """텍스트 문서 분류를 위한 LLM 프롬프트 생성"""
        return f"""
다음 텍스트 문서를 분석하여 문서 타입을 분류해주세요.

파일명: {filename}
문서 내용: {text[:2000]}  # 처음 2000자만 사용

분류 가능한 타입:
1. regulation - 내부 규정 (회사 규정, 정책, 지침, 규칙)
2. law - 법률 (법령, 시행령, 시행규칙, 조례, 법규)
3. report - 보고서 (분석 보고서, 현황 보고서, 결과 보고서)

분류 기준:
- regulation: "규정", "정책", "지침", "제1조", "제2조", "목적", "정의", "사규", "내규" 등이 포함된 경우
- law: "법", "시행령", "시행규칙", "조례", "법령", "법률", "대통령령", "부령", "시행" 등이 포함된 경우
- report: "보고서", "분석", "현황", "결과", "통계", "시장", "업계", "동향" 등이 포함된 경우

응답 형식: 정확히 다음 중 하나만 답변해주세요.
- regulation
- law
- report

분류 결과:
"""
    
    def _extract_document_type_from_llm_response(self, response: str) -> str:
        """LLM 응답에서 문서 타입을 추출"""
        response = response.strip().lower()
        
        # 지원하는 문서 타입들
        valid_types = [
            DocumentType.PERFORMANCE_DATA.value,
            DocumentType.CUSTOMER_INFO.value,
            DocumentType.HR_DATA.value,
            DocumentType.REGULATION.value,
            DocumentType.LAW.value,
            DocumentType.REPORT.value
        ]
        
        # 응답에서 문서 타입 찾기
        for doc_type in valid_types:
            if doc_type in response:
                return doc_type
        
        # 기본값 반환
        logger.warning(f"LLM 응답에서 문서 타입을 찾을 수 없음: {response}")
        return DocumentType.REPORT.value
    
    def get_chunking_type(self, document_type: str) -> str:
        """
        문서 타입에 따른 청킹 타입을 반환합니다.
        
        Args:
            document_type: 문서 타입
            
        Returns:
            청킹 타입 ("regulation" 또는 "report")
        """
        if document_type in [DocumentType.REGULATION.value, DocumentType.LAW.value]:
            return "regulation"
        else:
            return "report"
    
    def is_supported_file(self, filename: str) -> bool:
        """
        파일이 지원되는 형식인지 확인합니다.
        
        Args:
            filename: 파일명
            
        Returns:
            지원 여부
        """
        extension = self._get_file_extension(filename)
        supported_extensions = (
            self.supported_extensions["text"] + 
            self.supported_extensions["table"]
        )
        return extension in supported_extensions

# 싱글턴 인스턴스
document_analyzer = DocumentAnalyzer() 