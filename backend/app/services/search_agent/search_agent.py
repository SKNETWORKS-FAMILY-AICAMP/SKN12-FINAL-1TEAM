import os
import requests
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode
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
    
    def call_text2sql_api(self, query: str, limit: int = 20) -> str:
        """
        Text2SQL API 호출하여 구조화된 데이터 검색 후 자연어 답변 생성
        
        Args:
            query: 검색 쿼리
            limit: 결과 개수 제한
            
        Returns:
            자연어 답변 문자열
        """
        try:
            # GET 요청을 위한 쿼리 파라미터 구성
            params = {
                "query": query,
                "limit": limit
            }
            
            response = requests.get(
                f"{self.base_url}/search/text2sql",
                headers=self.headers,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # 검색 결과를 자연어로 변환
                    natural_response = self._generate_natural_response_text2sql(
                        query=query,
                        results=result.get("results", []),
                        total_count=result.get("total_count", 0)
                    )
                    return natural_response
                else:
                    return "데이터를 찾을 수 없습니다."
            else:
                logger.error(f"Text2SQL API 오류: {response.status_code} - {response.text}")
                return "데이터 검색 시스템에 일시적인 문제가 있습니다."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Text2SQL API 요청 오류: {e}")
            return "데이터 검색 시스템에 연결할 수 없습니다."
        except Exception as e:
            logger.error(f"Text2SQL API 처리 오류: {e}")
            return "데이터 검색 중 오류가 발생했습니다."
    
    def call_opensearch_api(self, query: str, limit: int = 20, pipeline_id: str = "hybrid-minmax-pipeline") -> str:
        """
        OpenSearch API 호출하여 문서 검색 후 자연어 답변 생성
        
        Args:
            query: 검색 쿼리
            limit: 결과 개수 제한
            pipeline_id: 사용할 파이프라인 ID
            
        Returns:
            자연어 답변 문자열
        """
        try:
            # GET 요청을 위한 쿼리 파라미터 구성
            params = {
                "query": query,
                "limit": limit,
                "pipeline_id": pipeline_id
            }
            
            response = requests.get(
                f"{self.base_url}/search/opensearch",
                headers=self.headers,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # 검색 결과를 자연어로 변환
                    natural_response = self._generate_natural_response_opensearch(
                        query=query,
                        results=result.get("results", []),
                        total_count=result.get("total_count", 0)
                    )
                    return natural_response
                else:
                    return "관련 문서를 찾을 수 없습니다."
            else:
                logger.error(f"OpenSearch API 오류: {response.status_code} - {response.text}")
                return "문서 검색 시스템에 일시적인 문제가 있습니다."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenSearch API 요청 오류: {e}")
            return "문서 검색 시스템에 연결할 수 없습니다."
        except Exception as e:
            logger.error(f"OpenSearch API 처리 오류: {e}")
            return "문서 검색 중 오류가 발생했습니다."
    
    def call_all_search_api(self, query: str, limit: int = 20) -> str:
        """
        통합 검색 API 호출하여 모든 데이터 소스에서 검색 후 자연어 답변 생성
        
        Args:
            query: 검색 쿼리
            limit: 결과 개수 제한
            
        Returns:
            자연어 답변 문자열
        """
        try:
            # GET 요청을 위한 쿼리 파라미터 구성
            params = {
                "query": query,
                "limit": limit
            }
            
            response = requests.get(
                f"{self.base_url}/search/all",
                headers=self.headers,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                # 통합 검색 결과를 자연어로 변환
                natural_response = self._generate_natural_response_all(
                    query=query,
                    text2sql_result=result.get("text2sql", {}),
                    opensearch_result=result.get("opensearch", {})
                )
                return natural_response
            else:
                logger.error(f"통합 검색 API 오류: {response.status_code} - {response.text}")
                return "통합 검색 시스템에 일시적인 문제가 있습니다."
                
        except requests.exceptions.RequestException as e:
            logger.error(f"통합 검색 API 요청 오류: {e}")
            return "통합 검색 시스템에 연결할 수 없습니다."
        except Exception as e:
            logger.error(f"통합 검색 API 처리 오류: {e}")
            return "통합 검색 중 오류가 발생했습니다."
    
    def _generate_natural_response_text2sql(self, query: str, results: List[Dict], total_count: int) -> str:
        """
        Text2SQL 검색 결과를 자연어로 변환
        
        Args:
            query: 원본 쿼리
            results: 검색 결과 리스트
            total_count: 전체 결과 수
            
        Returns:
            자연어 응답
        """
        if total_count == 0:
            return f'"{query}"에 대한 데이터를 찾을 수 없습니다.'
        
        # LLM을 사용하여 결과를 자연어로 변환
        prompt = f"""
사용자 질문: {query}

검색된 데이터:
{json.dumps(results[:3], ensure_ascii=False, indent=2)}

위 데이터를 바탕으로 사용자에게 친절하게 답변해주세요.

답변 지침:
- 사용자가 궁금해하는 핵심 정보를 먼저 제공
- 구체적인 수치, 날짜, 이름은 정확하게 명시
- 자연스러운 대화체로 작성
- "검색 결과", "데이터베이스"같은 기술적 용어 사용 금지
- 예시: "김영수님의 2024년 실적은 1억 2천만원입니다. 전년 대비 15% 성장한 수치입니다."
"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM 응답 생성 오류: {e}")
            # 폴백: 기본 포맷팅
            if results:
                first_result = results[0]
                content = first_result.get("content", {})
                return f"검색 결과 {total_count}건을 찾았습니다. 첫 번째 결과: {json.dumps(content, ensure_ascii=False)}"
            return f"검색 결과 {total_count}건을 찾았습니다."
    
    def _generate_natural_response_opensearch(self, query: str, results: List[Dict], total_count: int) -> str:
        """
        OpenSearch 검색 결과를 자연어로 변환
        
        Args:
            query: 원본 쿼리
            results: 검색 결과 리스트
            total_count: 전체 결과 수
            
        Returns:
            자연어 응답
        """
        if total_count == 0:
            return f'"{query}"와 관련된 문서를 찾을 수 없습니다.'
        
        # LLM을 사용하여 문서 검색 결과를 자연어로 변환
        prompt = f"""
사용자 질문: {query}

찾은 문서 내용:
{json.dumps(results[:3], ensure_ascii=False, indent=2)}

위 문서 내용을 바탕으로 사용자 질문에 답변해주세요.

답변 지침:
- 문서에서 찾은 핵심 정보를 자연스럽게 전달
- 규정이나 정책은 구체적으로 설명
- 복잡한 내용은 쉽게 풀어서 설명
- 유사도 점수나 문서 ID 같은 메타데이터는 절대 언급하지 말 것
- 예시: "휴가 규정에 따르면 연차는 입사 1년차에 15일이 부여되며, 매년 1일씩 추가됩니다."
"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM 응답 생성 오류: {e}")
            # 폴백: 기본 포맷팅
            if results:
                doc_list = []
                for doc in results[:3]:
                    title = doc.get("doc_title", "제목 없음")
                    score = doc.get("similarity_score", 0)
                    doc_list.append(f"- {title} (유사도: {score:.2f})")
                return f"관련 문서 {total_count}건을 찾았습니다:\n" + "\n".join(doc_list)
            return f"관련 문서 {total_count}건을 찾았습니다."
    
    def _generate_natural_response_all(self, query: str, text2sql_result: Dict, opensearch_result: Dict) -> str:
        """
        통합 검색 결과를 자연어로 변환
        
        Args:
            query: 원본 쿼리
            text2sql_result: Text2SQL 검색 결과
            opensearch_result: OpenSearch 검색 결과
            
        Returns:
            자연어 응답
        """
        responses = []
        
        # Text2SQL 결과 처리
        if text2sql_result.get("success"):
            text2sql_count = text2sql_result.get("total_count", 0)
            if text2sql_count > 0:
                text2sql_response = self._generate_natural_response_text2sql(
                    query, 
                    text2sql_result.get("results", []), 
                    text2sql_count
                )
                responses.append(f"**데이터베이스 검색 결과**:\n{text2sql_response}")
        
        # OpenSearch 결과 처리
        if opensearch_result.get("success"):
            opensearch_count = opensearch_result.get("total_count", 0)
            if opensearch_count > 0:
                opensearch_response = self._generate_natural_response_opensearch(
                    query,
                    opensearch_result.get("results", []),
                    opensearch_count
                )
                responses.append(f"**문서 검색 결과**:\n{opensearch_response}")
        
        if not responses:
            return f'"{query}"에 대한 정보를 찾을 수 없습니다.'
        
        # LLM을 사용하여 통합 응답 생성
        combined_response = "\n\n".join(responses)
        prompt = f"""
사용자 질문: {query}

수집된 정보:
{combined_response}

위 정보들을 종합하여 사용자에게 완전한 답변을 제공해주세요.

답변 지침:
- 가장 중요한 정보를 먼저 제시
- 데이터와 문서 정보를 자연스럽게 통합
- 중복되는 내용은 한 번만 언급
- 친근하고 도움이 되는 톤으로 작성
- 기술적인 용어나 시스템 관련 표현 사용 금지
"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM 통합 응답 생성 오류: {e}")
            return combined_response
    
    def create_tools(self) -> List[Tool]:
        """
        LangChain Tool 객체들 생성 - 완전한 LLM 기반 툴 선택
        
        Returns:
            Tool 리스트
        """
        return [
            Tool(
                name="Text2SQLSearch",
                func=self.call_text2sql_api,
                description="""구조화된 데이터베이스 검색 시스템입니다. 다음 경우에 사용하세요:

1. 인사 정보: "최수아 직원 정보", "김영수 부서", "직원 목록", "급여 내역"
2. 매출/실적 데이터: "2024년 매출", "분기별 실적", "월별 거래량", "매출 통계"
3. 고객/거래처 정보: "삼성병원 거래내역", "거래처별 매출", "A등급 고객"
4. 구체적인 수치와 통계: "상위 10개", "최고 매출", "전체 합계"

예시 질문:
- "최수아의 인사 정보를 알려줘"
- "지난달 매출이 가장 높은 고객"
- "김철수 직원의 이번 분기 실적"

이 툴은 자연어 쿼리를 SQL로 변환하여 정확한 데이터를 검색합니다."""
            ),
            Tool(
                name="OpenSearchDoc",
                func=self.call_opensearch_api,
                description="""문서 검색 시스템입니다. 다음 경우에 사용하세요:

1. 계약서/문서: "계약서", "보고서", "공지사항", "회의록"
2. 규정/정책 문서: "근무 규정", "회사 정책", "복리후생 안내"
3. 관련 내용 검색: "FDA 승인", "신약 개발", "연구 결과"
4. 일반적인 문서 질문: "어떻게", "무엇", "왜", "절차"

예시 질문:
- "신약 개발 관련 계약서를 찾아줘"
- "리모트 워크에 대한 사내 공지"
- "2024년 공급 계약"

이 툴은 벡터 검색과 키워드 검색을 활용하여 문서를 찾습니다."""
            ),
            Tool(
                name="IntegratedSearch",
                func=self.call_all_search_api,
                description="""통합 검색 시스템입니다. 다음 경우에 사용하세요:

1. 포괄적인 정보 요청: "모든 정보", "전체 현황", "종합 정보"
2. 여러 소스 필요: 데이터 + 문서가 모두 필요한 경우
3. 특정 대상의 종합 정보: "삼성병원에 대한 모든 정보"

예시 질문:
- "삼성병원에 대한 모든 정보를 알려줘"
- "프로젝트 X의 전체 현황"
- "김영희 고객의 종합 정보"

이 툴은 데이터베이스와 문서를 동시에 검색합니다."""
            )
        ]
    
    def create_agent(self):
        """
        LangGraph 에이전트 생성
        
        Returns:
            컴파일된 그래프 앱
        """
        tools = self.create_tools()
        
        # 통일된 응답 형식을 위한 시스템 프롬프트 추가
        system_prompt = """당신은 친절하고 전문적인 회사 정보 도우미입니다.

        응답 지침:
        1. 사용자의 질문에 대해 자연스럽고 대화하듯이 답변하세요
        2. 핵심 정보를 먼저 명확하게 전달하세요
        3. 구체적인 수치나 날짜, 금액은 정확하게 명시하세요
        4. 필요한 경우 추가 설명이나 예시를 제공하세요
        5. 기술적인 메타데이터(유사도 점수, 데이터 출처 등)는 언급하지 마세요
        
        응답 예시:
        "휴가 규정에 대해 안내드리겠습니다. 결혼 시에는 5일의 경조휴가와 100만원의 경조금이 지원됩니다. 
        출산의 경우 배우자에게 10일의 유급휴가가 제공되며..."
        
        절대 하지 말아야 할 것:
        - "검색 결과입니다", "데이터베이스에서 찾았습니다" 같은 기계적 표현
        - 유사도 점수, 검색 건수 등 기술적 정보
        - 불필요한 제목이나 구분선
        
        사용자가 원하는 정보를 친절하고 명확하게 전달하는 것이 가장 중요합니다."""
        
        # 시스템 메시지를 포함한 LLM 생성
        llm_with_system = self.llm.bind(system=system_prompt)
        
        # React 에이전트 생성
        agent_node = create_react_agent(llm_with_system, tools)
        
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
        
        # 검색 시스템 통계 확인
        try:
            stats_response = requests.get(
                f"{self.base_url}/search/stats",
                headers=self.headers,
                timeout=10
            )
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                if stats.get("success"):
                    stats_data = stats.get("stats", {})
                    health_status["text2sql"] = stats_data.get("text2sql", {"available": False, "message": "Unknown"})
                    health_status["opensearch"] = stats_data.get("opensearch", {"available": False, "message": "Unknown"})
                else:
                    health_status["error"] = "Failed to get stats"
            else:
                health_status["error"] = f"Stats API returned {stats_response.status_code}"
                
        except Exception as e:
            health_status["error"] = str(e)
            health_status["text2sql"] = {"available": False, "message": "Cannot connect"}
            health_status["opensearch"] = {"available": False, "message": "Cannot connect"}
        
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