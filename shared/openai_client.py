"""
Shared OpenAI client for microservices
"""
import os
import asyncio
import openai
from openai import AsyncOpenAI
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)


class MultiGPTClient:
    """
    멀티-GPT 클라이언트 (GPT-4o, GPT-4o-mini 통합)
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # 모델별 설정
        self.gpt4o_config = {
            "model": os.getenv('OPENAI_GPT4O_MODEL', 'gpt-4o'),
            "max_tokens": int(os.getenv('OPENAI_MAX_TOKENS', '4000')),
            "temperature": float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        }
        
        self.gpt4o_mini_config = {
            "model": os.getenv('OPENAI_GPT4O_MINI_MODEL', 'gpt-4o-mini'),
            "max_tokens": 2000,
            "temperature": 0.3
        }
    
    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        GPT-4o-mini로 빠른 의도 분류
        """
        try:
            system_prompt = """
            당신은 의료업계 QA 시스템의 의도 분류 전문가입니다.
            사용자 질의를 다음 카테고리로 분류하세요:
            - search: 정보 검색
            - analytics: 데이터 분석
            - client: 고객 관련
            - document: 문서 관련
            - news: 뉴스/동향
            - ml: 성과 예측
            - memory: 대화 기록
            - general: 일반 대화
            
            JSON 형태로 응답하세요: {"intent": "category", "confidence": 0.9, "keywords": ["key1", "key2"]}
            """
            
            response = await self.client.chat.completions.create(
                **self.gpt4o_mini_config,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
            )
            
            # JSON 파싱 시도
            try:
                import json
                result = json.loads(response.choices[0].message.content)
                return result
            except:
                # 파싱 실패 시 기본값 반환
                return {
                    "intent": "general",
                    "confidence": 0.5,
                    "keywords": []
                }
        
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "intent": "general",
                "confidence": 0.0,
                "keywords": []
            }
    
    async def enhance_content(self, content: str, context: Optional[str] = None) -> str:
        """
        GPT-4o-mini로 컨텐츠 향상
        """
        try:
            system_prompt = """
            당신은 의료업계 전문 컨텐츠 향상 도우미입니다.
            주어진 내용을 더 명확하고 유용하게 개선하세요.
            - 의료업계 전문 용어를 적절히 사용
            - 구체적이고 실용적인 정보 제공
            - 한국어로 자연스럽게 작성
            """
            
            user_prompt = f"내용: {content}"
            if context:
                user_prompt += f"\n컨텍스트: {context}"
            
            response = await self.client.chat.completions.create(
                **self.gpt4o_mini_config,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Content enhancement failed: {e}")
            return content  # 실패 시 원본 반환
    
    async def generate_final_response(self, context: str, query: str) -> Dict[str, Any]:
        """
        GPT-4o로 고품질 최종 응답 생성
        """
        try:
            system_prompt = """
            당신은 의료업계 전문 QA 시스템의 최고급 AI 어시스턴트입니다.
            다음 조건을 만족하는 고품질 응답을 생성하세요:
            
            1. 정확하고 신뢰할 수 있는 정보 제공
            2. 의료업계 전문성 반영
            3. 사용자 친화적이고 이해하기 쉬운 설명
            4. 필요시 추가 정보나 다음 단계 제안
            5. 한국어로 자연스럽고 전문적인 톤
            
            응답은 다음 JSON 형태로 제공하세요:
            {
                "answer": "주요 답변 내용",
                "summary": "핵심 요약",
                "recommendations": ["권장사항1", "권장사항2"],
                "confidence": 0.95,
                "sources": ["참고자료1", "참고자료2"]
            }
            """
            
            user_prompt = f"""
            사용자 질의: {query}
            
            수집된 컨텍스트:
            {context}
            
            위 정보를 바탕으로 종합적이고 정확한 답변을 생성해주세요.
            """
            
            response = await self.client.chat.completions.create(
                **self.gpt4o_config,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # JSON 파싱 시도
            try:
                import json
                result = json.loads(response.choices[0].message.content)
                return result
            except:
                # 파싱 실패 시 텍스트 응답 반환
                return {
                    "answer": response.choices[0].message.content,
                    "summary": "응답이 생성되었습니다.",
                    "recommendations": [],
                    "confidence": 0.8,
                    "sources": []
                }
        
        except Exception as e:
            logger.error(f"Final response generation failed: {e}")
            return {
                "answer": "죄송합니다. 현재 응답을 생성할 수 없습니다.",
                "summary": "오류 발생",
                "recommendations": [],
                "confidence": 0.0,
                "sources": []
            }
    
    async def validate_response(self, response: str, query: str) -> Dict[str, Any]:
        """
        GPT-4o-mini로 응답 검증
        """
        try:
            system_prompt = """
            당신은 QA 시스템의 품질 검증 전문가입니다.
            생성된 응답의 품질을 평가하세요:
            
            평가 기준:
            1. 질의와의 관련성 (0-1)
            2. 정보의 정확성 (0-1)
            3. 완성도 (0-1)
            4. 명확성 (0-1)
            
            JSON 형태로 응답하세요:
            {
                "overall_score": 0.85,
                "relevance": 0.9,
                "accuracy": 0.8,
                "completeness": 0.85,
                "clarity": 0.9,
                "issues": ["발견된 문제점들"],
                "approved": true
            }
            """
            
            user_prompt = f"""
            원본 질의: {query}
            생성된 응답: {response}
            
            위 응답의 품질을 평가해주세요.
            """
            
            validation_response = await self.client.chat.completions.create(
                **self.gpt4o_mini_config,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # JSON 파싱 시도
            try:
                import json
                result = json.loads(validation_response.choices[0].message.content)
                return result
            except:
                # 파싱 실패 시 기본 승인
                return {
                    "overall_score": 0.7,
                    "approved": True,
                    "issues": []
                }
        
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            return {
                "overall_score": 0.5,
                "approved": True,  # 오류 시 기본 승인
                "issues": [f"검증 오류: {str(e)}"]
            }


# 전역 클라이언트 인스턴스
multi_gpt_client = MultiGPTClient() 