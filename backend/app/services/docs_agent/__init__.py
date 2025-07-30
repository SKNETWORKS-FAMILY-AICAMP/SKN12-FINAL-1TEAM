"""
Docs Agent Module
문서 생성 에이전트 모듈
"""
from typing import Dict, Any
from .create_document_agent import CreateDocumentAgent

# 에이전트 인스턴스 생성 (싱글톤)
_agent_instance = None

def get_agent_instance():
    """에이전트 인스턴스 반환 (싱글톤 패턴)"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CreateDocumentAgent()
    return _agent_instance

async def run(query: str, session_id: str) -> Dict[str, Any]:
    """
    문서 생성 에이전트 실행
    router_api.py에서 호출하는 표준 인터페이스
    
    Args:
        query: 사용자 질의
        session_id: 세션 ID
        
    Returns:
        Dict[str, Any]: 실행 결과
    """
    try:
        # 에이전트 인스턴스 가져오기
        agent = get_agent_instance()
        
        # 에이전트 실행 (동기 메서드이므로 직접 호출)
        result = agent.run(user_input=query)
        
        # 결과 포맷 변환
        if result.get("success"):
            return {
                "success": True,
                "response": result.get("result", "문서 생성이 완료되었습니다."),
                "report": f"[Docs Agent]\n{result.get('result', '')}",
                "agent": "docs_agent",
                "session_id": session_id,
                "thread_id": result.get("thread_id"),
                "state": {
                    "doc_type": result.get("doc_type"),
                    "final_doc": result.get("final_doc"),
                    "template_content": result.get("template_content")
                }
            }
        else:
            return {
                "success": False,
                "response": f"문서 생성 중 오류가 발생했습니다: {result.get('error', 'Unknown error')}",
                "error": result.get("error"),
                "agent": "docs_agent",
                "session_id": session_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "response": f"문서 생성 에이전트 실행 중 오류가 발생했습니다: {str(e)}",
            "error": str(e),
            "agent": "docs_agent",
            "session_id": session_id
        }

# 하위 호환성을 위한 별칭
process_query = run