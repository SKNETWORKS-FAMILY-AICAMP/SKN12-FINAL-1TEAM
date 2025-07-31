<<<<<<< HEAD
import os, logging, json
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AVAILABLE_AGENT_IDS: List[str] = [
    "employee_agent",
    "client_agent",
    "search_agent",
    "create_document_agent",
]

AGENT_DESCS = {
    "employee_agent": (
        "사내 직원에 대한 정보 제공을 담당합니다. "
        "예: 개인 실적 조회, 인사 이력, 직책, 소속 부서, 조직도 확인, "
        "성과 평가 등 직원 관련 질의 응답을 처리합니다."
    ),
    "client_agent": (
        "고객 및 거래처에 대한 정보를 제공합니다. 반드시 병원, 제약영업과 관련이 있는 질문에만 답변합니다."
        "예: 특정 고객의 매출 추이, 거래 이력, 등급 분류, 잠재 고객 분석, "
        "영업 성과 분석 등 외부 고객 관련 질문에 대응합니다."
    ),
    "search_agent": (
        "내부 데이터베이스에서 정보 검색을 수행합니다. "
        "예: 문서 검색, 사내 규정, 업무 매뉴얼, 제품 정보, 교육 자료 등 "
        "특정 정보를 정제된 DB 또는 벡터DB 기반으로 검색합니다."
    ),
    "create_document_agent": (
        "문서 자동 생성 및 규정 검토를 담당합니다. "
        "예: 보고서 초안 자동 생성, 전표/계획서 생성, 컴플라이언스 위반 여부 판단, "
        "서식 분석 및 문서 오류 검토 등의 기능을 수행합니다."
    )
}

class RouterAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt = self._build_prompt()

    def _build_prompt(self) -> str:
        prompt = """당신은 제약회사 영업 지원 시스템의 라우터입니다.
사용자의 질문을 분석하여 가장 적절한 에이전트를 선택해야 합니다.

중요: 사용자의 질문이 아래 4개 에이전트의 기능과 전혀 관련이 없거나, 
일반적인 인사말, 잡담, 또는 시스템과 무관한 질문인 경우 반드시 "none"을 반환하세요.

사용 가능한 에이전트와 역할:
"""
        for aid, desc in AGENT_DESCS.items():
            prompt += f"\n- {aid}: {desc}"
        
        prompt += "\n\n질문이 위 에이전트들의 역할과 관련이 있을 때만 해당 에이전트 ID를 선택하세요."
        prompt += "\n관련이 없거나 애매한 경우 'none'을 반환하세요."
        prompt += "\n대화 맥락을 고려하되, 억지로 분류하지 마세요."
        return prompt

    async def classify(self, query: str, conversation_history: List[Dict[str, Any]] = None) -> Optional[str]:
        """사용자 쿼리와 대화 이력을 바탕으로 적절한 에이전트 선택"""
        try:
            messages = [{"role": "system", "content": self.prompt}]
            
            # 대화 이력 추가 (최근 10개)
            if conversation_history:
                for msg in conversation_history[-10:]:
                    if msg.get("role") == "user":
                        messages.append({"role": "user", "content": msg["content"]})
                    elif msg.get("role") == "assistant":
                        agent = msg.get("agent", "unknown")
                        messages.append({"role": "assistant", "content": f"[{agent}] {msg['content']}"})
            
            # 현재 쿼리 추가
            messages.append({"role": "user", "content": query})
            
            resp = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.2,
                messages=messages,
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "route",
                        "description": "적절한 에이전트를 선택합니다",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "agent": {
                                    "type": "string",
                                    "enum": AVAILABLE_AGENT_IDS + ["none"],
                                    "description": "선택된 에이전트 ID 또는 'none' (관련 없는 경우)"
                                }
                            },
                            "required": ["agent"]
                        }
                    }
                }],
            )
            
            tool_call = resp.choices[0].message.tool_calls[0]
            arguments = tool_call.function.arguments
            
            # JSON [EMOJI] [EMOJI]
            if isinstance(arguments, str):
                parsed_args = json.loads(arguments)
            else:
                parsed_args = arguments
                
            agent_id = parsed_args["agent"]
            
            if agent_id == "none":
                logger.info(f"[RouterAgent] 관련 없는 질문으로 분류: {query}")
                return None
            elif agent_id in AVAILABLE_AGENT_IDS:
                logger.info(f"[OK] 라우팅 성공: {agent_id}")
                return agent_id
            else:
                logger.warning(f"[WARNING] 알 수 없는 agent ID: {agent_id}")
                return None
                
        except Exception as e:
            logger.warning(f"[ERROR] [EMOJI] [EMOJI]: {e}, fallback [EMOJI]")
            return None
=======
import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class RouterState:
    def __init__(self, query: str):
        self.query = query
        self.selected_agent: Optional[str] = None
        self.routing_attempts: int = 0
        self.final_response: str = ""
        self.classification_result: str = ""
        self.error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "selected_agent": self.selected_agent,
            "routing_attempts": self.routing_attempts,
            "final_response": self.final_response,
            "classification_result": self.classification_result,
            "error_message": self.error_message,
        }

class RouterAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.available_agents = [
            "employee_agent", "client_agent", "search_agent", "docs_agent"
        ]
        self.max_retry_attempts = 3

        self.agent_descriptions = {
            "employee_agent": (
                "사내 직원에 대한 정보 제공을 담당합니다. "
                "예: 개인 실적 조회, 인사 이력, 직책, 소속 부서, 조직도 확인, "
                "성과 평가 등 직원 관련 질의 응답을 처리합니다."
            ),
            "client_agent": (
                "고객 및 거래처에 대한 정보를 제공합니다. "
                "예: 특정 고객의 매출 추이, 거래 이력, 등급 분류, 잠재 고객 분석, "
                "영업 성과 분석 등 외부 고객 관련 질문에 대응합니다."
            ),
            "search_agent": (
                "내부 데이터베이스에서 정보 검색을 수행합니다. "
                "예: 문서 검색, 사내 규정, 업무 매뉴얼, 제품 정보, 교육 자료 등 "
                "특정 정보를 정제된 DB 또는 벡터DB 기반으로 검색합니다."
            ),
            "docs_agent": (
                "문서 자동 생성 및 규정 검토를 담당합니다. "
                "예: 보고서 초안 자동 생성, 전표/계획서 생성, 컴플라이언스 위반 여부 판단, "
                "서식 분석 및 문서 오류 검토 등의 기능을 수행합니다."
            )
        }
        
    def classify_query(self, query: str) -> str:
        system_prompt = f"""
            당신은 사용자의 질문을 분석하여 아래 4개의 에이전트 중 하나를 선택하거나, 분류할 수 없으면 'AGENT: none'으로 답하십시오.

            1. employee_agent: {self.agent_descriptions['employee_agent']}
            2. client_agent: {self.agent_descriptions['client_agent']}
            3. search_agent: {self.agent_descriptions['search_agent']}
            4. docs_agent: {self.agent_descriptions['docs_agent']}

            응답 형식:
            AGENT: [에이전트명]
            REASON: [선택 이유]
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.2,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"GPT-4o 분류 실패: {str(e)}")
            return f"ERROR: {str(e)}"

    def extract_agent_from_response(self, response: str) -> Optional[str]:
        try:
            lines = response.split('\n')
            for line in lines:
                if line.startswith('AGENT:'):
                    agent_name = line.replace('AGENT:', '').strip()
                    if agent_name in self.available_agents:
                        return agent_name
                    elif agent_name.lower() == "none":
                        return None
            return None
        except Exception as e:
            logger.error(f"❌ 에이전트명 추출 실패: {str(e)}")
            return None

    def execute_dummy_agent(self, agent_name: str):
        print(f"\n🚀 [에이전트 실행] {agent_name}")
        if agent_name == "employee_agent":
            print("- 직원 정보 분석 중...")
        elif agent_name == "client_agent":
            print("- 거래처 분석 중...")
        elif agent_name == "search_agent":
            print("- 데이터베이스 검색 중...")
        elif agent_name == "docs_agent":
            print("- 문서 자동 생성 중...")
        else:
            print("- 알 수 없는 에이전트.")

    def fallback_to_h2h(self, state: RouterState) -> RouterState:
        print("\n⚠️ 자동 분류 실패 - H2H 모드 진입")
        print("사용자가 직접 선택해야 합니다.")
        for i, agent in enumerate(self.available_agents, 1):
            print(f"{i}. {agent}: {self.agent_descriptions[agent]}")

        try:
            selected = int(input("선택 번호 입력: "))
            if 1 <= selected <= len(self.available_agents):
                agent = self.available_agents[selected - 1]
                state.selected_agent = agent
                self.execute_dummy_agent(agent)
                state.final_response = f"H2H 수동 선택: [{agent}] 에이전트 실행 완료"
            else:
                raise ValueError("범위를 벗어남")
        except Exception as e:
            state.selected_agent = "search_agent"
            self.execute_dummy_agent("search_agent")
            state.final_response = f"예외 발생: 기본 에이전트 실행 ({str(e)})"

        return state
>>>>>>> e68a39a974366e551e5e2b37a4e9c1b12d803ee4
