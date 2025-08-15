import os
import requests
import json
from typing import Dict, Any, List, Optional
from langchain.agents import Tool
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import logging
from pathlib import Path
from dotenv import load_dotenv

# 중앙 설정 import
from app.core.config import config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchAgent:
    def __init__(self, base_url: Optional[str] = None, api_token: Optional[str] = None):
        """
        검색 에이전트 초기화
        
        Args:
            base_url: API 서버 기본 URL (None이면 config에서 가져옴)
            api_token: JWT 토큰 (선택사항)
        """
        self.base_url = base_url or config.get_database_api_url()
        self.api_token = api_token or os.getenv("API_TOKEN")
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            api_key=config.get_openai_api_key()
        )
        
        # API 헤더 설정
        self.headers = {
            "Content-Type": "application/json"
        }
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"
    
    def call_qa_api(self, question: str, top_k: int = 5) -> str:
        """
        QA API 호출하여 질문에 대한 답변 생성
        
        Args:
            question: 사용자 질문
            top_k: 검색할 문서 수
            
        Returns:
            답변 문자열
        """
        try:
            payload = {
                "question": question,
                "top_k": top_k,
                "include_summary": True,
                "include_sources": True
            }
            
            response = requests.post(
                f"{self.base_url}/qa/question",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    answer = result.get("answer", "답변을 찾을 수 없습니다.")
                    summary = result.get("summary", "")
                    sources_count = result.get("total_sources", 0)
                    
                    # 소스 정보가 있으면 포함
                    if sources_count > 0:
                        return f"{answer}\n\n(참고 문서: {sources_count}개)"
                    return answer
                else:
                    return "질문에 대한 답변을 생성할 수 없습니다."
            else:
                logger.error(f"QA API 오류: {response.status_code} - {response.text}")
                return "QA 시스템에 일시적인 문제가 있습니다."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"QA API 요청 오류: {e}")
            return "QA 시스템에 연결할 수 없습니다."
        except Exception as e:
            logger.error(f"QA API 처리 오류: {e}")
            return "QA 시스템 처리 중 오류가 발생했습니다."
    
    def call_hybrid_search_api(self, query: str, limit: int = 20) -> str:
        """
        Hybrid Search API 호출하여 통합 검색 수행
        
        Args:
            query: 검색 쿼리
            limit: 결과 개수 제한
            
        Returns:
            검색 결과 요약 문자열
        """
        try:
            payload = {
                "query": query,
                "limit": limit
            }
            
            response = requests.post(
                f"{self.base_url}/search/hybrid",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return self._format_search_results(result)
                else:
                    return "검색 결과를 찾을 수 없습니다."
            else:
                logger.error(f"Hybrid Search API 오류: {response.status_code} - {response.text}")
                return "검색 시스템에 일시적인 문제가 있습니다."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Hybrid Search API 요청 오류: {e}")
            return "검색 시스템에 연결할 수 없습니다."
        except Exception as e:
            logger.error(f"Hybrid Search API 처리 오류: {e}")
            return "검색 시스템 처리 중 오류가 발생했습니다."
    
    def _format_search_results(self, result: Dict[str, Any]) -> str:
        """
        검색 결과를 사용자가 이해하기 쉬운 형태로 포맷팅
        
        Args:
            result: API 응답 결과
            
        Returns:
            포맷팅된 검색 결과 문자열
        """
        table_results = result.get("table_results", [])
        text_results = result.get("text_results", [])
        total_count = result.get("total_count", 0)
        
        if total_count == 0:
            return "검색 결과가 없습니다."
        
        # 결과 요약 생성
        summary_parts = []
        
        if table_results:
            summary_parts.append(f"테이블 데이터: {len(table_results)}개")
            # 첫 번째 테이블 결과 예시
            if table_results:
                first_table = table_results[0]
                content = first_table.get("content", {})
                if isinstance(content, dict):
                    summary_parts.append(f"예시: {list(content.keys())}")
        
        if text_results:
            summary_parts.append(f"문서 데이터: {len(text_results)}개")
            # 첫 번째 텍스트 결과 예시
            if text_results:
                first_text = text_results[0]
                content = first_text.get("content", "")
                if content:
                    summary_parts.append(f"예시: {content[:100]}...")
        
        return f"검색 결과: {total_count}개\n" + "\n".join(summary_parts)
    
    def create_tools(self) -> List[Tool]:
        """
        LangChain Tool 객체들 생성 - 완전한 LLM 기반 툴 선택
        
        Returns:
            Tool 리스트
        """
        return [
            Tool(
                name="TextDocQA",
                func=self.call_qa_api,
                description="""문서 기반 질문-답변 시스템입니다. 다음 경우에 사용하세요:

1. 규정/정책 관련 질문: "근무시간 규정", "회사 정책", "복리후생"
2. 공지사항/보고서 검색: "리모트워크 공지", "분기별 보고서"
3. 매뉴얼/가이드 검색: "업무 매뉴얼", "시스템 사용법"
4. 일반적인 질문 형태: "어떻게", "무엇", "왜", "언제", "어디서"

예시 질문:
- "근무 시간 관련 규정 알려줘"
- "리모트 워크에 대한 사내 공지 어디 있어?"
- "회사 복리후생 정책은 어떻게 되나요?"

이 툴은 문서 내용을 분석하여 자연스러운 답변을 제공합니다."""
            ),
            Tool(
                name="HybridDocSearch",
                func=self.call_hybrid_search_api,
                description="""구조화된 데이터 검색 시스템입니다. 다음 경우에 사용하세요:

1. 사원 정보: "최수아 사원 급여", "김영수 부서", "직원 목록"
2. 거래처 정보: "삼성메디텍 거래내역", "거래처별 매출", "최고 매출 거래처"
3. 매출/실적 데이터: "2024년 매출", "분기별 실적", "월별 거래량"
4. 구체적인 수치/기간 포함: "최근 3개월", "상위 5개", "2024년 상반기"

예시 질문:
- "최수아 사원의 급여 내역 보여줘"
- "거래처 중 가장 매출이 높은 곳 알려줘"
- "2024년 상반기 거래처별 매출과 분석 자료"

이 툴은 테이블 데이터와 문서를 통합하여 검색합니다."""
            )
        ]
    
    def create_agent(self):
        """
        LangGraph 에이전트 생성
        
        Returns:
            컴파일된 그래프 앱
        """
        tools = self.create_tools()
        
        # React 에이전트 생성
        agent_node = create_react_agent(self.llm, tools)
        
        # StateGraph 구성 (최신 버전 호환)
        from typing import TypedDict
        
        class AgentState(TypedDict):
            messages: list
            next: str
        
        graph = StateGraph(AgentState)
        graph.add_node("agent", agent_node)
        graph.set_entry_point("agent")
        graph.add_edge("agent", END)
        
        # 컴파일
        return graph.compile()
    
    def check_api_health(self) -> Dict[str, Any]:
        """
        API 시스템 상태 확인
        
        Returns:
            상태 정보 딕셔너리
        """
        health_status = {}
        
        # QA API 상태 확인
        try:
            qa_response = requests.get(f"{self.base_url}/qa/health", timeout=10)
            health_status["qa_api"] = {
                "status": "healthy" if qa_response.status_code == 200 else "unhealthy",
                "response_code": qa_response.status_code
            }
        except Exception as e:
            health_status["qa_api"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Hybrid Search API 상태 확인 (간접적으로)
        try:
            search_response = requests.get(f"{self.base_url}/search/hybrid/stats", headers=self.headers, timeout=10)
            health_status["search_api"] = {
                "status": "healthy" if search_response.status_code == 200 else "unhealthy",
                "response_code": search_response.status_code
            }
        except Exception as e:
            health_status["search_api"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        return health_status

def create_search_agent(base_url: Optional[str] = None, api_token: Optional[str] = None):
    """
    검색 에이전트 팩토리 함수
    
    Args:
        base_url: API 서버 기본 URL (None이면 config에서 가져옴)
        api_token: JWT 토큰
        
    Returns:
        SearchAgent 인스턴스
    """
    return SearchAgent(base_url=base_url, api_token=api_token)

# 사용 예시
if __name__ == "__main__":
    # 에이전트 생성
    agent = create_search_agent()
    
    # 시스템 상태 확인
    health = agent.check_api_health()
    print("시스템 상태:", json.dumps(health, indent=2, ensure_ascii=False))
    
    # 에이전트 앱 생성
    app = agent.create_agent()
    print("검색 에이전트가 성공적으로 생성되었습니다.") 