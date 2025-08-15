"""
docs_agent 전용 FastAPI API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime

# docs_agent 임포트
from app.services.docs_agent.create_document_agent import CreateDocumentAgent
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 라우터 생성
router = APIRouter(tags=["docs-agent"])

# 전역 docs_agent 인스턴스 (API 모드로 설정)
docs_agent = None

def get_docs_agent():
    global docs_agent
    if docs_agent is None:
        docs_agent = CreateDocumentAgent(api_mode=True)
    return docs_agent

# 세션 저장소 (간단한 메모리 저장소)
sessions = {}


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
    requires_interrupt: bool = False
    response: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionStatusResponse(BaseModel):
    """세션 상태 응답 모델"""
    exists: bool
    session_id: Optional[str] = None
    status: Optional[str] = None
    thread_id: Optional[str] = None
    message: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    docs_agent로 문서 작성 요청을 처리합니다.
    
    Args:
        request: 채팅 요청
        
    Returns:
        ChatResponse: 처리 결과
    """
    try:
        # docs_agent 가져오기
        docs_agent = get_docs_agent()
        logger.info(f"[DOCS_CHAT] 요청 수신: {request.message[:50]}...")
        
        # 세션 ID 생성 또는 사용
        session_id = request.session_id or str(uuid.uuid4())
        
        # docs_agent 실행
        result = docs_agent.run(user_input=request.message)
        
        # 응답 구성
        response = ChatResponse(
            success=result.get("success", False),
            session_id=session_id,
            error=result.get("error")
        )
        
        if result.get("success"):
            # 성공적인 완료
            result_data = result.get("result", {})
            response.response = "문서가 성공적으로 생성되었습니다."
            response.data = {
                "document_path": result_data.get("final_doc"),
                "document_type": result_data.get("doc_type"),
                "filled_data": result_data.get("filled_data")
            }
            
        elif result.get("interrupted"):
            # 인터럽트 필요
            response.requires_interrupt = True
            response.data = {
                "thread_id": result.get("thread_id"),
                "next_node": result.get("next_node"),
                "doc_type": result.get("doc_type"),
                "state_info": result.get("state_info", {})
            }
            
            # 세션 정보 저장
            sessions[session_id] = {
                "thread_id": result.get("thread_id"),
                "status": "interrupted",
                "last_activity": datetime.now()
            }
            
            # 노드별 프롬프트 설정
            next_node = result.get("next_node")
            doc_type = result.get("doc_type")
            
            if next_node == "process_verification_response":
                response.response = f"분류된 문서 타입: {doc_type}\n\n위 분류 결과가 올바른가요?"
                response.data["interrupt_type"] = "verification"
                response.data["prompt_type"] = "verification"
                
            elif next_node == "process_manual_doc_type_selection":
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
                state_info = result.get("state_info", {})
                template_content = state_info.get("template_content", "")
                if template_content:
                    response.response = template_content
                else:
                    response.response = "필요한 정보를 입력해주세요."
                response.data["interrupt_type"] = "data_input"
                response.data["template_content"] = template_content
                
            else:
                response.response = "추가 정보가 필요합니다."
                response.data["interrupt_type"] = "unknown"
                
        else:
            # 처리 실패
            if result.get("error"):
                response.error = result["error"]
            else:
                # 규정 위반 확인
                result_data = result.get("result", {})
                violation = result_data.get("violation", "")
                if violation and violation != "OK":
                    response.error = "규정 위반으로 인해 문서가 생성되지 않습니다. 위반 내용을 확인하고 수정 후 다시 시도해주세요."
                    response.data = {
                        "violation": violation,
                        "violation_type": "policy_violation"
                    }
                else:
                    response.error = "문서 작성 중 오류가 발생했습니다."
        
        # 메타데이터 추가
        response.metadata = {
            "timestamp": datetime.now().isoformat(),
            "agent_type": "docs_agent"
        }
        
        logger.info(f"[DOCS_CHAT] 응답 완료: success={response.success}")
        return response
        
    except Exception as e:
        logger.error(f"[DOCS_CHAT] 오류 발생: {str(e)}")
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
        logger.info(f"[DOCS_RESUME] 세션 재개: {session_id}")
        
        # 세션 확인
        if session_id not in sessions:
            return ChatResponse(
                success=False,
                session_id=session_id,
                error="세션을 찾을 수 없습니다."
            )
        
        session_info = sessions[session_id]
        thread_id = session_info.get("thread_id")
        
        # docs_agent 재개
        # docs_agent 가져오기
        docs_agent = get_docs_agent()
        result = docs_agent.resume(
            thread_id=thread_id,
            user_reply=request.user_reply,
            input_type=request.reply_type
        )
        
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
                    "violation_blocked": True
                }
            else:
                # 정상적으로 완료
                response.response = "문서가 성공적으로 생성되었습니다."
                response.data = {
                    "final_doc": result_data.get("final_doc") if isinstance(result_data, dict) else None,
                    "filled_data": result.get("filled_data") or (result_data.get("filled_data") if isinstance(result_data, dict) else None)
                }
            
            # 세션 완료 처리
            if session_id in sessions:
                del sessions[session_id]
                
        elif result.get("interrupted"):
            # 여전히 인터럽트 상태
            response.requires_interrupt = True
            response.response = "추가 정보가 필요합니다."
            response.data = {
                "thread_id": result.get("thread_id"),
                "next_node": result.get("next_node")
            }
            
            # 세션 정보 업데이트
            sessions[session_id]["last_activity"] = datetime.now()
            
            # next_node로 정확한 상황 판단
            next_node = result.get("next_node")
            doc_type = result.get("doc_type")
            
            if next_node == "process_verification_response":
                response.response = f"분류된 문서 타입: {doc_type}\n\n위 분류 결과가 올바른가요?"
                response.data["interrupt_type"] = "verification"
                response.data["prompt_type"] = "verification"
                response.data["doc_type"] = doc_type
                
            elif next_node == "process_manual_doc_type_selection":
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
                if session_id in sessions:
                    del sessions[session_id]
                return response
            
            # 에러 메시지 구성
            error_msg = "처리 중 오류가 발생했습니다."
            violation_text = None
            
            if result.get("error"):
                error_msg = f"오류 발생: {result['error']}"
            elif result.get("violation"):
                error_msg = "규정 위반으로 인해 문서가 생성되지 않습니다. 위반 내용을 확인하고 수정 후 다시 시도해주세요."
                violation_text = result.get("violation")
            elif result.get("error_type") == "policy_violation":
                error_msg = "규정 위반으로 인해 문서가 생성되지 않습니다. 위반 내용을 확인하고 수정 후 다시 시도해주세요."
                violation_text = result.get("violation")
            elif result.get("result") is None:
                error_msg = "문서 생성 실패: 결과가 없습니다."
            
            response.response = error_msg
            
            # result가 dict인지 확인하고 안전하게 처리
            if isinstance(result, dict):
                inner_result = result.get("result", {})
                
                # violation_text가 이미 설정되어 있지 않으면 inner_result에서 확인
                if not violation_text and isinstance(inner_result, dict):
                    violation_text = inner_result.get("violation")
                
                response.data = {
                    "error_type": result.get("error_type", "policy_violation" if violation_text else "processing_error"),
                    "violation": violation_text,
                    "details": result.get("details", result.get("error")),
                    "filled_data": inner_result.get("filled_data") if inner_result else None
                }
            else:
                response.data = {"error_type": "unknown_error"}
        
        logger.info(f"[DOCS_RESUME] 응답 완료: success={response.success}")
        return response
        
    except Exception as e:
        logger.error(f"[DOCS_RESUME] 오류 발생: {str(e)}")
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
        logger.info(f"[DOCS_STATUS] 세션 상태 조회: {session_id}")
        
        if session_id in sessions:
            session_info = sessions[session_id]
            return SessionStatusResponse(
                exists=True,
                session_id=session_id,
                status=session_info.get("status", "unknown"),
                thread_id=session_info.get("thread_id"),
                message="세션이 활성 상태입니다."
            )
        else:
            return SessionStatusResponse(
                exists=False,
                session_id=session_id,
                message="세션을 찾을 수 없습니다."
            )
        
    except Exception as e:
        logger.error(f"[DOCS_STATUS] 오류 발생: {str(e)}")
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
        "service": "docs-agent",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/templates")
async def list_templates():
    """
    사용 가능한 문서 템플릿 목록을 반환합니다.
    
    Returns:
        Dict: 문서 템플릿 목록 및 설명
    """
    return {
        "templates": [
            {
                "name": "영업방문 결과보고서",
                "description": "고객 방문 후 영업 결과를 보고하는 문서",
                "required_fields": [
                    "방문날짜", "고객명", "방문목적", "주요내용", "결과", "후속조치"
                ]
            },
            {
                "name": "제품설명회 시행 신청서",
                "description": "제품설명회 개최를 신청하는 문서",
                "required_fields": [
                    "제품명", "일시", "장소", "참석인원", "목적", "내용"
                ]
            },
            {
                "name": "제품설명회 시행 결과보고서",
                "description": "제품설명회 완료 후 결과를 보고하는 문서",
                "required_fields": [
                    "제품명", "일시", "장소", "참석인원", "진행내용", "결과", "피드백"
                ]
            }
        ]
    }