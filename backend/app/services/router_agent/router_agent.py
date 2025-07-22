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
