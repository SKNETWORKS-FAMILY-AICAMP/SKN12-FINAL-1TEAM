from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from typing import TypedDict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class State(TypedDict):
    messages: List[HumanMessage]
    doc_type: Optional[str]
    template_content: Optional[str]
    filled_data: Optional[dict]
    violation: Optional[str]
    final_doc: Optional[str]
    retry_count: int
    restart_classification: Optional[bool]
    classification_retry_count: Optional[int]
    end_process: Optional[bool]
    parse_retry_count: Optional[int]
    parse_failed: Optional[bool]

class DocumentClassifyAgent:
    """지능형 문서 초안 작성 시스템"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        """
        DocumentDraftAgent 초기화
        
        Args:
            model_name: 사용할 OpenAI 모델명
            temperature: LLM 온도 설정
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=self.model_name, 
            temperature=self.temperature
        )
        
        # 문서 타입별 템플릿 정의
        self.doc_prompts = {
            "영업방문 결과보고서": {
                "input_prompt": """
영업방문 결과보고서 작성을 위해 다음 정보를 입력해주세요:

【기본 정보】
- 방문 제목: 
- Client(고객사명): 
- 담당자: 
- 방문 Site: 
- 담당자 소속: 
- 연락처: 
- 영업제공자: 
- 방문자: 
- 방문자 소속: 

【내용】
- 고객사 개요 (신규 고객사인 경우): 
- 프로젝트 개요 (새 프로젝트인 경우): 
- 방문 및 협의내용: 
- 향후계획 및 일정: 
- 협조사항 및 공유사항: 

위 항목들을 자유롭게 작성해주세요.
                """
            },
            "제품설명회 시행 신청서": {
                "input_prompt": """
다음 정보를 입력해주세요:

【제품설명회 세부 내역】
- 구분 단일/복수:
- 일시:
- 제품명:
- PM 참석:
- 장소:
- 참석인원:
- 제품설명회 시행목적:
- 제품설명회 주요내용:

【참석자현황】
<직원인 경우>
- 팀명/이름 :

<보건의료 전문가인 경우>
- 의료기관명/이름:

위 항목들을 자유롭게 작성해주세요.
                """
            },
            "제품설명회 시행 결과보고서": {
                "input_prompt": """
다음 정보를 입력해주세요:

【제품설명회 세부 내역】
- 구분 단일/복수:
- 일시:
- 제품명:
- PM 참석:
- 장소:
- 참석인원:
- 제품설명회 시행목적:
- 제품설명회 주요내용:

【참석자현황】
<직원인 경우>
- 팀명/이름 :

<보건의료 전문가인 경우>
- 의료기관명/이름:

【예산사용내역】
- 금액:
- 메뉴:
- 주류:
- 1인 금액:

위 항목들을 자유롭게 작성해주세요.
                """
            }
        }
        
        # 그래프 초기화
        self.app = self._build_graph()
    
    
    def classify_doc_type(self, state: State) -> State:
        """LLM을 사용해서 사용자 요청을 분석하고 문서 타입을 분류합니다."""
        # 재시도 카운터 초기화 (새로운 분류 시작시에만)
        if state.get("classification_retry_count") is None:
            state["classification_retry_count"] = 0
        
        user_message = state["messages"][-1].content
        
        classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """
사용자의 요청을 분석하여 다음 문서 타입 중 하나로 분류해주세요:
1. 영업방문 결과보고서 - 고객 방문, 영업 활동 관련
2. 제품설명회 시행 신청서 - 제품설명회 진행 계획, 신청 관련
3. 제품설명회 시행 결과보고서 - 제품설명회 완료 후 결과 보고 관련

반드시 위 3가지 중 하나의 정확한 문서 타입 이름만 응답해주세요.
앞에 숫자는 제거하고 문서명만 출력하세요.
            """),
            ("human", "{user_request}")
        ])
        
        try:
            response = self.llm.invoke(classification_prompt.format_messages(user_request=user_message))
            # response.content가 string인지 확인
            content = response.content
            if isinstance(content, str):
                doc_type = content.strip()
            else:
                doc_type = str(content).strip()
            
            # 유효한 문서 타입인지 확인
            valid_types = ["영업방문 결과보고서", "제품설명회 시행 신청서", "제품설명회 시행 결과보고서"]
            if doc_type not in valid_types:
                doc_type = response
                
            state["doc_type"] = doc_type
            print(f"📋 LLM 문서 타입 분류: {doc_type}")
            
        except Exception as e:
            print(f"⚠️ LLM 분류 실패, 기본값 사용: {e}")
            state["doc_type"] = response
        
        return state

    def validate_doc_type(self, state: State) -> State:
        """분류된 문서 타입이 유효한지 확인하고 템플릿을 추가합니다."""
        doc_type = state.get("doc_type", "")
        valid_types = ["영업방문 결과보고서", "제품설명회 시행 신청서", "제품설명회 시행 결과보고서"]
        
        if doc_type in valid_types:
            print(f"✅ 유효한 문서 타입: {doc_type}")
            
            # 분류된 문서 타입에 맞는 템플릿을 state에 추가
            if doc_type in self.doc_prompts:
                state["template_content"] = self.doc_prompts[doc_type]["input_prompt"]
                print(f"📝 템플릿 추가 완료: {doc_type}")
            
            state["classification_retry_count"] = 0
            return state
        else:
            retry_count = (state.get("classification_retry_count") or 0) + 1
            state["classification_retry_count"] = retry_count
            
            print(f"❌ 유효하지 않은 문서 타입: '{doc_type}'")
            print(f"🔄 재분류 시도 {retry_count}/3")
            
            if retry_count >= 3:
                print("⚠️ 최대 재시도 횟수 초과. 처리를 종료합니다.")
                state["end_process"] = True
            else:
                # 최근 메시지를 다시 사용하거나 간단한 fallback 메시지를 추가 (옵션)
                state["messages"].append(state["messages"][-1])
            
            return state



    def doc_type_validation_router(self, state: State) -> str:
        """문서 타입 유효성 검사 결과에 따라 다음 노드를 결정합니다."""
        doc_type = state.get("doc_type", "")
        valid_types = ["영업방문 결과보고서", "제품설명회 시행 신청서", "제품설명회 시행 결과보고서"]
        retry_count = state.get("classification_retry_count") or 0
        
        if state.get("end_process") or retry_count >= 3:
            return "END"
        elif doc_type in valid_types:
            return "END"  # 유효한 분류 완료시 종료
        else:
            return "classify_doc_type"  # 재분류 필요


    def _build_graph(self):
        """LangGraph 워크플로우를 구성합니다."""
        graph = StateGraph(State)

        # 노드 추가
        graph.add_node("classify_doc_type", self.classify_doc_type)
        graph.add_node("validate_doc_type", self.validate_doc_type)

        # 흐름 연결
        graph.set_entry_point("classify_doc_type")
        
        # 문서 타입 분류 → 유효성 검사
        graph.add_edge("classify_doc_type", "validate_doc_type")
        
        # 유효성 검사 결과에 따른 분기
        graph.add_conditional_edges(
            "validate_doc_type",
            self.doc_type_validation_router,
            {
                "classify_doc_type": "classify_doc_type",      # 재분류 필요
                "END": END                                     # 최대 재시도 횟수 초과시 종료
            }
        )

        return graph.compile()
    
    def run(self, user_input: str):
        """워크플로우를 실행하고 결과를 반환합니다."""
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "doc_type": None,
            "template_content": None,
            "filled_data": None,
            "violation": None,
            "final_doc": None,
            "retry_count": 0,
            "restart_classification": None,
            "classification_retry_count": None
        }
        
        # 그래프 실행
        final_state = self.app.invoke(initial_state)
        
        # 분류 결과 확인
        doc_type = final_state.get("doc_type")
        valid_types = ["영업방문 결과보고서", "제품설명회 시행 신청서", "제품설명회 시행 결과보고서"]
        
        if doc_type in valid_types:
            print(f"\n📋 문서 분류 완료: {doc_type}")
            return final_state  # State 객체 반환
        else:
            print(f"\n❌ 문서 분류 실패: {doc_type}")
            return None

if __name__ == "__main__":
    # 에이전트 실행 예시
    agent = DocumentClassifyAgent()
    
    print("🚀 문서 초안 작성 시스템을 시작합니다...")
    print("문서 작성 요청을 입력해주세요:")
    
    user_input = input("\n>>> ")
    
    # 에이전트 실행
    result = agent.run(user_input)
    
    if result:
        print("\n✅ 처리 완료!")
        print("반환된 결과:", result)
    else:
        print("\n❌ 처리 실패")