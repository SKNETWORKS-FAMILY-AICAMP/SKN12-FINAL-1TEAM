"""
메인 API 라우터

새로운 모듈화된 라우터 시스템의 메인 라우터입니다.
서비스 초기화 오류를 방지하기 위해 지연 로딩을 사용합니다.
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

# API 라우터 생성
api_router = APIRouter()

# 서브 라우터 지연 로딩 (존재하지 않는 routes 디렉토리 주석 처리)
# try:
#     from .routes.router import router as routes_router
#     # 서브 라우터 포함 (prefix 제거 - main.py에서 이미 설정됨)
#     api_router.include_router(routes_router)
#     logger.info("라우터 서브 모듈 로드 완료")
# except Exception as e:
#     logger.warning(f"라우터 서브 모듈 로드 실패: {str(e)}")
logger.info("기본 라우터 시스템 로드 완료")

# 🔧 Tool Calling 라우터 시스템 추가
try:
    from .routers.fastapi_router_tool_calling import router as tool_calling_router
    api_router.include_router(tool_calling_router, prefix="/tool-calling", tags=["Tool Calling 라우터"])
    logger.info("Tool Calling 라우터 시스템 로드 완료")
except Exception as e:
    logger.warning(f"Tool Calling 라우터 시스템 로드 실패: {str(e)}")

# 🚀 간단한 라우터 시스템 - 삭제됨 (새로운 Agent 시스템으로 통합)
# try:
#     from .routers.fastapi_router_simple import router as simple_router
#     api_router.include_router(simple_router, prefix="/api", tags=["간단한 라우터"])
#     logger.info("간단한 라우터 시스템 로드 완료")
# except Exception as e:
#     logger.warning(f"간단한 라우터 시스템 로드 실패: {str(e)}")
logger.info("간단한 라우터는 Tool Calling 라우터로 통합되었습니다")

# 📄 문서 라우터 시스템 추가 (Legacy 4개 전문 에이전트) - 현재 비활성화
# try:
#     from .routers.fastapi_router_document import router as document_router
#     api_router.include_router(document_router, prefix="/agents", tags=["4개 전문 에이전트"])
#     logger.info("4개 전문 에이전트 채팅 라우터 로드 완료")
# except Exception as e:
#     logger.warning(f"4개 전문 에이전트 채팅 라우터 로드 실패: {str(e)}")
logger.info("문서 라우터는 현재 agent_router_manager 구현 완료 후 활성화 예정")

# 메인 채팅 안내 엔드포인트 (실제 채팅은 /tool-calling/chat 사용)
@api_router.get("/chat/info")
async def chat_info():
    """채팅 API 안내"""
    return {
        "message": "채팅 기능이 새로운 Agent 시스템으로 이전되었습니다",
        "new_endpoint": "/api/v1/tool-calling/chat",
        "method": "POST",
        "available_agents": [
            "📄 ChromaDB Agent - 문서 검색 및 질문답변",
            "👥 Employee DB Agent - 직원 정보 검색", 
            "📊 Client Analysis Agent - 고객 데이터 분석",
            "📋 Rule Compliance Agent - 규정 준수 분석"
        ],
        "example": {
            "url": "/api/v1/tool-calling/chat",
            "method": "POST",
            "body": {
                "message": "회사 복리후생 정책 알려줘",
                "session_id": "optional_session_id"
            }
        }
    }

# 기본 라우터 생성
@api_router.get("/test")
async def test_fallback():
    """기본 테스트 엔드포인트"""
    return {
        "success": True,
        "message": "기본 API가 정상적으로 작동하고 있습니다.",
        "warning": "일부 서비스가 제한 모드로 실행 중입니다."
    }

@api_router.get("/health")
async def health_fallback():
    """기본 헬스 체크"""
    return {
        "status": "limited",
        "message": "기본 기능만 사용 가능합니다.",
        "services": {
            "embedding": False,
            "database": False,
            "openai": False
        }
    } 