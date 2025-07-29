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
            raise ValueError(f"알 수 없는 에이전트: {agent_id}")
            
    except Exception as e:
        logger.error(f"에이전트 실행 오류 ({agent_id}): {e}")
        return {
            "success": False,
            "error": str(e),
            "agent": agent_id
        }

@router.post("/chat")
async def chat(req: QueryRequest):
    """메인 채팅 엔드포인트 - RouterAgent를 통한 자동 라우팅"""
    try:
        # 세션 초기화
        if req.session_id not in sessions:
            sessions[req.session_id] = {
                "messages": [],
                "routing_attempts": 0
            }
        
        session = sessions[req.session_id]
        session["messages"].append({"role": "user", "content": req.query})
        
        # RouterAgent를 통한 분류 시도 (최대 3회)
        classified_agent = None
        max_attempts = 3
        
        if router_agent:
            for attempt in range(max_attempts):
                session["routing_attempts"] = attempt + 1
                # 대화 이력을 포함하여 분류
                classified_agent = await router_agent.classify(req.query, session["messages"])
                
                if classified_agent and classified_agent in AVAILABLE_AGENT_IDS:
                    logger.info(f"분류 성공 (시도 {attempt + 1}): {classified_agent}")
                    break
                    
                logger.warning(f"분류 실패 (시도 {attempt + 1})")
                await asyncio.sleep(0.5)  # 재시도 전 대기
        
        # 분류 실패 시 수동 선택 필요
        if not classified_agent:
            fallback_message = f"""죄송합니다. '{req.query}' 질문이 저희 시스템의 기능과 관련이 없거나 분류가 어렵습니다.

저희 시스템은 다음 기능을 제공합니다:
- 직원 실적/평가 조회
- 고객/거래처(병원,약국) 정보 관리  
- 영업 데이터 검색
- 보고서/문서 자동 생성

해당하는 기능이 있다면 아래에서 선택해주세요:"""
            
            return {
                "success": True,
                "needs_user_selection": True,
                "message": fallback_message,
                "available_agents": AVAILABLE_AGENT_IDS,
                "agent_descriptions": AGENT_DESCS,
                "agent_display_names": AGENT_DISPLAY_NAMES,
                "routing_attempts": session["routing_attempts"]
            }
        
        # 에이전트 실행
        result = await run_agent(classified_agent, req.query, req.session_id)
        result["routing_attempts"] = session["routing_attempts"]
        result["classification_result"] = f"자동 분류: {classified_agent}"
        
        # 응답 저장
        session["messages"].append({
            "role": "assistant",
            "content": result.get("response", ""),
            "agent": classified_agent
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "response": "처리 중 오류가 발생했습니다."
        }

@router.post("/select-agent")
async def select_agent(req: SelectionRequest):
    """사용자가 직접 에이전트 선택"""
    try:
        agent_id = req.selected_agent or req.agent
        
        if not agent_id or agent_id not in AVAILABLE_AGENT_IDS:
            return {
                "success": False,
                "error": "유효하지 않은 에이전트입니다."
            }
        
        # 세션 초기화
        if req.session_id not in sessions:
            sessions[req.session_id] = {
                "messages": [],
                "routing_attempts": 0
            }
        
        # 사용자가 새 질문을 입력하지 않았다면 예시 질문 제공
        if not req.query or req.query == "" or req.query == req.selected_agent:
            agent_name = AGENT_DISPLAY_NAMES.get(agent_id, agent_id)
            example_questions = AGENT_EXAMPLE_QUESTIONS.get(agent_id, [])
            
            guide_message = f"""{agent_name}을(를) 선택하셨습니다.

이 에이전트는 다음과 같은 질문에 답변할 수 있습니다:
"""
            for i, example in enumerate(example_questions, 1):
                guide_message += f"\n{i}. {example}"
            
            guide_message += "\n\n위 예시를 참고하여 질문을 입력해주세요."
            
            return {
                "success": True,
                "agent_selected": True,
                "needs_new_question": True,
                "selected_agent": agent_id,
                "message": guide_message,
                "example_questions": example_questions
            }
        
        # 질문이 있으면 에이전트 실행
        result = await run_agent(agent_id, req.query, req.session_id)
        result["agent_selected"] = True
        result["classification_result"] = f"사용자 선택: {agent_id}"
        
        # 세션에 메시지 저장
        sessions[req.session_id]["messages"].append({
            "role": "user",
            "content": req.query
        })
        sessions[req.session_id]["messages"].append({
            "role": "assistant",
            "content": result.get("response", ""),
            "agent": agent_id
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Select agent error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/initial-agent-select")
async def initial_agent_select(req: SelectionRequest):
    """초기 화면에서 에이전트 직접 선택"""
    try:
        agent_id = req.selected_agent or req.agent
        
        if not agent_id or agent_id not in AVAILABLE_AGENT_IDS:
            return {
                "success": False,
                "error": "유효하지 않은 에이전트입니다."
            }
        
        # 세션 초기화
        if req.session_id not in sessions:
            sessions[req.session_id] = {
                "messages": [],
                "routing_attempts": 0
            }
        
        # 선택된 에이전트 정보와 예시 질문 제공
        agent_name = AGENT_DISPLAY_NAMES.get(agent_id, agent_id)
        example_questions = AGENT_EXAMPLE_QUESTIONS.get(agent_id, [])
        
        guide_message = f"""{agent_name}을(를) 선택하셨습니다.

이 에이전트는 다음과 같은 질문에 답변할 수 있습니다:
"""
        for i, example in enumerate(example_questions, 1):
            guide_message += f"\n{i}. {example}"
        
        guide_message += "\n\n위 예시를 참고하여 질문을 입력해주세요."
        
        return {
            "success": True,
            "agent_selected": True,
            "needs_new_question": True,
            "selected_agent": agent_id,
            "message": guide_message,
            "example_questions": example_questions
        }
        
    except Exception as e:
        logger.error(f"Initial agent select error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/test")
async def test():
    """테스트 엔드포인트"""
    return {"message": "API is working!", "status": "ok"}

@router.get("/chat-history")
async def get_chat_history():
    """채팅 기록"""
    history = []
    for session_id, data in sessions.items():
        history.append({
            "session_id": session_id,
            "message_count": len(data.get("messages", [])),
            "selected_agent": data.get("selected_agent"),
            "created_at": data.get("created_at", "")
        })
    
    return {
        "success": True,
        "chatHistory": history,
        "count": len(history)
    }

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """세션별 메시지"""
    if session_id in sessions:
        messages = sessions[session_id].get("messages", [])
        return {
            "success": True,
            "messages": messages,
            "count": len(messages)
        }
    
    return {
        "success": True,
        "messages": [],
        "count": 0
    }

@router.get("/current-agent/{session_id}")
async def get_current_agent(session_id: str):
    """현재 세션의 마지막 사용 에이전트 확인"""
    if session_id in sessions:
        messages = sessions[session_id].get("messages", [])
        # 마지막 assistant 메시지에서 에이전트 정보 찾기
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("agent"):
                agent = msg["agent"]
                return {
                    "success": True,
                    "has_selected_agent": False,  # 고정되지 않음
                    "last_agent": {
                        "agent_name": AGENT_DISPLAY_NAMES.get(agent, agent),
                        "agent_key": agent
                    }
                }
    
    return {
        "success": True,
        "has_selected_agent": False,
        "agent": None
    }

@router.post("/reset-agent")
async def reset_agent(req: Dict[str, Any]):
    """대화 이력 리셋"""
    session_id = req.get("session_id")
    if session_id and session_id in sessions:
        sessions[session_id]["messages"] = []
        sessions[session_id]["routing_attempts"] = 0
    
    return {
        "success": True,
        "message": "대화 이력이 초기화되었습니다."
    }