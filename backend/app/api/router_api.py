
import os
from fastapi import APIRouter
from pydantic import BaseModel
from ..services.router_agent.state_graph_router import StateGraphRouter
from ..services.router_agent.router_agent import RouterAgent
from dotenv import load_dotenv
import httpx
import asyncio
from typing import Dict, Any

# OPENAI_API_KEY 확인
api_key = os.getenv("OPENAI_API_KEY")
print("router_api.py - OPENAI_API_KEY:", api_key[:10] + "..." if api_key else "없음")

# FastAPI 라우터 구성
router = APIRouter()
state_graph_router = StateGraphRouter()
router_agent = RouterAgent()

# Base URL for internal API calls
BASE_URL = "http://localhost:8000"

class QueryRequest(BaseModel):
    query: str

class AgentSelectionRequest(BaseModel):
    query: str
    selected_agent: str

async def call_agent_api(agent_name: str, query: str) -> Dict[str, Any]:
    """선택된 에이전트의 실제 API를 호출하는 함수"""
    try:
        async with httpx.AsyncClient() as client:
            if agent_name == "employee_agent":
                # 직원 분석 API 호출
                response = await client.post(
                    f"{BASE_URL}/api/employee/analyze",
                    json={"query": query},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", True):
                        # employee API의 실제 응답 형식에 맞춤
                        employee_name = result.get("employee_name", "N/A")
                        period = result.get("period", "N/A")
                        analysis_result = result.get("result", "분석 결과가 없습니다.")
                        
                        formatted_response = f"""📊 직원 실적 분석 완료!

👤 분석 대상: {employee_name}
📅 분석 기간: {period}

📈 분석 결과:
{analysis_result}

✅ 직원 성과 분석이 완료되었습니다!"""

                        return {
                            "success": True,
                            "agent": agent_name,
                            "response": formatted_response,
                            "api_result": result,
                            "message": f"{employee_name} 직원의 실적 분석이 완료되었습니다."
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("result", "직원 분석 실패"),
                            "message": "직원 분석 중 오류가 발생했습니다."
                        }
                        
            elif agent_name == "client_agent":
                # 거래처 분석 API 호출
                response = await client.post(
                    f"{BASE_URL}/api/client/analyze", 
                    json={"query": query},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", True):
                        # client API의 실제 응답 형식에 맞춤
                        client_name = result.get("client_name", "N/A")
                        analysis_type = result.get("analysis_type", "N/A")
                        analysis_result = result.get("result", "분석 결과가 없습니다.")
                        
                        formatted_response = f"""🏥 고객 분석 완료!

🏢 분석 대상: {client_name}
📊 분석 유형: {analysis_type}

📈 분석 결과:
{analysis_result}

✅ 고객 분석이 완료되었습니다!"""

                        return {
                            "success": True,
                            "agent": agent_name,
                            "response": formatted_response,
                            "api_result": result,
                            "message": f"{client_name}의 분석이 완료되었습니다."
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("result", "고객 분석 실패"),
                            "message": "고객 분석 중 오류가 발생했습니다."
                        }
                        
            elif agent_name == "docs_agent":
                # 문서 분류 API 호출
                response = await client.post(
                    f"{BASE_URL}/api/docs/classify",
                    json={
                        "text": query,
                        "file_type": "auto"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", True):
                        # docs API의 실제 응답 형식에 맞춤
                        doc_result = result.get("result", {})
                        doc_type = doc_result.get("document_type", "문서")
                        confidence = doc_result.get("confidence", 0.0)
                        keywords = doc_result.get("keywords", [])
                        
                        formatted_response = f"""📄 문서 분류 완료!

📋 분류 결과:
• 문서 유형: {doc_type}
• 신뢰도: {confidence:.1%}
• 주요 키워드: {', '.join(keywords) if keywords else 'N/A'}

📝 분류 상세:
{result.get('message', '문서 분류가 완료되었습니다.')}

✅ 문서 분류 및 분석이 완료되었습니다!"""

                        return {
                            "success": True,
                            "agent": agent_name,
                            "response": formatted_response,
                            "api_result": result,
                            "message": f"문서가 '{doc_type}'로 분류되었습니다."
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("error", "문서 분류 실패"),
                            "message": "문서 분류 중 오류가 발생했습니다."
                        }
                        
            elif agent_name == "search_agent":
                # 검색 에이전트는 더미 응답 (실제 구현 필요)
                formatted_response = f"""🔍 내부 데이터 검색 완료!

🔎 검색 쿼리: "{query}"

📋 검색 결과:
• 관련 문서 5건 발견
• 내부 규정 3건 매칭
• 업무 매뉴얼 2건 관련

📄 주요 결과:
1. 윤리강령 관련 문서
2. 영업 가이드라인
3. 컴플라이언스 규정

✅ 내부 데이터 검색이 완료되었습니다!"""

                return {
                    "success": True,
                    "agent": agent_name,
                    "response": formatted_response,
                    "message": f"'{query}' 검색이 완료되었습니다."
                }
            else:
                return {
                    "success": False,
                    "error": f"알 수 없는 에이전트: {agent_name}",
                    "message": "지원하지 않는 에이전트입니다."
                }
             
            # 응답 상태 코드 확인
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API 호출 실패: HTTP {response.status_code}",
                    "message": f"{agent_name} API 호출이 실패했습니다."
                }
                 
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "API 호출 시간 초과",
            "message": f"{agent_name} API 호출이 시간 초과되었습니다."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"{agent_name} API 호출 중 오류가 발생했습니다."
        }

@router.post("/router")
async def route_with_state_graph(req: QueryRequest):
    """쿼리를 분석하고 적절한 에이전트로 라우팅"""
    try:
        result = state_graph_router.process_query(req.query)
        
        # 사용자 선택이 필요한 경우
        if result.get("selected_agent") == "NEED_USER_SELECTION":
            return {
                "success": True,
                "needs_user_selection": True,
                "message": "질문의 의도가 불분명합니다. 4개중에 1개를 선택해주세요",
                "query": result.get("query", ""),
                "routing_attempts": result.get("routing_attempts", 0),
                "classification_result": result.get("classification_result", ""),
                "available_agents": router_agent.available_agents,
                "agent_descriptions": router_agent.agent_descriptions,
                "agent_display_names": router_agent.get_agent_display_names()
            }
        
        # 에이전트가 선택된 경우 해당 API 호출
        selected_agent = result.get("selected_agent")
        if selected_agent and selected_agent in router_agent.available_agents:
            api_result = await call_agent_api(selected_agent, req.query)
            
            return {
                "success": api_result.get("success", True),
                "agent": selected_agent,
                "response": api_result.get("response", ""),
                "api_result": api_result.get("api_result"),
                "message": f"{selected_agent} 에이전트로 라우팅되어 처리되었습니다.",
                "query": result.get("query", ""),
                "routing_attempts": result.get("routing_attempts", 0),
                "classification_result": result.get("classification_result", ""),
                "error": api_result.get("error") if not api_result.get("success") else None
            }
        
        return {
            "success": True,
            "agent": result.get("selected_agent", "unknown"),
            "response": result.get("final_response", ""),
            "message": f"{result.get('selected_agent', 'unknown')} 에이전트로 라우팅되었습니다.",
            "query": result.get("query", ""),
            "routing_attempts": result.get("routing_attempts", 0),
            "classification_result": result.get("classification_result", "")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "라우팅 처리 중 오류가 발생했습니다."
        }

@router.get("/agents")
def get_available_agents():
    """사용 가능한 에이전트 목록 반환"""
    try:
        return {
            "success": True,
            "available_agents": router_agent.available_agents,
            "agent_descriptions": router_agent.agent_descriptions,
            "agent_display_names": router_agent.get_agent_display_names()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "에이전트 목록 조회 중 오류가 발생했습니다."
        }

@router.post("/select-agent")
async def process_agent_selection(req: AgentSelectionRequest):
    """사용자가 선택한 에이전트로 쿼리 처리"""
    try:
        # 선택된 에이전트의 실제 API 호출
        api_result = await call_agent_api(req.selected_agent, req.query)
        
        return {
            "success": api_result.get("success", True),
            "agent": req.selected_agent,
            "response": api_result.get("response", ""),
            "api_result": api_result.get("api_result"),
            "message": f"사용자 선택: {req.selected_agent} 에이전트로 처리되었습니다.",
            "query": req.query,
            "routing_attempts": 0,
            "classification_result": "USER_SELECTED",
            "error": api_result.get("error") if not api_result.get("success") else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "에이전트 선택 처리 중 오류가 발생했습니다."
        }
