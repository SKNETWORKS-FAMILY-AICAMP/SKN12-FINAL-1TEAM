"""
Create Document Agent Run Module
"""
from typing import Dict, Any

async def run(query: str, session_id: str) -> Dict[str, Any]:
    """문서 생성 관련 쿼리 처리"""
    
    # 간단한 키워드 분석
    query_lower = query.lower()
    
    if "보고서" in query_lower:
        response = f"보고서 생성 중:\n- 요청: {query}\n- 보고서 템플릿을 준비하고 있습니다..."
        doc_type = "report"
    elif "문서" in query_lower:
        response = f"문서 생성 중:\n- 요청: {query}\n- 문서 템플릿을 생성하고 있습니다..."
        doc_type = "document"
    elif "작성" in query_lower:
        response = f"문서 작성 중:\n- 요청: {query}\n- 요청하신 내용을 작성하고 있습니다..."
        doc_type = "draft"
    else:
        response = f"문서 처리 중:\n- 요청: {query}\n- 적절한 문서 형식을 선택하고 있습니다..."
        doc_type = "general"
    
    return {
        "success": True,
        "response": response,
        "report": f"[Document Agent]\n{response}",
        "agent": "create_document_agent",
        "session_id": session_id,
        "state": {
            "doc_type": doc_type,
            "template_content": f"{doc_type} 템플릿이 준비되었습니다."
        }
    }