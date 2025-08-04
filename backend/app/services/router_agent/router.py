"""
Router Agent - 세션 기반 라우팅 시스템
동적 도구 생성과 대화 연속성을 지원합니다.
"""
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
import logging
from datetime import datetime
import uuid
import os

from ..employee_agent.employee_agent import EnhancedEmployeeAgent
from ..docs_agent import CreateDocumentAgent
from ..client_agent import client_agent
from ..search_agent import run as search_agent_run
import asyncio

# 분리된 모듈에서 import
from .graph import RouterState, create_graph
from ..tools.router_tools import create_tools_from_config

logger = logging.getLogger(__name__)


class RouterAgent:
    """세션 기반 Router Agent"""
    
    def __init__(self):
        # 에이전트 설정 (메타데이터 포함)
        self.agents_config = {
            "docs_agent": {
                "instance": CreateDocumentAgent(api_mode=True),  # API 모드로 초기화
                "metadata": {
                    "description": "문서 자동 생성 및 규정 검토를 담당합니다. 문서생성시 규정위반 여부도 검토합니다.",
                    "capabilities": [
                        "영업방문 결과보고서 작성",
                        "제품설명회 시행 신청서 작성",
                        "제품설명회 시행 결과보고서 작성",

                    ],
                    "examples": [
                        "영업방문 보고서 작성해줘",
                        "제품설명회 신청서 만들어줘",
                        "문서 작성 도와줘"
                    ]
                }
            },
            "employee_agent": {
                "instance": EnhancedEmployeeAgent(),
                "metadata": {
                    "description": "사내 직원에 대한 정보 제공을 담당합니다",
                    "capabilities": [
                        "개인 실적 조회 및 분석",
                        "인사 이력, 직책, 소속 부서 확인",
                        "성과 평가 및 목표 달성률 분석",
                        "실적 트렌드 분석"
                    ],
                    "examples": [
                        "최수아 실적 분석해줘",
                        "서부팀 성과 보여줘",
                        "최수아 이번달 달성률이 얼마지?"
                    ]
                }
            },
            "client_agent": {
                "instance": client_agent.agent,
                "metadata": {
                    "description": "고객 및 거래처에 대한 정보를 제공합니다. 테이블데이터에서 요청한 정보를 분석합니다. 사용자 질의를 바탕으로 필요한 tool을 호출합니다.",
                    "capabilities": [
                        "병원명,월별 실적 활동 정보 조회",
                        "매출 추이 분석",
                        "기준점을 제시하면 다른 수치와 비교,분석",
                        "고객 등급 분류",
                        "병원 전체매출과 우리 매출 비교"
                    ],
                    "examples": [
                        "미라클신경과 실적분석해줘",
                        "미라클신경과와 우리가족의원 비교",
                        "최근 3개월 실적 트렌드 분석"
                    ]
                }
            },
            "search_agent": {
                "instance": "search",  # 플래그로 사용
                "metadata": {
                    "description": "내부 데이터베이스에서 정보 검색을 수행합니다",
                    "capabilities": [
                        "문서 검색",
                        "사내 규정 및 정책 조회",
                        "업무 매뉴얼 검색",
                        "제품 정보 조회",
                        "교육 자료 검색"
                    ],
                    "examples": [
                        "영업 규정 찾아줘",
                        "제품 설명서 검색",
                        "교육 자료 조회"
                    ]
                }
            }
        }
        
        # 세션 저장소
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # 동적으로 도구 생성
        self.tools = create_tools_from_config(self.agents_config, self._execute_agent)
        
        # LLM with tools
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        ).bind_tools(self.tools)
        
        # Graph 생성
        self.graph = create_graph(self)
    
    
    def _get_agent_descriptions(self) -> List[Dict[str, Any]]:
        """모든 에이전트의 상세 설명 반환"""
        descriptions = []
        
        for agent_name, config in self.agents_config.items():
            if config["instance"] is not None:  # 구현된 에이전트만
                metadata = config["metadata"]
                descriptions.append({
                    "id": agent_name,
                    "name": self._get_agent_display_name(agent_name),
                    "description": metadata["description"],
                    "capabilities": metadata.get("capabilities", []),
                    "examples": metadata.get("examples", [])
                })
        
        return descriptions
    
    def _get_agent_display_name(self, agent_name: str) -> str:
        """에이전트 표시 이름 반환"""
        display_names = {
            "docs_agent": "📄 문서 작성 도우미",
            "employee_agent": "👥 직원 정보 조회",
            "client_agent": "🏢 거래처 분석",
            "search_agent": "🔍 정보 검색"
        }
        return display_names.get(agent_name, agent_name)
    
    def _generate_help_message(self) -> str:
        """도움말 메시지 생성"""
        message = "죄송합니다. 요청하신 작업을 정확히 이해하지 못했습니다.\n\n"
        message += "다음과 같은 작업을 도와드릴 수 있습니다:\n\n"
        
        for agent_name, config in self.agents_config.items():
            if config["instance"] is not None:
                metadata = config["metadata"]
                message += f"**{self._get_agent_display_name(agent_name)}**\n"
                message += f"{metadata['description']}\n"
                if metadata.get("examples"):
                    message += "예시:\n"
                    for ex in metadata["examples"]:
                        message += f"  - {ex}\n"
                message += "\n"
        
        message += "원하시는 작업을 구체적으로 말씀해주세요."
        return message
    
    def _execute_agent(self, agent_name: str, query: str) -> Dict[str, Any]:
        """에이전트 실행"""
        try:
            logger.info(f"[EXECUTE_AGENT] Starting {agent_name} with query: {query[:50]}...")
            
            config = self.agents_config.get(agent_name)
            if not config or not config["instance"]:
                return {
                    "success": False,
                    "error": f"{agent_name}는 아직 구현되지 않았습니다.",
                    "message": "담당자에게 문의해주세요."
                }
            
            agent = config["instance"]
            
            # 현재 state에서 정보 추출
            current_state = getattr(self, 'current_state', {})
            logger.info(f"[EXECUTE_AGENT] Current state keys: {list(current_state.keys()) if current_state else 'None'}")
            session_id = current_state.get("session_id")
            context = current_state.get("context", {})
            
            # 에이전트별 실행
            if agent_name == "docs_agent":
                logger.info(f"[EXECUTE_AGENT] Running docs_agent in API mode")
                try:
                    # docs_agent는 이미 API 모드로 초기화됨
                    result = agent.run(user_input=query)
                    logger.info(f"[EXECUTE_AGENT] docs_agent result keys: {list(result.keys()) if result else 'None'}")
                    
                    # 인터럽트 처리
                    if isinstance(result, dict) and result.get("interrupted"):
                        logger.info(f"[EXECUTE_AGENT] Interrupt detected - next_node: {result.get('next_node')}, doc_type: {result.get('doc_type')}")
                        
                        # router의 current_state에 모든 인터럽트 정보 저장
                        current_state["requires_interrupt"] = True
                        current_state["agent_type"] = agent_name
                        current_state["thread_id"] = result.get("thread_id")
                        current_state["next_node"] = result.get("next_node")
                        current_state["doc_type"] = result.get("doc_type")
                        current_state["state_info"] = result.get("state_info", {})
                        
                        # 세션 정보 업데이트
                        if session_id:
                            logger.info(f"[EXECUTE_AGENT] Saving session for {session_id} with thread_id: {result.get('thread_id')}")
                            self.sessions[session_id] = {
                                "agent": agent_name,
                                "thread_id": result.get("thread_id"),
                                "active": True,
                                "context": context,
                                "next_node": result.get("next_node"),
                                "doc_type": result.get("doc_type"),
                                "state_info": result.get("state_info", {})
                            }
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"[EXECUTE_AGENT] docs_agent error: {e}")
                    return {"success": False, "error": str(e)}
            
            elif agent_name == "employee_agent":
                # employee_agent는 analyze_employee_performance 메서드 사용
                if hasattr(agent, 'analyze_employee_performance'):
                    result = agent.analyze_employee_performance(query)
                else:
                    result = agent.run(query)
                
                current_state["agent_type"] = agent_name
                return result
            
            elif agent_name == "client_agent":
                # client_agent는 async 함수
                logger.info(f"[EXECUTE_AGENT] Running client_agent with query: {query[:50]}...")
                result = asyncio.run(client_agent.run(query, session_id or "default"))
                
                current_state["agent_type"] = agent_name
                return result
            
            elif agent_name == "search_agent":
                # search_agent는 async 함수
                logger.info(f"[EXECUTE_AGENT] Running search_agent with query: {query[:50]}...")
                result = asyncio.run(search_agent_run(query, session_id or "default"))
                
                current_state["agent_type"] = agent_name
                return result
            
            else:
                # 다른 에이전트들
                return agent.run(query)
                
        except Exception as e:
            logger.error(f"{agent_name} execution error: {e}")
            return {"success": False, "error": str(e)}
    
    
    
    
    
    
    
    
    def run(self, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Router 실행"""
        # 세션 ID 생성 또는 사용
        if not session_id:
            session_id = str(uuid.uuid4())
        
        initial_state = RouterState(
            messages=[],
            user_input=user_input,
            session_id=session_id,
            active_agent=None,
            is_continuation=False,
            context={},
            result=None,
            error=None,
            requires_interrupt=False,
            agent_type=None,
            thread_id=None,
            next_node=None,
            doc_type=None,
            state_info=None,
            agent_selection_required=False
        )
        
        try:
            # 그래프 실행
            final_state = self.graph.invoke(initial_state)
            
            # 에러 처리
            if final_state.get("error"):
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": final_state["error"],
                    "requires_interrupt": False
                }
            
            # 인터럽트 처리
            if final_state.get("requires_interrupt"):
                result = final_state.get("result", {})
                logger.info(f"[RUN] Interrupt detected - final_state keys: {list(final_state.keys())}")
                logger.info(f"[RUN] final_state next_node: {final_state.get('next_node')}, doc_type: {final_state.get('doc_type')}")
                logger.info(f"[RUN] result next_node: {result.get('next_node') if result else 'None'}, doc_type: {result.get('doc_type') if result else 'None'}")
                
                return {
                    "success": False,
                    "interrupted": True,
                    "thread_id": final_state.get("thread_id"),
                    "session_id": session_id,
                    "agent_type": final_state.get("agent_type"),
                    "requires_interrupt": True,
                    "prompt": result.get("prompt") if result else None,
                    "next_node": final_state.get("next_node") or (result.get("next_node") if result else None),
                    "doc_type": final_state.get("doc_type") or (result.get("doc_type") if result else None),
                    "state_info": final_state.get("state_info") or (result.get("state_info") if result else {})
                }
            
            # 정상 결과
            result = final_state.get("result", {})
            
            # 디버그 로깅
            logger.info(f"[RUN] Final state result: {result}")
            logger.info(f"[RUN] Has help_message: {result.get('help_message') is not None}")
            
            # help_message가 있는 경우 특별 처리
            if result.get("help_message"):
                logger.info(f"[RUN] Returning help message response")
                return {
                    "success": True,
                    "session_id": session_id,
                    "response": result["help_message"],
                    "requires_interrupt": False
                }
            
            return {
                "success": True,
                "session_id": session_id,
                "agent_type": final_state.get("agent_type"),
                "result": result,
                "requires_interrupt": False
            }
            
        except Exception as e:
            logger.error(f"Router execution error: {e}")
            return {
                "success": False,
                "session_id": session_id,
                "error": str(e),
                "requires_interrupt": False
            }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """세션 상태 조회"""
        if session_id in self.sessions:
            session_info = self.sessions[session_id]
            return {
                "exists": True,
                "session_id": session_id,
                "agent": session_info.get("agent"),
                "thread_id": session_info.get("thread_id"),
                "status": "active" if session_info.get("active") else "inactive"
            }
        else:
            return {
                "exists": False,
                "session_id": session_id,
                "message": "세션을 찾을 수 없습니다."
            }
    
    def resume(self, session_id: str, user_reply: str, reply_type: str = "user_reply") -> Dict[str, Any]:
        """인터럽트된 작업 재개"""
        session_info = self.sessions.get(session_id)
        if not session_info:
            return {
                "success": False,
                "error": "세션을 찾을 수 없습니다."
            }
        
        try:
            if session_info["agent"] == "docs_agent":
                thread_id = session_info["thread_id"]
                agent = self.agents_config["docs_agent"]["instance"]
                
                # docs_agent는 이미 API 모드로 설정됨
                result = agent.resume(thread_id, user_reply, reply_type)
                
                # result가 None인 경우 처리
                if result is None:
                    return {
                        "success": False,
                        "error": "문서 생성이 중단되었습니다."
                    }
                
                # 완료 확인
                if result.get("success"):
                    session_info["active"] = False
                elif result.get("interrupted"):
                    # 계속 대화 필요
                    return {
                        "success": False,
                        "interrupted": True,
                        "thread_id": thread_id,
                        "session_id": session_id,
                        "prompt": result.get("prompt"),
                        "requires_interrupt": True,
                        "next_node": result.get("next_node"),
                        "doc_type": result.get("doc_type"),
                        "state_info": result.get("state_info", {})
                    }
                
                return result
            else:
                return {
                    "success": False,
                    "error": f"{session_info['agent']}는 인터럽트를 지원하지 않습니다."
                }
                
        except Exception as e:
            logger.error(f"Resume error: {e}")
            return {
                "success": False,
                "error": str(e)
            }