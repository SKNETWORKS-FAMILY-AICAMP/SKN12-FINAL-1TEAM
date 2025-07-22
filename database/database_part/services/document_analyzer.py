"""
문서 타입 자동 분석 서비스
문서의 확장자와 내용을 분석하여 자동으로 타입을 분류합니다.
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentCategory(Enum):
    """문서 카테고리"""
    TABLE = "table"
    TEXT = "text"

class DocumentType(Enum):
    """문서 타입"""
    # 테이블 문서
    CUSTOMER_INFO = "customer_info"      # 거래처 정보
    EMPLOYEE_INFO = "employee_info"      # 직원 정보
    
    # 텍스트 문서
    REGULATION = "regulation"            # 내부 규정
    REPORT = "report"                   # 보고서

class DocumentAnalyzer:
    """문서 타입 자동 분석기"""
    
    def __init__(self):
        # 지원하는 파일 확장자
        self.supported_extensions = {
            "text": [".txt", ".docx", ".pdf"],
            "table": [".csv", ".xlsx", ".xls"]
        }
        
        # 테이블 문서 패턴
        self.table_patterns = {
            "customer_info": {
                "keywords": [
                    "거래처", "고객", "매입처", "공급업체", "업체명", "사업자번호", 
                    "대표자", "주소", "연락처", "담당자", "매출", "거래량",
                    "customer", "client", "vendor", "supplier", "company"
                ],
                "column_patterns": [
                    r"거래처\s*명", r"업체\s*명", r"고객\s*명", r"사업자\s*번호",
                    r"대표\s*자", r"주\s*소", r"연락\s*처", r"담당\s*자",
                    r"매출\s*액", r"거래\s*량", r"계약\s*일", r"만료\s*일"
                ]
            },
            "employee_info": {
                "keywords": [
                    "직원", "사원", "임직원", "근로자", "이름", "사번", "부서",
                    "직급", "입사일", "연락처", "이메일", "급여", "성과",
                    "employee", "staff", "worker", "name", "id", "department"
                ],
                "column_patterns": [
                    r"직원\s*명", r"사원\s*명", r"사\s*번", r"부\s*서",
                    r"직\s*급", r"입사\s*일", r"연락\s*처", r"이메\s*일",
                    r"급\s*여", r"성\s*과", r"평\s*가", r"승진\s*일"
                ]
            }
        }
        
        # 텍스트 문서 패턴
        self.text_patterns = {
            "regulation": {
                "keywords": [
                    "규정", "규칙", "지침", "정책", "가이드라인", "행동강령",
                    "제1장", "제2장", "제1조", "제2조", "목적", "정의", "준수",
                    "금지", "의무", "책임", "처벌", "위반", "조치",
                    "regulation", "policy", "guideline", "code", "rule"
                ],
                "structure_patterns": [
                    r"제\d+장\s*[^\n]+",  # 제1장 총칙
                    r"제\d+조\s*\[[^\]]+\]",  # 제1조[목적]
                    r"①\s*[^\n]+",  # ① 첫 번째 항목
                    r"②\s*[^\n]+",  # ② 두 번째 항목
                    r"본\s*규정", r"본\s*지침", r"본\s*정책"
                ]
            },
            "report": {
                "keywords": [
                    "보고서", "리포트", "분석", "현황", "결과", "통계",
                    "시장", "업계", "성과", "실적", "전망", "계획",
                    "report", "analysis", "status", "result", "statistics"
                ],
                "structure_patterns": [
                    r"\d+\.\s*[^\n]+",  # 1. 제목
                    r"[A-Z]\.\s*[^\n]+",  # A. 제목
                    r"[가-힣]\.\s*[^\n]+",  # 가. 제목
                    r"##\s*[^\n]+",  # ## 제목
                    r"#\s*[^\n]+",  # # 제목
                    r"[^\n]+\n[-=]{3,}",  # 제목\n--- 또는 ===
                    r"결\s*론", r"요\s*약", r"서\s*론", r"본\s*론"
                ]
            }
        }
    
    def analyze_document(self, text: str, filename: str) -> str:
        """
        문서를 분석하여 타입을 자동으로 분류합니다.
        
        Args:
            text: 문서 내용
            filename: 파일명
            
        Returns:
            문서 타입 문자열 (doc_type에 저장될 값)
        """
        try:
            logger.info(f"문서 분석 시작: {filename}")
            
            # 1. 파일 확장자 확인
            file_extension = self._get_file_extension(filename)
            
            if not file_extension:
                logger.warning(f"지원하지 않는 파일 형식: {filename}")
                return DocumentType.REPORT.value  # 기본값
            
            # 2. 확장자 기반 카테고리 분류
            if file_extension in self.supported_extensions["table"]:
                # 테이블 문서 분석
                return self._analyze_table_document(text)
            else:
                # 텍스트 문서 분석
                return self._analyze_text_document(text)
            
        except Exception as e:
            logger.error(f"문서 분석 중 오류 발생: {e}")
            return DocumentType.REPORT.value  # 기본값
    
    def _get_file_extension(self, filename: str) -> str:
        """파일 확장자를 추출합니다."""
        if not filename:
            return ""
        
        # 파일명에서 확장자 추출
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return ""
    
    def _analyze_table_document(self, text: str) -> str:
        """테이블 문서 분석"""
        logger.info("테이블 문서 분석 시작")
        
        # 구체적인 타입 분류
        customer_score = self._calculate_table_score(text, "customer_info")
        employee_score = self._calculate_table_score(text, "employee_info")
        
        if customer_score > employee_score:
            logger.info(f"거래처 정보로 분류 (점수: {customer_score:.2f})")
            return DocumentType.CUSTOMER_INFO.value
        else:
            logger.info(f"직원 정보로 분류 (점수: {employee_score:.2f})")
            return DocumentType.EMPLOYEE_INFO.value
    
    def _analyze_text_document(self, text: str) -> str:
        """텍스트 문서 분석"""
        logger.info("텍스트 문서 분석 시작")
        
        # 규정 문서 점수 계산
        regulation_score = self._calculate_text_score(text, "regulation")
        report_score = self._calculate_text_score(text, "report")
        
        if regulation_score > report_score:
            logger.info(f"내부 규정으로 분류 (점수: {regulation_score:.2f})")
            return DocumentType.REGULATION.value
        else:
            logger.info(f"보고서로 분류 (점수: {report_score:.2f})")
            return DocumentType.REPORT.value
    
    def _calculate_table_score(self, text: str, table_type: str) -> float:
        """테이블 문서 타입별 점수 계산"""
        patterns = self.table_patterns[table_type]
        score = 0.0
        
        # 키워드 매칭
        keyword_matches = 0
        for keyword in patterns["keywords"]:
            if keyword.lower() in text.lower():
                keyword_matches += 1
        
        keyword_score = keyword_matches / len(patterns["keywords"])
        score += keyword_score * 0.6
        
        # 컬럼 패턴 매칭
        column_matches = 0
        for pattern in patterns["column_patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                column_matches += 1
        
        column_score = column_matches / len(patterns["column_patterns"])
        score += column_score * 0.4
        
        return score
    
    def _calculate_text_score(self, text: str, text_type: str) -> float:
        """텍스트 문서 타입별 점수 계산"""
        patterns = self.text_patterns[text_type]
        score = 0.0
        
        # 키워드 매칭
        keyword_matches = 0
        for keyword in patterns["keywords"]:
            if keyword.lower() in text.lower():
                keyword_matches += 1
        
        keyword_score = keyword_matches / len(patterns["keywords"])
        score += keyword_score * 0.5
        
        # 구조 패턴 매칭
        structure_matches = 0
        for pattern in patterns["structure_patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                structure_matches += 1
        
        structure_score = structure_matches / len(patterns["structure_patterns"])
        score += structure_score * 0.5
        
        return score
    
    def get_chunking_type(self, document_type: str) -> str:
        """
        문서 타입에 따른 청킹 타입을 반환합니다.
        
        Args:
            document_type: 문서 타입
            
        Returns:
            청킹 타입 ("regulation" 또는 "report")
        """
        if document_type in [DocumentType.REGULATION.value]:
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