import logging
from typing import Dict, Any, TypedDict
from .router_agent import RouterAgent, RouterState
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

# LangGraph용 상태 타입 정의
class GraphState(TypedDict):
    query: str
    selected_agent: str
    routing_attempts: int
    final_response: str
    classification_result: str
    error_message: str

router = RouterAgent()

# 1. classify_with_llm 
def classify_with_llm(state: GraphState) -> GraphState:
    current_attempts = state.get('routing_attempts', 0)
    logger.info(f"📩 사용자 질문: {state['query']}")
    logger.info(f"🔄 현재 시도 횟수: {current_attempts}")
    
    # 3회 이상 시도한 경우 강제로 None 반환 (안전장치)
    if current_attempts >= 3:
        logger.warning("⚠️ 3회 이상 시도 - 강제로 None 반환")
        return {
            "query": state['query'],
            "selected_agent": None,
            "routing_attempts": current_attempts,
            "final_response": state.get('final_response', ''),
            "classification_result": "MAX_ATTEMPTS_REACHED",
            "error_message": "최대 시도 횟수 초과"
        }
    
    # 분류 수행
    classification = router.classify_query(state['query'])
    agent = router.extract_agent_from_response(classification)
    
    # 시도 횟수 증가
    new_attempts = current_attempts + 1
    
    logger.info(f"🤖 GPT-4o 분류 결과: {classification}")
    logger.info(f"🎯 추출된 에이전트: {agent}")
    logger.info(f"🔢 업데이트된 시도 횟수: {new_attempts}")
    
    # 결과 업데이트
    return {
        "query": state['query'],
        "selected_agent": agent,
        "routing_attempts": new_attempts,
        "final_response": state.get('final_response', ''),
        "classification_result": classification,
        "error_message": state.get('error_message', '')
    }

# 2. retry_classification
def retry_classification(state: GraphState) -> GraphState:
    logger.info(f"🔁 재분류 시도: {state['routing_attempts']}")
    return state

# 3. h2h_manual_selection
def h2h_manual_selection(state: GraphState) -> GraphState:
    logger.warning("🤖 자동 분류 실패 - H2H 모드로 전환")
    
    # RouterState 객체 생성
    state_obj = RouterState(state['query'])
    state_obj.routing_attempts = state['routing_attempts']
    
    # H2H 모드 실행
    result_state = router.fallback_to_h2h(state_obj)
    
    return {
        "query": state['query'],
        "selected_agent": result_state.selected_agent,
        "routing_attempts": state['routing_attempts'],
        "final_response": result_state.final_response,
        "classification_result": state['classification_result'],
        "error_message": state.get('error_message', '')
    }

# 4. route_to_agent
def route_to_agent(state: GraphState) -> GraphState:
    if not state['selected_agent']:
        error_msg = "에이전트가 선택되지 않았습니다."
        logger.error(error_msg)
        state['error_message'] = error_msg
    else:
        logger.info(f"🎯 선택된 에이전트: {state['selected_agent']}")
    
    return state

# 5. execute_selected_agent
def execute_selected_agent(state: GraphState) -> GraphState:
    if state['selected_agent']:
        router.execute_dummy_agent(state['selected_agent'])
        final_response = f"[{state['selected_agent']}] 에이전트가 실행되었습니다."
    else:
        final_response = "❌ 실행 실패: 선택된 에이전트가 없습니다."
    
    return {
        "query": state['query'],
        "selected_agent": state['selected_agent'],
        "routing_attempts": state['routing_attempts'],
        "final_response": final_response,
        "classification_result": state['classification_result'],
        "error_message": state.get('error_message', '')
    }

# ✅ 조건 분기 함수
def classify_condition(state: GraphState) -> str:
    selected_agent = state.get('selected_agent')
    routing_attempts = state.get('routing_attempts', 0)
    
    logger.info(f"🔍 조건 분기 확인: selected_agent={selected_agent}, routing_attempts={routing_attempts}")
    
    # 에이전트가 성공적으로 선택된 경우
    if selected_agent is not None and selected_agent != "none" and selected_agent in router.available_agents:
        logger.info("✅ 에이전트 선택됨 -> route_to_agent")
        return "has_agent"
    # 3회 미만 시도한 경우 재시도
    elif routing_attempts < 3:
        logger.info(f"🔁 재시도 {routing_attempts}/3 -> retry_classification")
        return "retry"
    # 3회 이상 실패한 경우 H2H 모드
    else:
        logger.info("🤖 3회 실패 -> h2h_manual_selection")
        return "h2h"

# ✅ LangGraph 전체 흐름
def build_router_graph():
    graph = StateGraph(GraphState)

    graph.add_node("classify_with_llm", classify_with_llm)
    graph.add_node("retry_classification", retry_classification)
    graph.add_node("h2h_manual_selection", h2h_manual_selection)
    graph.add_node("route_to_agent", route_to_agent)
    graph.add_node("execute_selected_agent", execute_selected_agent)

    graph.set_entry_point("classify_with_llm")

    # ✅ 분기를 하나의 조건 함수로 통합
    graph.add_conditional_edges(
        "classify_with_llm",
        classify_condition,
        {
            "has_agent": "route_to_agent",
            "retry": "retry_classification",
            "h2h": "h2h_manual_selection"
        }
    )

    graph.add_edge("retry_classification", "classify_with_llm")
    graph.add_edge("route_to_agent", "execute_selected_agent")
    graph.add_edge("h2h_manual_selection", "execute_selected_agent")
    graph.add_edge("execute_selected_agent", END)

    return graph.compile()

# ✅ 외부 호출용 클래스
class StateGraphRouter:
    def __init__(self):
        self.app = build_router_graph()

    def process_query(self, query: str) -> dict:
        # 초기 상태 생성
        initial_state: GraphState = {
            "query": query,
            "selected_agent": None,
            "routing_attempts": 0,
            "final_response": "",
            "classification_result": "",
            "error_message": ""
        }
        
        # 그래프 실행
        final_state = self.app.invoke(initial_state)
        return final_state
