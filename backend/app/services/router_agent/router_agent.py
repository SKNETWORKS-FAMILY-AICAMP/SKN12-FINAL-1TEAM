"""
LangGraph 기반 라우터 에이전트 시스템

GPT-4o를 사용하여 사용자 질문을 4개의 전문 에이전트로 분류하고
LangGraph StateGraph를 통해 상태를 관리합니다.
"""

import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
import os
from dataclasses import dataclass, field

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RouterState:
    """라우터 상태 클래스"""
    query: str = ""
    selected_agent: Optional[str] = None
    routing_attempts: int = 0
    final_response: str = ""
    classification_result: str = ""
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """상태를 딕셔너리로 변환"""
        return {
            "query": self.query,
            "selected_agent": self.selected_agent,
            "routing_attempts": self.routing_attempts,
            "final_response": self.final_response,
            "classification_result": self.classification_result,
            "error_message": self.error_message
        }

class RouterAgent:
    """라우터 에이전트 클래스"""
    
    def __init__(self):
        """초기화"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.available_agents = [
            "employee_agent",
            "client_agent", 
            "db_agent",
            "docs_agent"
        ]
        self.max_retry_attempts = 3
        
        # 에이전트 설명
        self.agent_descriptions = {
            "employee_agent": "직원 실적 분석, 인사 정보, 조직도 관련 업무",
            "client_agent": "거래처 분석, 고객 데이터 분석, 매출 분석",
            "db_agent": "데이터베이스 검색, 문서 검색, 정보 조회",
            "docs_agent": "문서 자동생성, 규정 위반 여부 분석, 컴플라이언스 검토"
        }
        
        logger.info("✅ RouterAgent 초기화 완료")
        logger.info(f"   - 사용 가능한 에이전트: {self.available_agents}")
        logger.info(f"   - 최대 재시도 횟수: {self.max_retry_attempts}")
    
    def classify_query(self, query: str) -> str:
        """GPT-4o를 사용하여 쿼리 분류"""
        
        system_prompt = f"""
당신은 사용자의 질문을 분석하여 적절한 에이전트를 선택하는 전문가입니다.

다음 4개의 에이전트 중 하나를 선택해야 합니다:

1. employee_agent: {self.agent_descriptions['employee_agent']}
2. client_agent: {self.agent_descriptions['client_agent']}
3. db_agent: {self.agent_descriptions['db_agent']}
4. docs_agent: {self.agent_descriptions['docs_agent']}

사용자의 질문을 분석하고 가장 적절한 에이전트 하나만 선택하세요.
응답은 반드시 다음 형식으로만 답변하세요:

AGENT: [에이전트명]
REASON: [선택 이유]

예시:
AGENT: employee_agent
REASON: 직원 실적에 대한 질문이므로 직원 분석 에이전트가 적절합니다.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"🤖 GPT-4o 분류 결과: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ GPT-4o 분류 실패: {str(e)}")
            return f"ERROR: {str(e)}"
    
    def extract_agent_from_response(self, response: str) -> Optional[str]:
        """응답에서 에이전트명 추출"""
        try:
            lines = response.split('\n')
            for line in lines:
                if line.startswith('AGENT:'):
                    agent_name = line.replace('AGENT:', '').strip()
                    if agent_name in self.available_agents:
                        return agent_name
            return None
        except Exception as e:
            logger.error(f"❌ 에이전트명 추출 실패: {str(e)}")
            return None
    
    def route_query(self, state: RouterState) -> RouterState:
        """쿼리 라우팅 수행"""
        
        print(f"\n🔄 라우팅 시작 (시도 {state.routing_attempts + 1}/{self.max_retry_attempts})")
        print(f"📝 사용자 질문: {state.query}")
        
        # 분류 시도
        classification_result = self.classify_query(state.query)
        state.classification_result = classification_result
        state.routing_attempts += 1
        
        print(f"🤖 LLM 분류 결과:")
        print(f"   {classification_result}")
        
        # 에이전트 추출
        selected_agent = self.extract_agent_from_response(classification_result)
        
        if selected_agent:
            state.selected_agent = selected_agent
            print(f"✅ 분기된 에이전트: {selected_agent}")
            
            # 더미 에이전트 실행
            self.execute_dummy_agent(selected_agent)
            
            state.final_response = f"[{selected_agent}] 에이전트가 성공적으로 실행되었습니다."
            
        else:
            print(f"❌ 에이전트 선택 실패")
            state.error_message = f"에이전트 선택 실패: {classification_result}"
            
            # 재시도 로직
            if state.routing_attempts < self.max_retry_attempts:
                print(f"🔄 재시도 {state.routing_attempts}/{self.max_retry_attempts}")
                return self.route_query(state)
            else:
                print(f"⚠️ 최대 재시도 횟수 초과 - 수동 선택(H2H) 모드로 전환")
                return self.fallback_to_manual_selection(state)
        
        return state
    
    def fallback_to_manual_selection(self, state: RouterState) -> RouterState:
        """수동 선택 모드 (H2H)"""
        
        print(f"\n🔧 수동 선택 모드 (Human-to-Human)")
        print(f"📋 사용 가능한 에이전트:")
        
        for i, agent in enumerate(self.available_agents, 1):
            print(f"   {i}. {agent}: {self.agent_descriptions[agent]}")
        
        try:
            print(f"\n선택하세요 (1-{len(self.available_agents)}): ", end="")
            choice = input()
            
            if choice.isdigit() and 1 <= int(choice) <= len(self.available_agents):
                selected_agent = self.available_agents[int(choice) - 1]
                state.selected_agent = selected_agent
                
                print(f"✅ 수동 선택된 에이전트: {selected_agent}")
                
                # 더미 에이전트 실행
                self.execute_dummy_agent(selected_agent)
                
                state.final_response = f"[{selected_agent}] 에이전트가 수동 선택으로 실행되었습니다."
                
            else:
                print(f"❌ 잘못된 선택입니다. 기본 에이전트(db_agent)를 사용합니다.")
                state.selected_agent = "db_agent"
                self.execute_dummy_agent("db_agent")
                state.final_response = "[db_agent] 기본 에이전트가 실행되었습니다."
                
        except Exception as e:
            logger.error(f"❌ 수동 선택 실패: {str(e)}")
            state.selected_agent = "db_agent"
            self.execute_dummy_agent("db_agent")
            state.final_response = f"[db_agent] 오류로 인한 기본 에이전트 실행: {str(e)}"
        
        return state
    
    def execute_dummy_agent(self, agent_name: str):
        """더미 에이전트 실행"""
        print(f"🚀 [{agent_name}] 실행됨")
        
        # 각 에이전트별 더미 동작
        if agent_name == "employee_agent":
            print("   - 직원 데이터베이스 연결 중...")
            print("   - 실적 데이터 분석 중...")
            
        elif agent_name == "client_agent":
            print("   - 거래처 데이터 로드 중...")
            print("   - 고객 분석 리포트 생성 중...")
            
        elif agent_name == "db_agent":
            print("   - 벡터 데이터베이스 검색 중...")
            print("   - 관련 문서 검색 중...")
            
        elif agent_name == "docs_agent":
            print("   - 문서 생성 엔진 시작 중...")
            print("   - 컴플라이언스 규정 검토 중...")
        
        print(f"   ✅ [{agent_name}] 처리 완료")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """쿼리 처리 메인 메서드"""
        
        print(f"\n" + "="*60)
        print(f"🎯 NaruTalk AI 라우터 시스템 시작")
        print(f"="*60)
        
        # 상태 초기화
        state = RouterState(query=query)
        
        # Step 1: 사용자 질문 출력
        print(f"\n📋 Step 1. 사용자 질문 출력")
        print(f"   질문: {query}")
        
        # Step 2: LLM 분류 및 라우팅
        print(f"\n🤖 Step 2. LLM 분류 결과 출력")
        final_state = self.route_query(state)
        
        # Step 3: 분기된 에이전트 이름 출력
        print(f"\n🎯 Step 3. 분기된 에이전트 이름 출력")
        print(f"   최종 선택 에이전트: {final_state.selected_agent}")
        
        print(f"\n" + "="*60)
        print(f"🏁 라우팅 완료")
        print(f"="*60)
        
        return final_state.to_dict()

# 테스트용 메인 함수
if __name__ == "__main__":
    
    # 테스트 쿼리들
    test_queries = [
        "김철수 직원의 이번 달 실적을 분석해주세요",
        "ABC 거래처의 매출 현황을 알려주세요", 
        "회사 휴가 규정을 검색해주세요",
        "영업비밀보호서약서를 자동으로 생성해주세요"
    ]
    
    router = RouterAgent()
    
    for query in test_queries:
        result = router.process_query(query)
        print(f"\n📊 결과: {result}")
        print(f"\n" + "-"*60 + "\n") 