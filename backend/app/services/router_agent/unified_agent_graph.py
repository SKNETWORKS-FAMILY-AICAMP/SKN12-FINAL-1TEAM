from typing import Dict, List, Any, Optional, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import openai
import os
from datetime import datetime

# 새로운 에이전트 구조 imports
from ..employee_agent.simple_employee_handler import process_employee_request
from ..client_agent.simple_client_handler import process_client_request
from ..create_document_agent.document_creator import process_document_request
from ..search_agent.database_searcher import process_search_request
from .router_agent import RouterAgent

# State 정의
class UnifiedState(TypedDict):
    query: str                          # 사용자 쿼리
    session_id: str                     # 세션 ID
    agent: Optional[str]                # 선택된 에이전트
    stage: str                          # 현재 단계 (initial, classified, processing, completed, error, needs_user_selection)
    response: Optional[str]             # 최종 응답
    memory: List[Dict[str, Any]]        # 숏텀 메모리
    error: Optional[str]                # 오류 메시지
    classification_result: Optional[Dict[str, Any]]  # 분류 결과
    agent_result: Optional[Dict[str, Any]]           # 에이전트 실행 결과
    available_agents: Optional[List[str]]            # 사용 가능한 에이전트 목록
    requires_followup: Optional[bool]                # 후속 입력 필요 여부
    user_selection_needed: Optional[bool]            # 사용자 선택 필요 여부

class UnifiedAgentGraph:
    """통합 에이전트 그래프 클래스"""
    
    def __init__(self):
        self.router_agent = RouterAgent()
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.graph = self._create_graph()
        
        # 에이전트 메타데이터
        self.agent_metadata = {
            "employee_agent": {
                "name": "직원 실적 분석",
                "description": "사내 직원의 실적 분석, 성과 평가, 인사 정보 조회",
                "keywords": ["직원", "실적", "성과", "평가", "인사", "담당자"]
            },
            "client_agent": {
                "name": "고객/거래처 분석", 
                "description": "고객 분석, 거래처 매출 분석, 영업 성과 분석",
                "keywords": ["고객", "거래처", "병원", "매출", "영업"]
            },
            "create_document_agent": {
                "name": "문서 초안 작성",
                "description": "문서 초안 작성, 양식 생성, 컴플라이언스 검토",
                "keywords": ["문서", "보고서", "양식", "작성", "생성", "초안"]
            },
            "search_agent": {
                "name": "내부 데이터 검색",
                "description": "내부 데이터베이스 검색, 정보 조회, 문서 검색",
                "keywords": ["검색", "조회", "찾기", "정보"]
            }
        }
    
    def _create_graph(self):
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(UnifiedState)
        
        # 노드 추가
        workflow.add_node("classify_agent", self._classify_agent_node)
        workflow.add_node("employee_executor", self._employee_agent_executor)
        workflow.add_node("client_executor", self._client_agent_executor)
        workflow.add_node("create_document_executor", self._create_document_agent_executor)
        workflow.add_node("search_executor", self._search_agent_executor)
        workflow.add_node("fallback_handler", self._fallback_handler_node)
        workflow.add_node("user_selection_handler", self._user_selection_handler_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        
        # 시작점 설정
        workflow.set_entry_point("classify_agent")
        
        # 조건부 엣지 - 분류 결과에 따른 라우팅
        workflow.add_conditional_edges(
            "classify_agent",
            self._route_to_agent,
            {
                "employee_agent": "employee_executor",
                "client_agent": "client_executor", 
                "create_document_agent": "create_document_executor",
                "search_agent": "search_executor",
                "needs_user_selection": "user_selection_handler",
                "error": "fallback_handler"
            }
        )
        
        # 각 에이전트 실행 후 최종화
        workflow.add_edge("employee_executor", "finalize_response")
        workflow.add_edge("client_executor", "finalize_response")
        workflow.add_edge("create_document_executor", "finalize_response")
        workflow.add_edge("search_executor", "finalize_response")
        workflow.add_edge("fallback_handler", "finalize_response")
        workflow.add_edge("user_selection_handler", "finalize_response")
        workflow.add_edge("finalize_response", END)
        
        return workflow.compile()
    
    def _classify_agent_node(self, state: UnifiedState) -> UnifiedState:
        """에이전트 분류 노드"""
        try:
            query = state["query"]
            
            # 메모리에 사용자 쿼리 추가
            if "memory" not in state:
                state["memory"] = []
            
            state["memory"].append({
                "role": "user",
                "content": query,
                "timestamp": datetime.now().isoformat()
            })
            
            # RouterAgent를 사용한 분류
            classification_result = self.router_agent.classify_query(query)
            
            if "ERROR:" in classification_result:
                state["stage"] = "error"
                state["error"] = "분류 중 오류가 발생했습니다."
                state["agent"] = "error"
                return state
            
            # 분류 결과에서 에이전트 추출
            selected_agent = self.router_agent.extract_agent_from_response(classification_result)
            
            if selected_agent and selected_agent in self.router_agent.available_agents:
                state["agent"] = selected_agent
                state["stage"] = "classified"
                state["classification_result"] = {
                    "selected_agent": selected_agent,
                    "classification_text": classification_result,
                    "confidence": "high"
                }
                print(f"✅ 에이전트 분류 완료: {selected_agent}")
            else:
                # 분류 실패 시 사용자 선택 모드
                state["stage"] = "needs_user_selection"
                state["agent"] = "needs_user_selection"
                state["user_selection_needed"] = True
                state["available_agents"] = self.router_agent.available_agents
                print("⚠️ 자동 분류 실패 - 사용자 선택 모드")
            
        except Exception as e:
            state["stage"] = "error"
            state["error"] = f"분류 처리 중 오류: {str(e)}"
            state["agent"] = "error"
            print(f"❌ 분류 노드 오류: {e}")
        
        return state
    
    def _route_to_agent(self, state: UnifiedState) -> str:
        """에이전트 라우팅 결정"""
        agent = state.get("agent")
        
        if agent == "needs_user_selection":
            return "needs_user_selection"
        elif agent == "error":
            return "error"
        elif agent in ["employee_agent", "client_agent", "create_document_agent", "search_agent"]:
            return agent
        else:
            return "error"
    
    async def _employee_agent_executor(self, state: UnifiedState) -> UnifiedState:
        """직원 에이전트 실행기"""
        try:
            state["stage"] = "processing"
            print(f"🔄 직원 에이전트 실행 시작: {state['query']}")
            
            # 새로운 employee_agent 호출
            result = await process_employee_request(state["query"], state.get("session_id"))
            
            if result.get("success"):
                state["response"] = result.get("response", "")
                state["stage"] = result.get("stage", "completed")
                state["agent_result"] = result
                
                # 메모리에 결과 추가
                state["memory"].append({
                    "role": "assistant",
                    "content": result.get("response", ""),
                    "agent": "employee_agent",
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                state["stage"] = "error"
                state["error"] = result.get("error", "직원 분석 실패")
                state["response"] = "직원 실적 분석 중 오류가 발생했습니다."
                
        except Exception as e:
            state["stage"] = "error"
            state["error"] = str(e)
            state["response"] = "직원 에이전트 실행 중 오류가 발생했습니다."
            print(f"❌ 직원 에이전트 오류: {e}")
        
        return state
    
    async def _client_agent_executor(self, state: UnifiedState) -> UnifiedState:
        """고객 에이전트 실행기"""
        try:
            state["stage"] = "processing"
            print(f"🔄 고객 에이전트 실행 시작: {state['query']}")
            
            # 새로운 client_agent 호출
            result = await process_client_request(state["query"], state.get("session_id"))
            
            if result.get("success"):
                state["response"] = result.get("response", "")
                state["stage"] = result.get("stage", "completed")
                state["agent_result"] = result
                
                # 메모리에 결과 추가
                state["memory"].append({
                    "role": "assistant",
                    "content": result.get("response", ""),
                    "agent": "client_agent",
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                state["stage"] = "error"
                state["error"] = result.get("error", "고객 분석 실패")
                state["response"] = "고객 분석 중 오류가 발생했습니다."
                
        except Exception as e:
            state["stage"] = "error"
            state["error"] = str(e)
            state["response"] = "고객 에이전트 실행 중 오류가 발생했습니다."
            print(f"❌ 고객 에이전트 오류: {e}")
        
        return state
    
    async def _create_document_agent_executor(self, state: UnifiedState) -> UnifiedState:
        """문서 작성 에이전트 실행기"""
        try:
            state["stage"] = "processing"
            print(f"🔄 문서 작성 에이전트 실행 시작: {state['query']}")
            
            # 새로운 create_document_agent 호출
            result = await process_document_request(state["query"], state.get("session_id"))
            
            if result.get("success"):
                state["response"] = result.get("response", "")
                state["stage"] = result.get("stage", "completed")
                state["agent_result"] = result
                
                # 메모리에 결과 추가
                state["memory"].append({
                    "role": "assistant",
                    "content": result.get("response", ""),
                    "agent": "create_document_agent",
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                state["stage"] = "error"
                state["error"] = result.get("error", "문서 작성 실패")
                state["response"] = "문서 작성 중 오류가 발생했습니다."
                
        except Exception as e:
            state["stage"] = "error"
            state["error"] = str(e)
            state["response"] = "문서 작성 에이전트 실행 중 오류가 발생했습니다."
            print(f"❌ 문서 작성 에이전트 오류: {e}")
        
        return state
    
    async def _search_agent_executor(self, state: UnifiedState) -> UnifiedState:
        """검색 에이전트 실행기"""
        try:
            state["stage"] = "processing"
            print(f"🔄 검색 에이전트 실행 시작: {state['query']}")
            
            # 새로운 search_agent 호출
            result = await process_search_request(state["query"], state.get("session_id"))
            
            if result.get("success"):
                state["response"] = result.get("response", "")
                state["stage"] = result.get("stage", "completed")
                state["agent_result"] = result
                
                # 메모리에 결과 추가
                state["memory"].append({
                    "role": "assistant",
                    "content": result.get("response", ""),
                    "agent": "search_agent",
                    "timestamp": datetime.now().isoformat()
                })
                
            else:
                state["stage"] = "error"
                state["error"] = result.get("error", "검색 실패")
                state["response"] = "검색 중 오류가 발생했습니다."
            
        except Exception as e:
            state["stage"] = "error"
            state["error"] = str(e)
            state["response"] = "검색 에이전트 실행 중 오류가 발생했습니다."
            print(f"❌ 검색 에이전트 오류: {e}")
        
        return state
    
    def _user_selection_handler_node(self, state: UnifiedState) -> UnifiedState:
        """사용자 선택 처리 노드"""
        try:
            state["stage"] = "needs_user_selection"
            
            # 사용 가능한 에이전트 정보 제공
            agent_options = []
            for agent_key in self.router_agent.available_agents:
                metadata = self.agent_metadata.get(agent_key, {})
                agent_options.append(f"• **{metadata.get('name', agent_key)}**: {metadata.get('description', '')}")
            
            formatted_response = (
                f"🤔 **질문의 의도가 불분명합니다.**\n\n"
                f"다음 중 하나를 선택해주세요:\n\n"
                f"{chr(10).join(agent_options)}\n\n"
                f"💡 **선택 방법**: 원하는 분석 유형을 명시해서 다시 질문해주시거나, "
                f"'직원 분석', '고객 분석', '문서 작성', '정보 검색' 중 하나를 선택해주세요."
            )
            
            state["response"] = formatted_response
            state["user_selection_needed"] = True
            
            # 메모리에 결과 추가
            state["memory"].append({
                "role": "assistant",
                "content": formatted_response,
                "agent": "user_selection",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            state["stage"] = "error"
            state["error"] = str(e)
            state["response"] = "사용자 선택 처리 중 오류가 발생했습니다."
            print(f"❌ 사용자 선택 핸들러 오류: {e}")
        
        return state
    
    def _fallback_handler_node(self, state: UnifiedState) -> UnifiedState:
        """폴백 처리 노드"""
        try:
            error_msg = state.get("error", "알 수 없는 오류")
            
            formatted_response = (
                f"❌ **처리 중 오류가 발생했습니다.**\n\n"
                f"오류 내용: {error_msg}\n\n"
                f"💡 **해결 방법:**\n"
                f"• 질문을 더 구체적으로 작성해주세요\n"
                f"• 다른 방식으로 질문해보세요\n"
                f"• 시스템 관리자에게 문의해주세요\n\n"
                f"🔄 다시 시도해보시거나 다른 질문을 해주세요."
            )
            
            state["response"] = formatted_response
            state["stage"] = "error_handled"
            
            # 메모리에 결과 추가
            state["memory"].append({
                "role": "assistant",
                "content": formatted_response,
                "agent": "fallback",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            state["response"] = "시스템 오류가 발생했습니다. 관리자에게 문의해주세요."
            state["stage"] = "critical_error"
            print(f"❌ 폴백 핸들러 오류: {e}")
        
        return state
    
    def _finalize_response_node(self, state: UnifiedState) -> UnifiedState:
        """응답 최종화 노드"""
        try:
            # 응답이 없는 경우 기본 응답 설정
            if not state.get("response"):
                state["response"] = "요청을 처리했지만 응답을 생성할 수 없습니다."
                state["stage"] = "completed_no_response"
            
            # 최종 로그
            print(f"✅ 최종 응답 준비 완료 - Agent: {state.get('agent')}, Stage: {state.get('stage')}")
            
        except Exception as e:
            state["response"] = "응답 최종화 중 오류가 발생했습니다."
            state["stage"] = "finalization_error"
            print(f"❌ 응답 최종화 오류: {e}")
        
        return state
    
    async def process_query(self, query: str, session_id: str) -> Dict[str, Any]:
        """쿼리 처리 메인 함수"""
        initial_state = {
            "query": query,
            "session_id": session_id,
            "agent": None,
            "stage": "initial",
            "response": None,
            "memory": [],
            "error": None,
            "classification_result": None,
            "agent_result": None,
            "available_agents": None,
            "requires_followup": False,
            "user_selection_needed": False
        }
        
        try:
            # LangGraph 실행
            result = await self.graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "agent": result.get("agent"),
                "stage": result.get("stage"),
                "session_id": session_id,
                "requires_followup": result.get("requires_followup", False),
                "user_selection_needed": result.get("user_selection_needed", False),
                "available_agents": result.get("available_agents", []),
                "memory": result.get("memory", []),
                "agent_result": result.get("agent_result"),
                "error": result.get("error")
            }
            
        except Exception as e:
            print(f"❌ 통합 그래프 실행 오류: {e}")
            return {
                "success": False,
                "response": "시스템 처리 중 오류가 발생했습니다.",
                "error": str(e),
                "session_id": session_id,
                "stage": "graph_error"
            }

# 전역 인스턴스
unified_graph = UnifiedAgentGraph() 