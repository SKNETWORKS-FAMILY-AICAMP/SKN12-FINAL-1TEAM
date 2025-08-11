"""
LangGraph 기반 멀티 에이전트 라우터 API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime

# 라우터 에이전트 임포트
from app.services.router_agent import RouterAgent
# 대화 저장 임포트
from app.services.common.conversation_storage import save_message_sync

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 라우터 생성
router = APIRouter(prefix="/v1", tags=["langgraph"])

# 전역 라우터 에이전트 인스턴스
router_agent = RouterAgent()


# Request/Response 모델
class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "영업방문 결과보고서 작성해줘",
                "session_id": "optional-session-id"
            }
        }


class ResumeRequest(BaseModel):
    """세션 재개 요청 모델"""
    user_reply: str
    reply_type: str = "user_reply"
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_reply": "네, 맞습니다",
                "reply_type": "verification_reply"
            }
        }


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    success: bool
    session_id: str
    target_agent: Optional[str] = None
    requires_interrupt: bool = False
    response: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionStatusResponse(BaseModel):
    """세션 상태 응답 모델"""
    exists: bool
    session_id: Optional[str] = None
    agent: Optional[str] = None
    status: Optional[str] = None
    thread_id: Optional[str] = None
    message: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    사용자 메시지를 처리하고 적절한 에이전트로 라우팅합니다.
    
    Args:
        request: 채팅 요청
        
    Returns:
        ChatResponse: 처리 결과
    """
    try:
        logger.info(f"[CHAT] 요청 수신: {request.message[:50]}...")
        
        # 라우터 에이전트 실행
        result = router_agent.run(
            user_input=request.message,
            session_id=request.session_id
        )
        
        # 응답 구성
        response = ChatResponse(
            success=result.get("success", False),
            session_id=result.get("session_id"),
            target_agent=result.get("agent_type"),  # agent_type으로 변경
            requires_interrupt=result.get("requires_interrupt", False),
            error=result.get("error"),
            data={}  # 초기화
        )
        
        # 하위 에이전트 결과 처리
        sub_result = result.get("result", {})
        
        logger.info(f"[CHAT] Router result: {result}")
        logger.info(f"[CHAT] Sub-agent result: {sub_result}")
        logger.info(f"[CHAT] Router requires_interrupt: {result.get('requires_interrupt')}, next_node: {result.get('next_node')}, doc_type: {result.get('doc_type')}")
        logger.info(f"[CHAT] Router has response: {result.get('response') is not None}")
        
        # help_message 처리 (router에서 직접 반환하는 경우)
        if result.get("response"):
            logger.info(f"[CHAT] Returning help message from router")
            response.response = result["response"]
            return response
        
        # 인터럽트 처리를 먼저 확인
        if result.get("requires_interrupt"):
            # router 레벨의 인터럽트 정보 사용
            response.requires_interrupt = True
            
            # 상태 정보 추출 (router 레벨 우선, 없으면 sub_result 확인)
            next_node = result.get("next_node") or (sub_result.get("next_node") if sub_result else None)
            doc_type = result.get("doc_type") or (sub_result.get("doc_type") if sub_result else None)
            state_info = result.get("state_info") or (sub_result.get("state_info", {}) if sub_result else {})
            
            logger.info(f"[INTERRUPT] next_node: {next_node}, doc_type: {doc_type}")
            
            # docs_agent에서 반환한 정보가 있으면 우선 사용
            if sub_result and isinstance(sub_result, dict):
                response.data = {
                    "thread_id": result.get("thread_id") or sub_result.get("thread_id"),
                    "next_node": next_node,
                    "doc_type": doc_type,
                    "state_info": state_info,
                    "prompt": sub_result.get("prompt"),
                    "prompt_type": sub_result.get("prompt_type"),
                    "options": sub_result.get("options"),
                    "required_fields": sub_result.get("required_fields")
                }
                
                # docs_agent에서 반환한 프롬프트 사용
                response.response = sub_result.get("prompt", "추가 정보가 필요합니다.")
                response.data["interrupt_type"] = sub_result.get("prompt_type", "unknown")
            else:
                # 기본 처리 (sub_result가 없는 경우)
                response.data = {
                    "thread_id": result.get("thread_id"),
                    "next_node": next_node,
                    "doc_type": doc_type,
                    "state_info": state_info
                }
                
                # next_node로 정확한 상황 판단
                if next_node == "receive_verification_input" or next_node == "process_verification_response":
                    # 분류 검증 단계
                    response.response = f"분류된 문서 타입: {doc_type}\n\n위 분류 결과가 올바른가요?"
                    response.data["interrupt_type"] = "verification"
                    response.data["prompt_type"] = "verification"
                    
                elif next_node == "receive_manual_doc_type_input" or next_node == "process_manual_doc_type_selection":
                    # 수동 선택 단계
                    response.response = "문서 타입을 선택해주세요."
                    response.data["prompt_type"] = "manual_doc_selection"
                    response.data["options"] = [
                        {"value": "1", "label": "영업방문 결과보고서"},
                        {"value": "2", "label": "제품설명회 시행 신청서"},
                        {"value": "3", "label": "제품설명회 시행 결과보고서"},
                        {"value": "4", "label": "종료"}
                    ]
                    response.data["message"] = "올바른 문서 타입을 선택해주세요. 번호(1-4) 또는 문서명을 직접 입력할 수 있습니다."
                    
                elif next_node == "receive_user_input":
                    # 필드 입력 단계
                    template_content = state_info.get("template_content", "")
                    if template_content:
                        response.response = template_content
                    else:
                        response.response = "필요한 정보를 입력해주세요."
                    response.data["interrupt_type"] = "data_input"
                    response.data["template_content"] = template_content
                    
                else:
                    # 기본값
                    response.response = "추가 정보가 필요합니다."
                    response.data["interrupt_type"] = "unknown"
                
        elif sub_result and sub_result.get("success"):
            # 성공적인 결과
            agent_type = result.get("agent_type")
            
            if agent_type == "docs_agent":
                response.response = "문서가 성공적으로 생성되었습니다."
                response.data = {
                    "document_path": sub_result.get("result", {}).get("final_doc"),
                    "document_type": sub_result.get("result", {}).get("doc_type"),
                    "filled_data": sub_result.get("result", {}).get("filled_data")
                }
            elif agent_type == "employee_agent":
                response.response = sub_result.get("report", "")
                response.data = {
                    "employee_name": sub_result.get("employee_name"),
                    "period": sub_result.get("period"),
                    "total_performance": sub_result.get("total_performance"),
                    "achievement_rate": sub_result.get("achievement_rate")
                }
            elif agent_type == "client_agent":
                # client_agent 결과 처리
                response.response = sub_result.get("response", "") or sub_result.get("report", "") or sub_result.get("analysis_result", "") or sub_result.get("result", "") or str(sub_result)
                response.data = sub_result if isinstance(sub_result, dict) else {"result": sub_result}
            elif agent_type == "search_agent":
                # search_agent 결과 처리
                response.response = sub_result.get("search_result", "") or sub_result.get("result", "") or str(sub_result)
                response.data = sub_result if isinstance(sub_result, dict) else {"result": sub_result}
        
        
        else:
            # 오류 발생 또는 결과 없음
            if sub_result:
                response.error = sub_result.get("error", "알 수 없는 오류")
            else:
                response.error = result.get("error", "결과를 가져올 수 없습니다.")
        
        # 메타데이터 추가
        response.metadata = {
            "classification_confidence": result.get("classification_confidence"),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[CHAT] 응답 완료: success={response.success}, agent={response.target_agent}")
        return response
        
    except Exception as e:
        logger.error(f"[CHAT] 오류 발생: {str(e)}")
        return ChatResponse(
            success=False,
            session_id=request.session_id or str(uuid.uuid4()),
            requires_interrupt=False,
            error=f"처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/resume/{session_id}", response_model=ChatResponse)
async def resume_session(session_id: str, request: ResumeRequest) -> ChatResponse:
    """
    인터럽트된 세션을 재개합니다.
    
    Args:
        session_id: 세션 ID
        request: 재개 요청
        
    Returns:
        ChatResponse: 처리 결과
    """
    try:
        logger.info(f"[RESUME] 세션 재개: {session_id}")
        
        # 사용자 입력을 채팅 히스토리에 저장
        try:
            save_result = save_message_sync(
                session_id=session_id,
                role="user",
                message=request.user_reply
            )
            if save_result:
                logger.info(f"[RESUME] 사용자 입력 저장 성공: {session_id}")
            else:
                logger.warning(f"[RESUME] 사용자 입력 저장 실패: {session_id}")
        except Exception as e:
            logger.error(f"[RESUME] 사용자 입력 저장 오류: {e}")
        
        # 세션 재개
        result = router_agent.resume(
            session_id=session_id,
            user_reply=request.user_reply,
            reply_type=request.reply_type
        )
        
        # result가 None인 경우 처리
        if result is None:
            logger.error(f"[RESUME] None 반환: session_id={session_id}")
            result = {
                "success": False,
                "error": "세션 처리 중 오류가 발생했습니다."
            }
        
        # 응답 구성
        response = ChatResponse(
            success=result.get("success", False),
            session_id=session_id,
            error=result.get("error")
        )
        
        if result.get("success"):
            # 성공적으로 완료 (규정 위반이 있어도 분석은 완료)
            result_data = result.get("result") or {}
            
            # 규정 위반으로 파일 생성이 차단된 경우 확인
            if result.get("violation_blocked"):
                response.response = "분석이 완료되었지만 규정 위반으로 파일 생성이 차단되었습니다."
                response.data = {
                    "final_doc": None,  # 파일이 생성되지 않음
                    "filled_data": result.get("filled_data") or (result_data.get("filled_data") if isinstance(result_data, dict) else None),
                    "violation": result.get("violation"),
                    "violation_details": result.get("violation_details", []),
                    "violation_blocked": True
                }
            else:
                # 정상적으로 완료
                response.response = "처리가 완료되었습니다."
                response.data = {
                    "final_doc": result_data.get("final_doc") if isinstance(result_data, dict) else None,
                    "filled_data": result.get("filled_data") or (result_data.get("filled_data") if isinstance(result_data, dict) else None)
                }
        
        elif result.get("interrupted"):
            # 여전히 인터럽트 상태
            response.requires_interrupt = True
            response.response = "추가 정보가 필요합니다."
            response.data = {
                "thread_id": result.get("thread_id"),
                "next_node": result.get("next_node")
            }
            
            # next_node로 정확한 상황 판단
            next_node = result.get("next_node")
            doc_type = result.get("doc_type")
            
            if next_node == "receive_verification_input":
                # 분류 검증 단계
                response.response = f"분류된 문서 타입: {doc_type}\n\n위 분류 결과가 올바른가요?"
                response.data["interrupt_type"] = "verification"
                response.data["prompt_type"] = "verification"
                response.data["doc_type"] = doc_type
                
            elif next_node == "receive_manual_doc_type_input" or next_node == "process_manual_doc_type_selection":
                # 수동 선택 단계
                response.response = "문서 타입을 선택해주세요."
                response.data["prompt_type"] = "manual_doc_selection"
                response.data["options"] = [
                    {"value": "1", "label": "영업방문 결과보고서"},
                    {"value": "2", "label": "제품설명회 시행 신청서"},
                    {"value": "3", "label": "제품설명회 시행 결과보고서"},
                    {"value": "4", "label": "종료"}
                ]
                response.data["message"] = "올바른 문서 타입을 선택해주세요. 번호(1-4) 또는 문서명을 직접 입력할 수 있습니다."
                
            elif next_node == "receive_user_input":
                # 필드 입력 단계
                state_info = result.get("state_info", {})
                template_content = state_info.get("template_content", "")
                if template_content:
                    response.response = template_content
                else:
                    response.response = "필요한 정보를 입력해주세요."
                response.data["interrupt_type"] = "data_input"
                response.data["doc_type"] = doc_type
                response.data["template_content"] = template_content
                response.data["state_info"] = state_info
        else:
            # 실패 케이스 (규정 위반, 종료 등)
            response.requires_interrupt = False
            
            # 종료 처리 확인
            if result.get("error_type") == "user_terminated" or result.get("end_process"):
                response.response = "문서 작성이 종료되었습니다."
                response.data = {
                    "error_type": "user_terminated",
                    "message": "사용자가 종료를 선택했습니다.",
                    "end_session": True
                }
                # 세션 정리
                if hasattr(router_agent, 'sessions') and session_id in router_agent.sessions:
                    del router_agent.sessions[session_id]
                return response
            
            # 에러 메시지 구성
            error_msg = "처리 중 오류가 발생했습니다."
            violation_text = None
            
            if result.get("error"):
                error_msg = f"오류 발생: {result['error']}"
            elif result.get("violation"):
                error_msg = "규정 위반으로 문서 생성이 중단되었습니다."
                violation_text = result.get("violation")
            elif result.get("error_type") == "policy_violation":
                error_msg = "규정 위반으로 문서 생성이 중단되었습니다."
                violation_text = result.get("violation")
            elif result.get("result") is None:
                error_msg = "문서 생성 실패: 결과가 없습니다."
            
            response.response = error_msg
            
            # result가 dict인지 확인하고 안전하게 처리
            if isinstance(result, dict):
                # result.result에서 violation 정보 확인
                inner_result = result.get("result", {})
                
                # violation_text가 이미 설정되어 있지 않으면 inner_result에서 확인
                if not violation_text and isinstance(inner_result, dict):
                    violation_text = inner_result.get("violation")
                
                # 위반 상세 정보가 있으면 포함
                violation_details = result.get("violation_details", [])
                
                response.data = {
                    "error_type": result.get("error_type", "policy_violation" if violation_text else "processing_error"),
                    "violation": violation_text,
                    "violation_details": violation_details,
                    "details": result.get("details", result.get("error")),
                    "filled_data": inner_result.get("filled_data") if inner_result else None
                }
            else:
                response.data = {"error_type": "unknown_error"}
        
        # AI 응답을 채팅 히스토리에 저장
        if response.response:
            try:
                save_result = save_message_sync(
                    session_id=session_id,
                    role="assistant",
                    message=response.response
                )
                if save_result:
                    logger.info(f"[RESUME] AI 응답 저장 성공: {session_id}")
                else:
                    logger.warning(f"[RESUME] AI 응답 저장 실패: {session_id}")
            except Exception as e:
                logger.error(f"[RESUME] AI 응답 저장 오류: {e}")
        
        logger.info(f"[RESUME] 응답 완료: success={response.success}")
        return response
        
    except Exception as e:
        logger.error(f"[RESUME] 오류 발생: {str(e)}")
        return ChatResponse(
            success=False,
            session_id=session_id,
            requires_interrupt=False,
            error=f"세션 재개 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str) -> SessionStatusResponse:
    """
    세션 상태를 조회합니다.
    
    Args:
        session_id: 세션 ID
        
    Returns:
        SessionStatusResponse: 세션 상태
    """
    try:
        logger.info(f"[STATUS] 세션 상태 조회: {session_id}")
        
        # 세션 상태 조회
        status = router_agent.get_session_status(session_id)
        
        return SessionStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"[STATUS] 오류 발생: {str(e)}")
        return SessionStatusResponse(
            exists=False,
            message=f"상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트
    
    Returns:
        Dict: 서비스 상태
    """
    return {
        "status": "healthy",
        "service": "langgraph-router",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/agents")
async def list_agents():
    """
    사용 가능한 에이전트 목록을 반환합니다.
    
    Returns:
        Dict: 에이전트 목록 및 설명
    """
    return {
        "agents": [
            {
                "name": "docs_agent",
                "description": "문서 작성 에이전트 - 영업방문 결과보고서, 제품설명회 신청서/결과보고서 작성",
                "features": [
                    "템플릿 기반 문서 생성",
                    "규정 준수 검사",
                    "대화형 입력 지원"
                ]
            },
            {
                "name": "employee_agent",
                "description": "직원 실적 분석 에이전트 - 실적 조회, 목표 달성률 분석, 트렌드 분석",
                "features": [
                    "실적 데이터 분석",
                    "목표 대비 달성률 계산",
                    "성과 트렌드 분석",
                    "종합 평가 보고서 생성"
                ]
            }
        ]
    }


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    특정 세션의 채팅 내역을 조회합니다.
    
    Args:
        session_id: 세션 ID
        
    Returns:
        List[Dict]: 메시지 목록
    """
    try:
        from app.services.common.conversation_storage import ConversationStorage
        
        storage = ConversationStorage()
        messages = await storage.get_conversation(session_id)
        
        # 메시지가 없어도 정상 응답 (빈 배열 반환)
        if messages is None:
            messages = []
        
        return {
            "success": True,
            "session_id": session_id,
            "messages": messages,
            "count": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CHAT_HISTORY] 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"대화 내역 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/chat/sessions/user/{employee_id}")
async def get_user_sessions(employee_id: int):
    """
    사용자의 모든 세션 목록을 조회합니다.
    
    Args:
        employee_id: 직원 ID
        
    Returns:
        List[Dict]: 세션 목록
    """
    try:
        from app.services.common.conversation_storage import ConversationStorage
        
        storage = ConversationStorage()
        sessions = await storage.get_user_sessions(employee_id)
        
        return {
            "success": True,
            "employee_id": employee_id,
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"[USER_SESSIONS] 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"세션 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str, employee_id: int = 1):
    """
    특정 세션을 삭제합니다.
    
    Args:
        session_id: 세션 ID
        employee_id: 직원 ID
        
    Returns:
        Dict: 삭제 결과
    """
    try:
        from app.services.common.conversation_storage import ConversationStorage
        
        storage = ConversationStorage()
        success = await storage.delete_session(session_id, employee_id)
        
        if success:
            return {
                "success": True,
                "message": f"세션 {session_id}이(가) 삭제되었습니다."
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"세션 {session_id}을(를) 찾을 수 없습니다."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE_SESSION] 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"세션 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/chat/session/{session_id}/title")
async def update_session_title(session_id: str, request: dict):
    """
    세션 제목을 업데이트합니다.
    
    Args:
        session_id: 세션 ID
        request: {"title": "새로운 제목"}
        
    Returns:
        Dict: 업데이트 결과
    """
    try:
        from app.services.common.conversation_storage import ConversationStorage
        
        title = request.get("title")
        if not title:
            raise HTTPException(
                status_code=400,
                detail="제목이 필요합니다."
            )
        
        storage = ConversationStorage()
        result = await storage.update_session_title(session_id, title)
        
        if result:
            return {
                "success": True,
                "message": f"세션 제목이 업데이트되었습니다.",
                "session_id": session_id,
                "title": title
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"세션 {session_id}을(를) 찾을 수 없습니다."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UPDATE_TITLE] 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"세션 제목 업데이트 중 오류가 발생했습니다: {str(e)}"
        )


# 개발용 테스트 엔드포인트
if __name__ == "__main__":
    # 테스트를 위한 간단한 예제
    @router.post("/test")
    async def test_endpoint(message: str):
        """테스트 엔드포인트"""
        return {"message": f"Received: {message}"}