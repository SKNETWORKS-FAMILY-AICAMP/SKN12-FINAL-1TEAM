import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..services.docs_agent.classify_docs import DocumentClassifyAgent
from ..services.docs_agent.write_docs import DocumentDraftAgent

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