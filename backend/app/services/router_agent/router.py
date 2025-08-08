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
from ..client_agent import agent as client_agent_instance, run as client_agent_run
from ..search_agent import run as search_agent_run
import asyncio

# 분리된 모듈에서 import
from .graph import RouterState, create_graph
from ..tools.router_tools import create_tools_from_config

# 대화 저장 시스템 import
from ..common.conversation_storage import ConversationStorage

logger = logging.getLogger(__name__)


class RouterAgent:
    """세션 기반 Router Agent"""
    
    def __init__(self):
        # 대화 저장 시스템 초기화
        self.conversation_storage = ConversationStorage()
        
        # 에이전트 설정 (메타데이터 포함)
        self.agents_config = {
            "docs_agent": {
                "instance": CreateDocumentAgent(api_mode=True),  # API 모드로 초기화
                "metadata": {
                    "description": "문서를 새로 작성하고 생성하는 전문 에이전트입니다. 영업방문 결과보고서, 제품설명회 신청서, 제품설명회 결과보고서 등 회사 공식 문서의 초안을 작성하고 템플릿을 채워 완성된 문서를 만듭니다. 문서 생성 시 자동으로 사내 규정 위반 여부를 검토합니다. 주의: 이미 존재하는 문서를 찾거나 조회하는 것이 아니라, 새로운 문서를 '작성'하고 '생성'하는 작업을 담당합니다.",
                    "capabilities": [
                        "영업방문 결과보고서 초안 작성 및 템플릿 채우기",
                        "제품설명회 시행 신청서 새로 만들기",
                        "제품설명회 시행 결과보고서 문서 생성",
                        "각종 공식 문서의 초안 작성",
                        "문서 작성 시 자동 규정 검토",
                        "템플릿 기반 문서 자동 생성"
                    ],
                    "examples": [
                        "영업방문 보고서 작성해줘",
                        "제품설명회 신청서 만들어줘",
                        "문서 작성 도와줘",
                        "보고서 써줘",
                        "방문 결과 문서로 만들어줘",
                        "오늘 방문 내용 보고서로 정리해줘",
                        "신청서 초안 작성 부탁해",
                        "결과보고서 생성해줘",
                        "보고서 작성 필요해",
                        "문서 하나 만들어야 되는데",
                        "방문 보고서 부탁",
                        "설명회 신청서 급해",
                        "결과보고서 작성 가능?"
                    ]
                }
            },
            "employee_agent": {
                "instance": EnhancedEmployeeAgent(),
                "metadata": {
                    "description": "회사 내부 직원과 팀의 실적 데이터를 조회하고 분석하는 에이전트입니다. 개인별 영업 실적, 팀별 성과, 목표 달성률, 실적 트렌드를 분석합니다. 직원 이름(예: 최수아, 김철수)이나 팀명(예: 서부팀, 영업1팀)이 언급되면 해당 직원이나 팀의 성과 데이터를 제공합니다. 주의: 외부 고객이나 병원이 아닌, 우리 회사 직원의 정보만 다룹니다.",
                    "capabilities": [
                        "개인별 영업 실적 조회 및 상세 분석",
                        "팀별 성과 데이터 집계 및 비교",
                        "직원 인사 이력, 직책, 소속 부서 확인",
                        "월별/분기별 목표 달성률 계산",
                        "실적 트렌드 및 성장률 분석",
                        "개인 및 팀 간 성과 비교"
                    ],
                    "examples": [
                        "최수아 실적 분석해줘",
                        "서부팀 성과 보여줘",
                        "최수아 이번달 달성률이 얼마지?",
                        "김철수 성과 확인",
                        "이영희 달성률 보여줘",
                        "박민수 실적 조회",
                        "정대리 이번달 실적",
                        "영업1팀 실적 현황",
                        "동부지사 달성률",
                        "중부팀 목표 대비 실적",
                        "김과장 작년 실적 어때?",
                        "우리팀 실적 어때",
                        "영업직원들 성과 확인",
                        "직원 성과 평가"
                    ]
                }
            },
            "client_agent": {
                "instance": client_agent_instance,
                "metadata": {
                    "description": "외부 고객사, 병원, 의료기관 등 거래처의 매출과 실적을 분석하는 에이전트입니다. 병원명(예: 미라클신경과, 우리가족의원)이 언급되거나 거래처, 고객사 관련 매출 분석이 필요할 때 사용됩니다. 병원별 매출 추이, 거래처 간 비교, 고객 등급 분류 등을 수행합니다. 주의: 회사 직원이 아닌, 외부 거래처와 고객사 정보만 다룹니다.",
                    "capabilities": [
                        "병원 및 의료기관별 매출 실적 조회",
                        "거래처 월별/분기별 매출 추이 분석",
                        "병원 간 실적 비교 및 벤치마킹",
                        "고객 등급 분류 및 관리",
                        "병원 전체 매출 대비 우리 회사 점유율 분석",
                        "거래처별 성장률 및 잠재력 평가"
                    ],
                    "examples": [
                        "미라클신경과 실적분석해줘",
                        "미라클신경과와 우리가족의원 비교",
                        "최근 3개월 실적 트렌드 분석",
                        "우리가족의원 매출 현황",
                        "서울대병원 거래 내역",
                        "삼성병원 실적 조회",
                        "한양내과 정보 확인",
                        "거래처별 실적 비교",
                        "병원간 성과 분석",
                        "병원 실적 알려줘",
                        "거래처 정보 필요해",
                        "고객사 매출 현황",
                        "주요 병원 데이터",
                        "거래처 분석 자료"
                    ]
                }
            },
            "search_agent": {
                "instance": "search",  # 플래그로 사용
                "metadata": {
                    "description": "기존에 저장된 문서, 규정, 매뉴얼을 검색하고 찾는 에이전트입니다. 회사 규정, 정책 문서, 업무 매뉴얼, 제품 설명서, 교육 자료 등 이미 존재하는 자료를 데이터베이스에서 검색합니다. 주의: 새로운 문서를 작성하는 것이 아니라, 기존 자료를 '찾고' '검색'하는 작업만 수행합니다.",
                    "capabilities": [
                        "기존 문서 및 자료 검색",
                        "사내 규정 및 정책 문서 조회",
                        "업무 매뉴얼 및 가이드라인 검색",
                        "제품 정보 및 사양서 조회",
                        "교육 자료 및 학습 콘텐츠 검색",
                        "저장된 보고서 및 템플릿 찾기"
                    ],
                    "examples": [
                        "영업 규정 찾아줘",
                        "제품 설명서 검색",
                        "교육 자료 조회",
                        "회사 정책 검색",
                        "내부 규정 조회",
                        "업무 규칙 확인",
                        "매뉴얼 찾아줘",
                        "가이드라인 조회",
                        "사용 설명서 필요",
                        "업무 매뉴얼 확인",
                        "트레이닝 문서 찾기",
                        "자료 찾아줘",
                        "문서 검색해줘",
                        "정보 조회 필요",
                        "내부 자료 찾기"
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
                result = asyncio.run(client_agent_run(query, session_id or "default"))
                
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
        
        # 사용자 메시지를 PostgreSQL에 저장 (비동기를 동기로 실행)
        try:
            asyncio.run(self.conversation_storage.save_message(
                session_id=session_id,
                role="user",
                message=user_input
            ))
        except RuntimeWarning:
            pass  # RuntimeWarning 무시
        except Exception as e:
            logger.warning(f"사용자 메시지 저장 실패: {e}")
        
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
                response_text = result["help_message"]
                
                # AI 응답 저장
                try:
                    asyncio.run(self.conversation_storage.save_message(
                        session_id=session_id,
                        role="assistant",
                        message=response_text
                    ))
                except RuntimeWarning:
                    pass  # RuntimeWarning 무시
                except Exception as e:
                    logger.warning(f"AI 응답 저장 실패: {e}")
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "response": response_text,
                    "requires_interrupt": False
                }
            
            # AI 응답 저장 (일반 응답)
            response_text = result.get("response", "") if result else ""
            if response_text:
                try:
                    asyncio.run(self.conversation_storage.save_message(
                        session_id=session_id,
                        role="assistant",
                        message=response_text
                    ))
                except RuntimeWarning:
                    pass  # RuntimeWarning 무시
                except Exception as e:
                    logger.warning(f"AI 응답 저장 실패: {e}")
            
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