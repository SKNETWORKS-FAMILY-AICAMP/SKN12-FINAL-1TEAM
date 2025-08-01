from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import logging
import sys
from pathlib import Path

# 경로 설정
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.router_agent.router_agent import RouterAgent, AVAILABLE_AGENT_IDS, AGENT_DESCS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 요청 모델
class QueryRequest(BaseModel):
    session_id: str
    query: str

class SelectionRequest(BaseModel):
    session_id: str
    agent: Optional[str] = None
    selected_agent: Optional[str] = None
    query: str

# 세션 관리
sessions = {}

# Router Agent 인스턴스 (싱글톤)
try:
    router_agent = RouterAgent()
    logger.info("RouterAgent 초기화 성공")
except Exception as e:
    logger.error(f"RouterAgent 초기화 실패: {e}")
    router_agent = None

# 에이전트 표시 이름
AGENT_DISPLAY_NAMES = {
    "employee_agent": "직원 실적 분석",
    "client_agent": "고객/거래처 분석", 
    "search_agent": "정보 검색",
    "create_document_agent": "문서 생성"
}

# 에이전트별 예시 질문
AGENT_EXAMPLE_QUESTIONS = {
    "employee_agent": [
        "김철수 사원의 이번 달 실적을 보여주세요",
        "영업1팀의 평균 매출액은 얼마인가요?",
        "작년 우수 사원 명단을 조회해주세요",
        "영업본부 조직도를 보여주세요"
    ],
    "client_agent": [
        "A병원의 월별 구매 추이를 분석해주세요",
        "서울 지역 약국 거래처 목록을 보여주세요",
        "이번 달 신규 거래처는 몇 개인가요?",
        "VIP 등급 병원들의 주요 구매 품목은?"
    ],
    "search_agent": [
        "항생제 제품 카탈로그를 검색해주세요",
        "영업 매뉴얼에서 계약 절차를 찾아주세요",
        "사내 휴가 규정을 검색해주세요",
        "신제품 교육 자료를 찾아주세요"
    ],
    "create_document_agent": [
        "이번 달 영업 실적 보고서를 작성해주세요",
        "거래처 방문 보고서 템플릿을 만들어주세요",
        "분기별 매출 분석 문서를 생성해주세요",
        "신규 거래처 제안서를 작성해주세요"
    ]
}

async def run_agent(agent_id: str, query: str, session_id: str) -> Dict[str, Any]:
    """각 에이전트의 run.py 실행"""
    try:
        if agent_id == "employee_agent":
            from app.services.employee_agent.run import run
            result = await run(query, session_id)
            return result
            
        elif agent_id == "client_agent":
            from app.services.client_agent.run import run
            result = await run(query, session_id)
            return result
            
        elif agent_id == "search_agent":
            from app.services.search_agent.run import run
            result = await run(query, session_id)
            return result
            
        elif agent_id == "create_document_agent":
            from app.services.create_document_agent.run import run
            result = await run(query, session_id)
            return result
            
        else:
            return {"error": f"Unknown agent: {agent_id}"}
            
    except Exception as e:
        logger.error(f"Agent {agent_id} 실행 오류: {e}")
        return {"error": f"Agent 실행 중 오류 발생: {str(e)}"}

@router.post("/chat")
async def chat(req: QueryRequest):
    """메인 채팅 엔드포인트 - 라우터가 자동으로 적절한 에이전트 선택"""
    try:
        if not router_agent:
            raise HTTPException(status_code=500, detail="RouterAgent가 초기화되지 않았습니다.")
        
        logger.info(f"채팅 요청: session_id={req.session_id}, query={req.query[:50]}...")
        
        # 라우터 에이전트로 쿼리 분석 및 적절한 에이전트 선택
        result = await router_agent.route_query(req.query, req.session_id)
        
        if result.get("needs_user_selection"):
            # 사용자 선택이 필요한 경우
            return {
                "success": True,
                "needs_user_selection": True,
                "message": result.get("message", "어떤 기능을 사용하시겠습니까?"),
                "available_agents": result.get("available_agents", AVAILABLE_AGENT_IDS),
                "agent_descriptions": result.get("agent_descriptions", AGENT_DESCS),
                "agent_display_names": AGENT_DISPLAY_NAMES
            }
        
        # 자동으로 에이전트가 선택된 경우
        selected_agent = result.get("selected_agent")
        if selected_agent:
            # 선택된 에이전트 실행
            agent_result = await run_agent(selected_agent, req.query, req.session_id)
            
            return {
                "success": True,
                "agent": selected_agent,
                "response": agent_result.get("response", "처리가 완료되었습니다."),
                "routing_attempts": result.get("routing_attempts", 1),
                "classification_result": result.get("classification_result", "자동 선택")
            }
        else:
            return {
                "success": False,
                "error": "적절한 에이전트를 찾을 수 없습니다."
            }
            
    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류 발생: {str(e)}")

@router.post("/select-agent")
async def select_agent(req: SelectionRequest):
    """사용자가 직접 에이전트를 선택하는 엔드포인트"""
    try:
        logger.info(f"에이전트 선택: session_id={req.session_id}, agent={req.selected_agent}, query={req.query[:50]}...")
        
        if not req.selected_agent:
            raise HTTPException(status_code=400, detail="선택된 에이전트가 없습니다.")
        
        # 선택된 에이전트 실행
        result = await run_agent(req.selected_agent, req.query, req.session_id)
        
        if result.get("error"):
            return {
                "success": False,
                "error": result["error"]
            }
        
        return {
            "success": True,
            "agent": req.selected_agent,
            "response": result.get("response", "처리가 완료되었습니다."),
            "agent_selected": True
        }
        
    except Exception as e:
        logger.error(f"에이전트 선택 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"에이전트 선택 처리 중 오류 발생: {str(e)}")

@router.post("/initial-agent-select")
async def initial_agent_select(req: SelectionRequest):
    """초기 화면에서 에이전트를 선택하는 엔드포인트"""
    try:
        logger.info(f"초기 에이전트 선택: session_id={req.session_id}, agent={req.selected_agent}")
        
        if not req.selected_agent:
            raise HTTPException(status_code=400, detail="선택된 에이전트가 없습니다.")
        
        # 선택된 에이전트의 예시 질문 제공
        example_questions = AGENT_EXAMPLE_QUESTIONS.get(req.selected_agent, [])
        
        return {
            "success": True,
            "selected_agent": req.selected_agent,
            "message": f"{AGENT_DISPLAY_NAMES.get(req.selected_agent, req.selected_agent)}를 선택하셨습니다. 어떤 정보를 찾고 계신가요?",
            "needs_new_question": True,
            "example_questions": example_questions
        }
        
    except Exception as e:
        logger.error(f"초기 에이전트 선택 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"초기 에이전트 선택 처리 중 오류 발생: {str(e)}")

@router.get("/test")
async def test():
    """테스트 엔드포인트"""
    return {
        "success": True,
        "message": "Router API가 정상적으로 작동합니다.",
        "available_agents": AVAILABLE_AGENT_IDS
    }

@router.get("/chat-history")
async def get_chat_history():
    """채팅 히스토리 조회 (임시 구현)"""
    return {
        "success": True,
        "chatHistory": [],
        "count": 0
    }

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """세션별 메시지 조회 (임시 구현)"""
    return {
        "success": True,
        "messages": [],
        "count": 0
    }

@router.get("/current-agent/{session_id}")
async def get_current_agent(session_id: str):
    """현재 세션의 선택된 에이전트 확인 (임시 구현)"""
    return {
        "success": True,
        "has_selected_agent": False,
        "agent_info": None
    }

@router.post("/reset-agent")
async def reset_agent(req: Dict[str, Any]):
    """에이전트 초기화 (임시 구현)"""
    return {
        "success": True,
        "message": "에이전트가 초기화되었습니다. 다음 질문부터 새로운 에이전트가 선택됩니다."
    }

# 새로운 라우터 엔드포인트 (상태 그래프 기반)
class QueryRequest(BaseModel):
    query: str

@router.post("/router")
def route_with_state_graph(req: QueryRequest):
    """상태 그래프 기반 라우터"""
    try:
        from app.services.router_agent.state_graph_router import execute_router
        
        # 상태 그래프 라우터 실행
        result = execute_router(req.query)
        
        return {
            "success": True,
            "agent": result.get("agent", "unknown"),
            "response": result.get("response", "처리가 완료되었습니다."),
            "message": result.get("message", "라우팅이 완료되었습니다.")
        }
        
    except Exception as e:
        logger.error(f"상태 그래프 라우터 오류: {e}")
        return {
            "success": False,
            "error": f"라우터 처리 중 오류 발생: {str(e)}"
        }
