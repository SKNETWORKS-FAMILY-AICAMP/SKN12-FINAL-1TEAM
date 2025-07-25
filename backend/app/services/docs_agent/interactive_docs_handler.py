from typing import Dict, Any, Optional, Tuple
from enum import Enum
import json
from .classify_docs import DocumentClassifyAgent
from .write_docs import DocumentDraftAgent

class DocsSessionStage(Enum):
    """문서 작성 세션의 단계"""
    INITIAL = "initial"              # 초기 상태
    CLASSIFIED = "classified"        # 문서 분류 완료
    WAITING_INPUT = "waiting_input"  # 사용자 입력 대기
    PROCESSING = "processing"        # 문서 작성 중
    COMPLETED = "completed"          # 완료
    ERROR = "error"                  # 오류

class InteractiveDocsHandler:
    """사용자와 상호작용하는 문서 작성 핸들러"""
    
    def __init__(self):
        self.classify_agent = DocumentClassifyAgent()
        self.write_agent = DocumentDraftAgent()
        # 세션별 상태 저장 (실제 운영에서는 Redis나 DB 사용 권장)
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """세션 상태 조회"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "stage": DocsSessionStage.INITIAL.value,
                "doc_type": None,
                "template_content": None,
                "classify_result": None,
                "user_input_history": [],
                "error_message": None
            }
        return self.sessions[session_id]
    
    def update_session_state(self, session_id: str, updates: Dict[str, Any]):
        """세션 상태 업데이트"""
        session_state = self.get_session_state(session_id)
        session_state.update(updates)
        self.sessions[session_id] = session_state
    
    def clear_session(self, session_id: str):
        """세션 초기화"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def process_initial_request(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """초기 사용자 요청 처리 (문서 분류)"""
        try:
            # 1. 문서 분류 실행
            classify_result = self.classify_agent.run(user_input)
            
            if not classify_result:
                return {
                    "success": False,
                    "stage": DocsSessionStage.ERROR.value,
                    "message": "문서 분류에 실패했습니다. 다시 시도해주세요.",
                    "error": "classification_failed"
                }
            
            # 2. 분류 결과에서 정보 추출
            doc_type = classify_result.get("doc_type")
            template_content = classify_result.get("template_content", "")
            
            # 3. 세션 상태 업데이트
            self.update_session_state(session_id, {
                "stage": DocsSessionStage.CLASSIFIED.value,
                "doc_type": doc_type,
                "template_content": template_content,
                "classify_result": dict(classify_result),
                "user_input_history": [user_input]
            })
            
            # 4. 사용자에게 템플릿 제공
            return {
                "success": True,
                "stage": DocsSessionStage.WAITING_INPUT.value,
                "doc_type": doc_type,
                "message": f"📄 **{doc_type}** 작성을 시작합니다.\n\n다음 정보를 입력해주세요:",
                "template": template_content,
                "requires_user_input": True,
                "session_id": session_id
            }
            
        except Exception as e:
            self.update_session_state(session_id, {
                "stage": DocsSessionStage.ERROR.value,
                "error_message": str(e)
            })
            
            return {
                "success": False,
                "stage": DocsSessionStage.ERROR.value,
                "message": f"문서 분류 중 오류가 발생했습니다: {str(e)}",
                "error": "classification_error"
            }
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """사용자 입력 처리 (문서 작성)"""
        try:
            session_state = self.get_session_state(session_id)
            
            # 세션 상태 확인
            if session_state["stage"] not in [DocsSessionStage.CLASSIFIED.value, DocsSessionStage.WAITING_INPUT.value]:
                return {
                    "success": False,
                    "message": "잘못된 세션 상태입니다. 새로 시작해주세요.",
                    "error": "invalid_session_state"
                }
            
            # 문서 작성 실행
            classify_result = session_state["classify_result"]
            if not classify_result:
                return {
                    "success": False,
                    "message": "분류 정보가 없습니다. 새로 시작해주세요.",
                    "error": "missing_classification"
                }
            
            # 사용자 입력 히스토리 업데이트
            session_state["user_input_history"].append(user_input)
            
            # 문서 작성 에이전트 실행
            self.update_session_state(session_id, {"stage": DocsSessionStage.PROCESSING.value})
            
            write_result = self.write_agent.run_with_state(classify_result, user_input)
            
            if not write_result:
                self.update_session_state(session_id, {
                    "stage": DocsSessionStage.ERROR.value,
                    "error_message": "문서 작성 실패"
                })
                
                return {
                    "success": False,
                    "stage": DocsSessionStage.ERROR.value,
                    "message": "문서 작성에 실패했습니다. 입력 정보를 확인하고 다시 시도해주세요.",
                    "error": "document_creation_failed"
                }
            
            # 성공적으로 완료
            self.update_session_state(session_id, {
                "stage": DocsSessionStage.COMPLETED.value,
                "final_document": write_result
            })
            
            return {
                "success": True,
                "stage": DocsSessionStage.COMPLETED.value,
                "doc_type": session_state["doc_type"],
                "message": f"📄 **{session_state['doc_type']}** 작성이 완료되었습니다!",
                "document": write_result,
                "session_completed": True
            }
            
        except Exception as e:
            self.update_session_state(session_id, {
                "stage": DocsSessionStage.ERROR.value,
                "error_message": str(e)
            })
            
            return {
                "success": False,
                "stage": DocsSessionStage.ERROR.value,
                "message": f"문서 작성 중 오류가 발생했습니다: {str(e)}",
                "error": "document_creation_error"
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """세션 상태 조회"""
        session_state = self.get_session_state(session_id)
        
        return {
            "session_id": session_id,
            "stage": session_state["stage"],
            "doc_type": session_state.get("doc_type"),
            "has_template": bool(session_state.get("template_content")),
            "input_count": len(session_state.get("user_input_history", [])),
            "is_completed": session_state["stage"] == DocsSessionStage.COMPLETED.value,
            "has_error": session_state["stage"] == DocsSessionStage.ERROR.value,
            "error_message": session_state.get("error_message")
        }
    
    def reset_session(self, session_id: str) -> Dict[str, Any]:
        """세션 리셋"""
        self.clear_session(session_id)
        
        return {
            "success": True,
            "message": "세션이 초기화되었습니다. 새로운 문서 작성을 시작할 수 있습니다.",
            "session_id": session_id,
            "stage": DocsSessionStage.INITIAL.value
        }

# 전역 핸들러 인스턴스 (싱글톤 패턴)
interactive_handler = InteractiveDocsHandler() 