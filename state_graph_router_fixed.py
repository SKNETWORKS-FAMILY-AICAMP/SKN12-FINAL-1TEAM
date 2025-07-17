import logging
from .router_agent import RouterAgent, RouterState
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)
router = RouterAgent()

# ✅ 1. classify_with_llm
def classify_with_llm(state: dict) -> RouterState:
    logger.info(f"📩 사용자 질문: {state.query}")
    classification = router.classify_query(state.query)
    state.classification_result = classification
    agent = router.extract_agent_from_response(classification)
    state.selected_agent = agent
    state.routing_attempts += 1
    return s.to_dict()tate

# ✅ 2. retry_classification
def retry_classification(state: dict) -> RouterState:
    logger.info(f"🔁 재분류 시도: {state.routing_attempts}")
    return s.to_dict()tate

# ✅ 3. h2h_manual_selection
def h2h_manual_selection(state: RouterState) -> RouterState:
    logger.warning("🤖 자동 분류 실패 - H2H 모드로 전환")
    return router.fallback_to_h2h(state)

# ✅ 4. route_to_agent
def route_to_agent(state: RouterState) -> RouterState:
    if not state.selected_agent:
        state.error_message = "에이전트가 선택되지 않았습니다."
        logger.error(state.error_message)
    else:
        logger.info(f"🎯 선택된 에이전트: {state.selected_agent}")
    return s.to_dict()tate

# ✅ 5. execute_selected_agent
def execute_selected_agent(state: RouterState) -> RouterState:
    if state.selected_agent:
        router.execute_dummy_agent(state.selected_agent)
        state.final_response = f"[{state.selected_agent}] 에이전트가 실행되었습니다."
    else:
        state.final_response = "❌ 실행 실패: 선택된 에이전트가 없습니다."
    return s.to_dict()tate

# ✅ LangGraph 전체 흐름
def build_router_graph():
    graph = StateGraph(RouterState)

    graph.add_node("classify_with_llm", classify_with_llm)
    graph.add_node("retry_classification", retry_classification)
    graph.add_node("h2h_manual_selection", h2h_manual_selection)
    graph.add_node("route_to_agent", route_to_agent)
    graph.add_node("execute_selected_agent", execute_selected_agent)

    graph.set_entry_point("classify_with_llm")

    # 분류 실패 → 재시도 or H2H
    graph.add_conditional_edges(
        "classify_with_llm",
        lambda s: s.selected_agent is None and s.routing_attempts < 3,
        {
            True: "retry_classification",
            False: "h2h_manual_selection"
        }
    )

    graph.add_edge("retry_classification", "classify_with_llm")

    # 분류 성공 시 → route → execute
    graph.add_conditional_edges("classify_with_llm", lambda s: s.selected_agent is not None, {
        True: "route_to_agent"
    })
    graph.add_edge("route_to_agent", "execute_selected_agent")
    graph.add_edge("h2h_manual_selection", "execute_selected_agent")
    graph.add_edge("execute_selected_agent", END)

    return graph.compile()


# ✅ 외부 호출용 클래스
class StateGraphRouter:
    def __init__(self):
        self.app = build_router_graph()

    def process_query(self, query: str) -> dict:
        state = RouterState(**query=query)
        final_state = self.app.invoke(state)
        return final_state.to_dict()
