"""
LangGraph StateGraph 기반 라우터 시스템

StateGraph를 사용하여 상태 기반 흐름 제어와 조건부 분기를 구현합니다.
"""

import logging
from typing import Dict, Any, Optional, List, Literal
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
import json

from .router_agent import RouterAgent, RouterState

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphState(TypedDict):
    """그래프 상태 정의"""
    query: str
    selected_agent: Optional[str]
    routing_attempts: int
    final_response: str
    classification_result: str
    error_message: str
    next_action: str
    is_completed: bool

class StateGraphRouter:
    """StateGraph 기반 라우터 클래스"""
    
    def __init__(self):
        """초기화"""
        self.router_agent = RouterAgent()
        self.graph = self._build_graph()
        logger.info("✅ StateGraphRouter 초기화 완료")
        logger.info("   - LangGraph StateGraph 구성 완료")
        logger.info("   - 노드: start → classify → route → execute → end")
    
    def _build_graph(self) :
        """StateGraph 구축"""
        
        # StateGraph 생성
        workflow = StateGraph(GraphState)
        
        # 노드 추가
        workflow.add_node("start", self._start_node)
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("route", self._route_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("retry", self._retry_node)
        workflow.add_node("manual_selection", self._manual_selection_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # 시작점 설정
        workflow.set_entry_point("start")
        
        # 엣지 추가
        workflow.add_edge("start", "classify")
        
        # 조건부 엣지 - 분류 결과에 따른 분기
        workflow.add_conditional_edges(
            "classify",
            self._classify_decision,
            {
                "route": "route",
                "retry": "retry",
                "manual": "manual_selection"
            }
        )
        
        # 라우팅 후 실행
        workflow.add_edge("route", "execute")
        workflow.add_edge("execute", "finalize")
        
        # 재시도 후 다시 분류
        workflow.add_edge("retry", "classify")
        
        # 수동 선택 후 실행
        workflow.add_edge("manual_selection", "execute")
        
        # 종료
        workflow.add_edge("finalize", END)
        
        # 그래프 컴파일
        compiled_graph = workflow.compile()
        
        logger.info("🔧 StateGraph 구축 완료")
        return compiled_graph
    
    def _start_node(self, state: GraphState) -> GraphState:
        """시작 노드"""
        logger.info(f"🚀 [START] 라우팅 시작")
        
        print(f"\n" + "="*60)
        print(f"🎯 NaruTalk AI StateGraph 라우터 시스템 시작")
        print(f"="*60)
        
        # Step 1: 사용자 질문 출력
        print(f"\n📋 Step 1. 사용자 질문 출력")
        print(f"   질문: {state['query']}")
        
        state["routing_attempts"] = 0
        state["is_completed"] = False
        state["next_action"] = "classify"
        
        return state
    
    def _classify_node(self, state: GraphState) -> GraphState:
        """분류 노드"""
        logger.info(f"🤖 [CLASSIFY] LLM 분류 시작")
        
        print(f"\n🤖 Step 2. LLM 분류 결과 출력")
        print(f"🔄 분류 시도 {state['routing_attempts'] + 1}/{self.router_agent.max_retry_attempts}")
        
        # 분류 시도
        classification_result = self.router_agent.classify_query(state["query"])
        state["classification_result"] = classification_result
        state["routing_attempts"] += 1
        
        print(f"   분류 결과: {classification_result}")
        
        # 에이전트 추출
        selected_agent = self.router_agent.extract_agent_from_response(classification_result)
        
        if selected_agent:
            state["selected_agent"] = selected_agent
            state["next_action"] = "route"
            logger.info(f"✅ 에이전트 선택 성공: {selected_agent}")
            
        else:
            state["error_message"] = f"에이전트 선택 실패: {classification_result}"
            
            # 재시도 또는 수동 선택 결정
            if state["routing_attempts"] < self.router_agent.max_retry_attempts:
                state["next_action"] = "retry"
                logger.warning(f"⚠️ 재시도 필요: {state['routing_attempts']}/{self.router_agent.max_retry_attempts}")
            else:
                state["next_action"] = "manual"
                logger.warning(f"❌ 최대 재시도 초과 - 수동 선택 모드")
        
        return state
    
    def _route_node(self, state: GraphState) -> GraphState:
        """라우팅 노드"""
        logger.info(f"🎯 [ROUTE] 에이전트 라우팅: {state['selected_agent']}")
        
        print(f"✅ 에이전트 라우팅 성공: {state['selected_agent']}")
        
        state["next_action"] = "execute"
        return state
    
    def _execute_node(self, state: GraphState) -> GraphState:
        """실행 노드"""
        logger.info(f"🚀 [EXECUTE] 에이전트 실행: {state['selected_agent']}")
        
        print(f"\n🎯 Step 3. 분기된 에이전트 이름 출력")
        print(f"   최종 선택 에이전트: {state['selected_agent']}")
        
        # 더미 에이전트 실행
        self.router_agent.execute_dummy_agent(state["selected_agent"])
        
        state["final_response"] = f"[{state['selected_agent']}] 에이전트가 성공적으로 실행되었습니다."
        state["is_completed"] = True
        state["next_action"] = "finalize"
        
        return state
    
    def _retry_node(self, state: GraphState) -> GraphState:
        """재시도 노드"""
        logger.info(f"🔄 [RETRY] 재시도 {state['routing_attempts']}/{self.router_agent.max_retry_attempts}")
        
        print(f"🔄 재시도 {state['routing_attempts']}/{self.router_agent.max_retry_attempts}")
        
        state["next_action"] = "classify"
        return state
    
    def _manual_selection_node(self, state: GraphState) -> GraphState:
        """수동 선택 노드"""
        logger.info(f"🔧 [MANUAL] 수동 선택 모드")
        
        print(f"\n🔧 수동 선택 모드 (Human-to-Human)")
        print(f"📋 사용 가능한 에이전트:")
        
        for i, agent in enumerate(self.router_agent.available_agents, 1):
            print(f"   {i}. {agent}: {self.router_agent.agent_descriptions[agent]}")
        
        try:
            print(f"\n선택하세요 (1-{len(self.router_agent.available_agents)}): ", end="")
            choice = input()
            
            if choice.isdigit() and 1 <= int(choice) <= len(self.router_agent.available_agents):
                selected_agent = self.router_agent.available_agents[int(choice) - 1]
                state["selected_agent"] = selected_agent
                
                print(f"✅ 수동 선택된 에이전트: {selected_agent}")
                logger.info(f"✅ 수동 선택: {selected_agent}")
                
            else:
                print(f"❌ 잘못된 선택입니다. 기본 에이전트(db_agent)를 사용합니다.")
                state["selected_agent"] = "db_agent"
                logger.warning(f"⚠️ 잘못된 선택 - 기본 에이전트 사용")
                
        except Exception as e:
            logger.error(f"❌ 수동 선택 실패: {str(e)}")
            state["selected_agent"] = "db_agent"
            state["error_message"] = f"수동 선택 실패: {str(e)}"
        
        state["next_action"] = "execute"
        return state
    
    def _finalize_node(self, state: GraphState) -> GraphState:
        """종료 노드"""
        logger.info(f"🏁 [FINALIZE] 라우팅 완료")
        
        print(f"\n" + "="*60)
        print(f"🏁 StateGraph 라우팅 완료")
        print(f"   최종 에이전트: {state['selected_agent']}")
        print(f"   시도 횟수: {state['routing_attempts']}")
        print(f"   결과: {state['final_response']}")
        print(f"="*60)
        
        state["is_completed"] = True
        return state
    
    def _classify_decision(self, state: GraphState) -> Literal["route", "retry", "manual"]:
        """분류 결과에 따른 분기 결정"""
        
        if state["selected_agent"]:
            return "route"
        elif state["routing_attempts"] < self.router_agent.max_retry_attempts:
            return "retry"
        else:
            return "manual"
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """쿼리 처리 메인 메서드"""
        
        # 초기 상태 설정
        initial_state: GraphState = {
            "query": query,
            "selected_agent": None,
            "routing_attempts": 0,
            "final_response": "",
            "classification_result": "",
            "error_message": "",
            "next_action": "start",
            "is_completed": False
        }
        
        try:
            # StateGraph 실행
            result = self.graph.invoke(initial_state)
            
            logger.info(f"✅ StateGraph 실행 완료")
            return {
                "query": result["query"],
                "selected_agent": result["selected_agent"],
                "routing_attempts": result["routing_attempts"],
                "final_response": result["final_response"],
                "classification_result": result["classification_result"],
                "error_message": result["error_message"],
                "is_completed": result["is_completed"]
            }
            
        except Exception as e:
            logger.error(f"❌ StateGraph 실행 실패: {str(e)}")
            return {
                "query": query,
                "selected_agent": "db_agent",
                "routing_attempts": 0,
                "final_response": f"오류로 인한 기본 에이전트 실행: {str(e)}",
                "classification_result": "",
                "error_message": str(e),
                "is_completed": False
            }
    
    def get_graph_visualization(self) -> str:
        """그래프 시각화 정보 반환"""
        
        visualization = """
StateGraph 흐름도:

┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌─────────┐
│CLASSIFY │
└────┬────┘
     │
     ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│  ROUTE  │◄───┤DECISION │───►│  RETRY  │
└────┬────┘    └─────────┘    └────┬────┘
     │                             │
     ▼                             ▼
┌─────────┐                   ┌─────────┐
│EXECUTE  │                   │CLASSIFY │
└────┬────┘                   └─────────┘
     │
     ▼
┌─────────┐
│FINALIZE │
└────┬────┘
     │
     ▼
┌─────────┐
│   END   │
└─────────┘

노드 설명:
- START: 초기화 및 사용자 질문 출력
- CLASSIFY: GPT-4o를 사용한 에이전트 분류
- DECISION: 분류 결과에 따른 분기 결정
- ROUTE: 선택된 에이전트로 라우팅
- RETRY: 재시도 로직
- MANUAL: 수동 선택 모드
- EXECUTE: 에이전트 실행
- FINALIZE: 결과 정리 및 완료
- END: 종료
"""
        
        return visualization

# 테스트용 메인 함수
if __name__ == "__main__":
    
    # 테스트 쿼리들
    test_queries = [
        "김철수 직원의 이번 달 실적을 분석해주세요",
        "ABC 거래처의 매출 현황을 알려주세요", 
        "회사 휴가 규정을 검색해주세요",
        "영업비밀보호서약서를 자동으로 생성해주세요"
    ]
    
    state_router = StateGraphRouter()
    
    # 그래프 시각화 출력
    print(state_router.get_graph_visualization())
    
    for query in test_queries:
        result = state_router.process_query(query)
        print(f"\n📊 StateGraph 결과:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\n" + "-"*60 + "\n") 