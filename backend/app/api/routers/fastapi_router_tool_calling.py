"""
메인 Agent Router 기반 채팅 API 엔드포인트
OpenAI Function Calling으로 4개 전문 Agent에 라우팅
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, AsyncGenerator
import logging
import json
import asyncio
from ...services.main_agent_router import MainAgentRouter

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 메인 Agent Router 인스턴스
main_agent_router = MainAgentRouter()

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    response: str
    agent: str
    arguments: Dict[str, Any]
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    session_id: Optional[str] = None
    error: Optional[str] = None

@router.post("/chat/stream")
async def agent_chat_stream(request: ChatMessage):
    """
    메인 Agent Router를 통해 4개 전문 Agent로 라우팅하여 스트리밍 방식으로 메시지를 처리합니다.
    
    Agent 종류:
    1. chroma_db_agent - 문서 검색 및 질문답변
    2. employee_db_agent - 직원 정보 검색
    3. client_analysis_agent - 고객 데이터 분석  
    4. rule_compliance_agent - 규정 준수 분석
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            logger.info(f"Agent chat stream request: {request.message}")
            
            # 시작 메시지 전송
            yield f"data: {json.dumps({'type': 'start', 'message': 'AI가 분석 중입니다...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Agent 선택 메시지
            yield f"data: {json.dumps({'type': 'agent_selection', 'message': '적절한 전문 Agent를 선택하고 있습니다...'})}\n\n"
            await asyncio.sleep(0.5)
            
            # 메인 Agent Router를 통해 메시지 처리
            result = await main_agent_router.route_message(
                message=request.message,
                session_id=request.session_id
            )
            
            if result.get('error'):
                yield f"data: {json.dumps({'type': 'error', 'message': result['error']})}\n\n"
                return
            
            # Agent 정보 전송
            agent_name = result.get('agent', 'unknown')
            yield f"data: {json.dumps({'type': 'agent_info', 'agent': agent_name, 'message': f'{agent_name} Agent가 처리합니다...'})}\n\n"
            await asyncio.sleep(0.3)
            
            # 응답을 청크 단위로 전송 (타이핑 효과)
            response_text = result.get('response', '')
            
            # 응답 텍스트를 단어 단위로 분할
            words = response_text.split()
            current_text = ""
            
            for i, word in enumerate(words):
                current_text += word + " "
                
                # 단어별로 스트리밍 (더 자연스러운 타이핑 효과)
                yield f"data: {json.dumps({'type': 'content', 'content': current_text.strip(), 'is_final': i == len(words) - 1})}\n\n"
                await asyncio.sleep(0.05)  # 50ms 딜레이로 타이핑 효과
            
            # 최종 메타데이터 전송
            final_data = {
                'type': 'complete',
                'agent': result.get('agent', 'unknown'),
                'arguments': result.get('arguments', {}),
                'sources': result.get('sources', []),
                'metadata': result.get('metadata', {}),
                'session_id': request.session_id
            }
            
            yield f"data: {json.dumps(final_data)}\n\n"
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Agent chat stream error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'스트리밍 처리 중 오류가 발생했습니다: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

@router.post("/chat", response_model=ChatResponse)
async def agent_chat(request: ChatMessage):
    """
    메인 Agent Router를 통해 4개 전문 Agent로 라우팅하여 메시지를 처리합니다.
    
    Agent 종류:
    1. chroma_db_agent - 문서 검색 및 질문답변
    2. employee_db_agent - 직원 정보 검색
    3. client_analysis_agent - 고객 데이터 분석  
    4. rule_compliance_agent - 규정 준수 분석
    """
    try:
        logger.info(f"Agent chat request: {request.message}")
        
        # 메인 Agent Router를 통해 메시지 처리
        result = await main_agent_router.route_message(
            message=request.message,
            session_id=request.session_id
        )
        
        logger.info(f"Agent chat response - Agent: {result.get('agent', 'unknown')}")
        
        return ChatResponse(
            response=result.get("response", ""),
            agent=result.get("agent", "unknown"),
            arguments=result.get("arguments", {}),
            sources=result.get("sources", []),
            metadata=result.get("metadata", {}),
            session_id=request.session_id,
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Agent chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent chat failed: {str(e)}"
        )

@router.get("/agents")
async def get_available_agents():
    """
    사용 가능한 Agent들의 목록을 반환합니다.
    """
    try:
        agents_info = []
        for func in main_agent_router.agent_functions:
            function_def = func["function"]
            agents_info.append({
                "name": function_def["name"],
                "description": function_def["description"],
                "parameters": function_def["parameters"]
            })
        
        return {
            "agents": agents_info,
            "count": len(agents_info)
        }
        
    except Exception as e:
        logger.error(f"Get agents error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agents: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    메인 Agent Router 상태 확인
    """
    return {
        "status": "healthy",
        "router_type": "main_agent_router", 
        "message": "Main Agent Router is running",
        "agents": ["chroma_db_agent", "employee_db_agent", "client_analysis_agent", "rule_compliance_agent"]
    }

@router.get("/info")
async def get_router_info():
    """
    메인 Agent Router 정보
    """
    return {
        "name": "Main Agent Router",
        "version": "1.0.0",
        "description": "OpenAI Function Calling 기반 4개 전문 Agent 라우터",
        "agents": {
            "chroma_db_agent": "ChromaDB 문서 검색 및 질문답변",
            "employee_db_agent": "직원 정보 검색",
            "client_analysis_agent": "고객 데이터 분석",
            "rule_compliance_agent": "규정 준수 분석"
        },
        "endpoints": ["/chat", "/agents", "/health", "/info"]
    } 