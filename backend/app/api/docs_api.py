import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.docs_agent.classify_docs import DocumentClassifyAgent
from services.docs_agent.write_docs import DocumentDraftAgent
from services.docs_agent.interactive_docs_handler import interactive_handler

# .env 로드 (현재 경로와 상위 경로에서 찾기)
current_env = Path(__file__).parent / ".env"
parent_env = Path(__file__).resolve().parents[1] / ".env"

if current_env.exists():
    load_dotenv(dotenv_path=current_env)
    print(f"✅ docs_api.py - .env 로드됨: {current_env}")
elif parent_env.exists():
    load_dotenv(dotenv_path=parent_env)
    print(f"✅ docs_api.py - .env 로드됨: {parent_env}")
else:
    print("⚠️ docs_api.py - .env 파일을 찾을 수 없습니다")

# OPENAI_API_KEY 확인용 로그
print("docs_api.py - OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY")[:10] if os.getenv("OPENAI_API_KEY") else "없음")

router = APIRouter()

# ────────────────────────────────────────────────────────────────────────────────
# 기존 엔드포인트 (레거시 호환성)
# ────────────────────────────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    user_input: str

class ClassifyResponse(BaseModel):
    success: bool
    state: Optional[Dict[str, Any]]
    error: Optional[str]

class WriteRequest(BaseModel):
    state: Dict[str, Any]
    user_input: str

class WriteResponse(BaseModel):
    success: bool
    filled_data: Optional[Dict[str, Any]]
    error: Optional[str]

@router.post("/classify", response_model=ClassifyResponse)
async def classify_document(request: ClassifyRequest):
    try:
        agent = DocumentClassifyAgent()
        result = agent.run(request.user_input)
        
        if result:
            return ClassifyResponse(
                success=True,
                state=dict(result),
                error=None
            )
        else:
            return ClassifyResponse(
                success=False,
                state=None,
                error="문서 분류에 실패했습니다."
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분류 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/write", response_model=WriteResponse)
async def write_document(request: WriteRequest):
    try:
        agent = DocumentDraftAgent()
        result = agent.run_with_state(request.state, request.user_input)
        
        if result:
            return WriteResponse(
                success=True,
                filled_data=result,
                error=None
            )
        else:
            return WriteResponse(
                success=False,
                filled_data=None,
                error="문서 초안 작성에 실패했습니다."
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 작성 처리 중 오류가 발생했습니다: {str(e)}")

# ────────────────────────────────────────────────────────────────────────────────
# 새로운 상호작용 엔드포인트
# ────────────────────────────────────────────────────────────────────────────────

class InteractiveRequest(BaseModel):
    session_id: str
    user_input: str
    is_initial: Optional[bool] = None  # True면 초기 요청, False면 후속 입력

class InteractiveResponse(BaseModel):
    success: bool
    stage: str
    message: str
    doc_type: Optional[str] = None
    template: Optional[str] = None
    document: Optional[Dict[str, Any]] = None
    requires_user_input: Optional[bool] = None
    session_completed: Optional[bool] = None
    error: Optional[str] = None

class SessionStatusResponse(BaseModel):
    session_id: str
    stage: str
    doc_type: Optional[str]
    has_template: bool
    input_count: int
    is_completed: bool
    has_error: bool
    error_message: Optional[str]

@router.post("/interactive", response_model=InteractiveResponse)
async def interactive_document_process(request: InteractiveRequest):
    """
    사용자와 상호작용하는 문서 작성 처리
    
    - is_initial=True: 초기 문서 분류 요청
    - is_initial=False 또는 None: 사용자 입력 처리 (문서 작성)
    """
    try:
        # 세션 상태 확인
        session_status = interactive_handler.get_session_status(request.session_id)
        
        # 초기 요청인지 판단
        if request.is_initial or session_status["stage"] == "initial":
            # 초기 분류 처리
            result = interactive_handler.process_initial_request(
                request.session_id, 
                request.user_input
            )
        else:
            # 사용자 입력 처리 (문서 작성)
            result = interactive_handler.process_user_input(
                request.session_id, 
                request.user_input
            )
        
        return InteractiveResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"상호작용 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """세션 상태 조회"""
    try:
        status = interactive_handler.get_session_status(session_id)
        return SessionStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"세션 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/reset/{session_id}")
async def reset_session(session_id: str):
    """세션 리셋"""
    try:
        result = interactive_handler.reset_session(session_id)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"세션 리셋 중 오류가 발생했습니다: {str(e)}"
        )