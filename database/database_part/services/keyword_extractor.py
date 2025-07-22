"""
OpenAI 기반 키워드 추출 서비스

사용자 질문에서 검색 키워드를 추출하는 OpenAI API 기반 서비스입니다.
"""

import logging
from typing import List, Tuple
from openai import OpenAI
from config import settings

logger = logging.getLogger(__name__)

class OpenAIKeywordExtractor:
    """OpenAI API 기반 키워드 추출 클래스"""
    
    def __init__(self):
        """초기화"""
        # OpenAI 클라이언트 초기화
        try:
            # 중앙화된 설정에서 OpenAI API 키 가져오기
            api_key = settings.get_openai_config().get("api_key")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI 클라이언트 초기화 성공")
            else:
                logger.warning("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
                self.openai_client = None
        except Exception as e:
            logger.warning(f"OpenAI 클라이언트 초기화 실패: {e}")
            self.openai_client = None

    def extract_keywords(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        OpenAI API를 사용한 키워드 추출
        
        Args:
            text: 입력 텍스트 (질문)
            top_k: 추출할 키워드 수
        
        Returns:
            (키워드, 점수) 튜플 리스트
        """
        if not self.openai_client:
            logger.warning("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return []
        
        try:
            # OpenAI API 호출을 위한 프롬프트 구성
            prompt = f"""
다음 질문에서 검색에 유용한 키워드를 추출해주세요. 
한국어로 답변하고, 키워드는 쉼표로 구분하여 나열해주세요.

질문: {text}

키워드 (쉼표로 구분):
"""
            
            # OpenAI API 호출
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 키워드 추출 전문가입니다. 질문에서 검색에 유용한 핵심 키워드만을 추출해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            # 응답에서 키워드 추출
            keywords_text = response.choices[0].message.content.strip()
            
            # 쉼표로 구분된 키워드를 리스트로 변환
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            
            # 키워드 수 제한
            keywords = keywords[:top_k]
            
            # 점수 계산 (OpenAI는 점수를 제공하지 않으므로 균등 분배)
            score_per_keyword = 1.0 / len(keywords) if keywords else 0
            keyword_scores = [(kw, score_per_keyword) for kw in keywords]
            
            logger.info(f"OpenAI 키워드 추출 완료: {keywords}")
            return keyword_scores
            
        except Exception as e:
            logger.error(f"OpenAI 키워드 추출 실패: {e}")
            return []


# 전역 인스턴스 생성
keyword_extractor = OpenAIKeywordExtractor() 