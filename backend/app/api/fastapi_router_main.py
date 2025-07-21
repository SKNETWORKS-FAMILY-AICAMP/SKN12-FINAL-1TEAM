"""
메인 API 라우터

LangGraph StateGraph 기반 State Management 시스템
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

# API 라우터 생성
api_router = APIRouter()

# 🚀 State Management 기반 Tool Calling 라우터 시스템
try:
    from .routers.fastapi_router_tool_calling import router as state_managed_router
    api_router.include_router(state_managed_router, prefix="/tool-calling", tags=["State Managed Chat"])
    logger.info("✅ State Management 시스템 로드 완료")
    logger.info("   - LangGraph StateGraph 기반")
    logger.info("   - 세션별 대화 기록 관리")
    logger.info("   - 컨텍스트 유지 및 상태 지속성")
    logger.info("   - 4개 전문 Agent 자동 라우팅")
except Exception as e:
    logger.warning(f"❌ State Management 시스템 로드 실패: {str(e)}")

# 👤 Employee Agent 전용 API 라우터
try:
    from .employee_api import employee_router
    api_router.include_router(employee_router, tags=["Employee Analysis"])
    logger.info("✅ Employee Agent API 로드 완료")
    logger.info("   - 직원 실적 분석")
    logger.info("   - 실적 요약 조회")
    logger.info("   - 보고서 생성")
except Exception as e:
    logger.warning(f"❌ Employee Agent API 로드 실패: {str(e)}")

# 메인 시스템 정보 엔드포인트
@api_router.get("/system/info")
async def system_info():
    """시스템 정보"""
    return {
        "system": "NaruTalk AI 챗봇",
        "version": "2.0.0",
        "architecture": "LangGraph StateGraph + Session Management",
        "features": [
            "🔄 LangGraph StateGraph 기반 대화 흐름",
            "💾 세션별 대화 기록 자동 저장",
            "🧠 컨텍스트 유지 및 상태 지속성",
            "🤖 4개 전문 Agent 자동 라우팅",
            "📊 실시간 세션 관리 및 통계",
            "🔍 대화 기록 검색 및 분석"
        ],
        "agents": {
            "chroma_db_agent": { 
                "name": "문서 검색 에이전트",
                "description": "ChromaDB 기반 회사 문서 검색 및 질문답변",
                "capabilities": ["정책 검색", "규정 조회", "매뉴얼 검색"]
            },
            "employee_db_agent": {
                "name": "직원 정보 에이전트", 
                "description": "직원 데이터베이스 검색 및 조직 관리",
                "capabilities": ["직원 검색", "조직도 확인", "연락처 조회"]
            },
            "client_analysis_agent": {
                "name": "고객 분석 에이전트",
                "description": "고객 데이터 분석 및 비즈니스 인사이트",
                "capabilities": ["고객 분석", "매출 분석", "거래 현황 분석"]
            },
            "rule_compliance_agent": {
                "name": "규정 준수 에이전트",
                "description": "컴플라이언스 및 규정 준수 분석",
                "capabilities": ["규정 검토", "위험 분석", "준수성 확인"]
            }
        },
        "endpoints": {
            "chat": "/api/v1/tool-calling/chat",
            "chat_stream": "/api/v1/tool-calling/chat/stream",
            "conversation_history": "/api/v1/tool-calling/conversation/history/{session_id}",
            "session_stats": "/api/v1/tool-calling/session/stats/{session_id}",
            "session_delete": "/api/v1/tool-calling/session/{session_id}",
            "session_cleanup": "/api/v1/tool-calling/session/cleanup",
            "health": "/api/v1/tool-calling/health"
        }
    }

# 메인 채팅 안내 엔드포인트 (Legacy 호환성)
@api_router.get("/chat/info")
async def chat_info():
    """채팅 API 안내 (Legacy 호환성)"""
    return {
        "message": "NaruTalk AI 챗봇이 State Management 시스템으로 업그레이드되었습니다!",
        "new_features": [
            "🔄 LangGraph StateGraph 기반 대화 흐름 관리",
            "💾 세션별 대화 기록 자동 저장 및 복원",
            "🧠 이전 대화 컨텍스트 유지",
            "📊 실시간 세션 통계 및 관리",
            "🤖 개선된 4개 전문 Agent 라우팅"
        ],
        "migration_guide": {
            "old_endpoint": "/api/v1/chat",
            "new_endpoint": "/api/v1/tool-calling/chat",
            "changes": [
                "session_id가 자동 생성 및 관리됨",
                "user_id 필드 추가 (선택사항)",
                "대화 기록 자동 저장",
                "컨텍스트 유지로 더 자연스러운 대화"
            ]
        },
        "example_usage": {
            "url": "/api/v1/tool-calling/chat",
            "method": "POST",
            "body": {
                "message": "회사 복리후생 정책 알려줘",
                "session_id": "optional_session_id",
                "user_id": "optional_user_id"
            },
            "response": {
                "response": "AI 응답 내용",
                "agent": "chroma_db_agent",
                "sources": [],
                "metadata": {},
                "session_id": "auto_generated_session_id"
            }
        }
    }

# 헬스 체크 (전체 시스템)
@api_router.get("/health")
async def system_health():
    """전체 시스템 헬스 체크"""
    try:
        # State Manager 헬스 체크 (import해서 확인)
        from ..services.state_management import StateManager
        
        # 간단한 상태 확인
        state_manager = StateManager()
        session_count = state_manager.session_manager.get_active_sessions_count()
        
        return {
            "status": "healthy",
            "system": "NaruTalk AI 챗봇 v2.0",
            "components": {
                "state_manager": "healthy",
                "session_manager": "healthy", 
                "conversation_store": "healthy",
                "langgraph_workflow": "healthy",
                "agent_router": "healthy"
            },
            "statistics": {
                "active_sessions": session_count,
                "system_uptime": "running",
                "api_version": "v1"
            },
            "endpoints_available": [
                "/api/v1/tool-calling/chat",
                "/api/v1/tool-calling/chat/stream", 
                "/api/v1/tool-calling/conversation/history/{session_id}",
                "/api/v1/tool-calling/session/stats/{session_id}",
                "/api/v1/system/info"
            ]
        }
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return {
            "status": "degraded",
            "system": "NaruTalk AI 챗봇 v2.0",
            "error": str(e),
            "message": "일부 기능에 제한이 있을 수 있습니다."
        }

# 기본 루트 엔드포인트
@api_router.get("/")
async def api_root():
    """API 루트"""
    return {
        "message": "NaruTalk AI 챗봇 API v2.0",
        "description": "LangGraph StateGraph 기반 State Management 시스템",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "system_info": "/api/v1/system/info",
        "main_chat": "/api/v1/tool-calling/chat"
    } 