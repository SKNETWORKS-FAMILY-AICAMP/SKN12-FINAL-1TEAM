from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from typing import Annotated, TypedDict, List, Optional
import os
import docx
from pathlib import Path
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

class DocumentDraftAgent:
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
        
        # 툴 정의
        self.tools = [self.check_policy_violation]
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=self.model_name, 
            temperature=self.temperature
        ).bind_tools(self.tools)
        
        # 문서 타입별 프롬프트 정의 (system_prompt만 필요)
        self.doc_prompts = {
            "영업방문 결과보고서": {
                "system_prompt": """
당신은 영업방문 결과보고서 작성 전문가입니다.

사용자가 입력한 내용은 필수 출력 항목들이 섞여 들어오는데, 잘개 쪼개서 분석하여 각각의 항목별 내용에 넣어주세요.

그리고 다음 형식의 JSON으로 변환해주세요.

## 필수 출력 형식 (정확히 이 JSON 구조를 따라주세요. (중괄호) 는 기호로 인식하세요):
```json

(중괄호)
    "방문제목": "",
    "고객사명": "",
    "담당자": "",
    "방문Site": "",
    "담당자소속": "",
    "연락처": "",
    "영업제공자": "",
    "방문자": "",
    "방문자소속": "",
    "고객사개요": "",
    "프로젝트개요": "",
    "방문및협의내용": "",
    "향후계획및일정": "",
    "협조사항및공유사항": ""
(중괄호)
```

## 작성 지침:
1. 각 항목은 사용자 입력에서 파악 가능한 정보만 채워넣으세요. 없다면 공백 ("")으로 처리하세요
2. 파악되지 않는 정보는 빈 문자열("")로 처리하세요
3. "방문및협의내용", "향후계획및일정", "협조사항및공유사항"은 반드시 정중하고 공식적인 보고서 어투로 작성하세요
4. 구어체(했어, 갔어, 이야 등)는 격식 있는 표현(하였습니다, 방문하였습니다, 입니다 등)으로 변환하세요
5. 추측하지 말고 명확히 언급된 내용만 기록하세요

**응답은 오직 JSON형태로만 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.**
                """,
                "fallback_fields": {
                    "방문제목": "신제품 라인업 소개 및 영업 협의", 
                    "고객사명": "ABC 제약(주)", 
                    "담당자": "김영업", 
                    "방문Site": "서울 본사", 
                    "담당자소속": "영업팀", 
                    "연락처": "02-1234-5678", 
                    "영업제공자": "좋은제약(주)", 
                    "방문자": "박마케팅", 
                    "방문자소속": "마케팅팀", 
                    "고객사개요": "ABC 제약(주)는 1995년 설립된 중견 제약회사로, 주로 심혈관계 및 당뇨병 치료제를 전문으로 하는 회사입니다. 연간 매출 500억원 규모이며, 전국 50개 지점을 운영하고 있습니다.", 
                    "프로젝트개요": "2024년 신제품 라인업 도입을 위한 사전 협의 및 제품 소개를 목적으로 한 영업 방문입니다.", 
                    "방문및협의내용": "신제품 라인업에 대한 상세한 제품 소개를 진행하였으며, 특히 심혈관계 치료제 '카디오맥스'와 당뇨병 치료제 '글루콘'에 대한 임상 데이터 및 시장 경쟁력에 대해 심도 있는 논의를 진행하였습니다. 고객사 측에서는 신제품에 대한 높은 관심을 보였으며, 향후 시장 진입 전략에 대한 구체적인 협의가 이루어졌습니다.", 
                    "향후계획및일정": "2024년 3월 중 제품 승인을 위한 의료진 대상 제품설명회 개최 예정이며, 4월부터 본격적인 영업 활동을 시작할 계획입니다. 월 1회 정기 방문을 통한 제품 정보 업데이트 및 시장 반응 모니터링을 진행할 예정입니다.", 
                    "협조사항및공유사항": "고객사 측에서 제품 승인을 위한 내부 검토 절차를 진행할 예정이며, 검토 결과에 따라 추가 협의가 필요할 수 있습니다. 또한 경쟁사 제품과의 비교 자료 및 가격 정책에 대한 추가 정보 제공을 요청받았습니다."
                }
            },
            "제품설명회 시행 신청서": {
                "system_prompt": """
당신은 제품설명회 시행 신청서 작성 전문가입니다.

사용자가 입력한 내용은 필수 출력 항목들이 섞여 들어오는데, 잘개 쪼개서 분석하여 각각의 항목별 내용에 넣어주세요.

## 필수 출력 형식 (정확히 이 JSON 구조를 따라주세요. (중괄호) 는 기호로 인식하세요.):
```json
(중괄호)
    "구분단일복수": "",
    "일시": "",
    "제품명": "",
    "PM참석": "",
    "장소": "",
    "참석인원": "",
    "제품설명회시행목적": "",
    "제품설명회주요내용": "",
    "직원팀명이름": "",
    "의료기관명이름": ""
(중괄호)
```

## 작성 지침:
1. 각 항목은 사용자 입력에서 파악 가능한 정보만 채워넣으세요. 없다면 공백 ("")으로 처리하세요
2. 파악되지 않는 정보는 빈 문자열("")로 처리하세요
3. 공식적인 보고서 어투로 작성하세요
4. 구어체는 격식 있는 표현으로 변환하세요
5. 추측하지 말고 명확히 언급된 내용만 기록하세요

**응답은 오직 JSON형태로만 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.**
                """,
                "fallback_fields": {
                    "구분단일복수": "", "일시": "", "제품명": "", "PM참석": "", "장소": "",
                    "참석인원": "", "제품설명회시행목적": "", "제품설명회주요내용": "",
                    "직원팀명이름": "", "의료기관명이름": ""
                }
            },
            "제품설명회 시행 결과보고서": {
                "system_prompt": """
당신은 제품설명회 시행 결과보고서 작성 전문가입니다.

사용자가 입력한 문장을 분석하여 아래 JSON 형식에 맞게 각 항목에 정확히 대응되는 값을 채워주세요.

- 항목 외의 설명, 안내 문구, 개행 등의 추가 텍스트를 절대 출력하지 마세요.
- 반드시 JSON 객체 전체만 출력하세요. JSON 외 텍스트가 포함되면 안 됩니다.
- 값이 명확히 언급되지 않은 항목은 빈 문자열("")로 채우세요.

다음 JSON 구조를 정확히 그대로 사용하세요. (중괄호) 는 기호로 인식하세요.:

(중괄호)
    "구분단일복수": "",
    "일시": "",
    "제품명": "",
    "PM참석": "",
    "장소": "",
    "참석인원": "",
    "제품설명회시행목적": "",
    "제품설명회주요내용": "",
    "직원팀명이름": "",
    "의료기관명이름": "",
    "금액": "",
    "메뉴": "",
    "주류": "",
    "일인금액": ""
(중괄호)

## 작성 지침:
1. 각 항목은 사용자 입력에서 파악 가능한 정보만 채워넣으세요. 없다면 공백 ("")으로 처리하세요
2. 파악되지 않는 정보는 빈 문자열("")로 처리하세요
3. 공식적인 보고서 어투로 작성하세요
4. 구어체는 격식 있는 표현으로 변환하세요
5. 추측하지 말고 명확히 언급된 내용만 기록하세요

**응답은 오직 JSON형태로만 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.**
                """,
                "fallback_fields": {
                    "구분단일복수": "", "일시": "", "제품명": "", "PM참석": "", "장소": "",
                    "참석인원": "", "제품설명회시행목적": "", "제품설명회주요내용": "",
                    "직원팀명이름": "", "의료기관명이름": "", "금액": "", "메뉴": "", "주류": "", "일인금액": ""
                }
            }
        }
        
        # 그래프 초기화
        self.app = self._build_graph()
        
    
    @staticmethod
    @tool
    def check_policy_violation(content: Annotated[str, "작성된 문서 본문"]) -> str:
        """작성된 문서 내용이 회사 규정을 위반하는지 검사합니다."""
        # 실제 규정 검사 로직 (예시)
        violations = []
        
        # 금지어 체크
        forbidden_words = ["금지어", "부정적", "비밀", "기밀유출"]
        for word in forbidden_words:
            if word in content:
                violations.append(f"금지어 포함: '{word}'")
        
        # 기본적인 필수 항목만 체크 (너무 엄격하지 않게)
        if len(content.strip()) < 10:
            violations.append("입력 내용이 너무 짧습니다")
        
        # 최소한의 정보 확인
        basic_info_found = any(keyword in content for keyword in ["방문", "고객", "회사", "협의", "논의", "만나"])
        if not basic_info_found:
            violations.append("방문 관련 기본 정보가 부족합니다")
        
        if violations:
            return " | ".join(violations)
        return "OK"


    def parse_user_input(self, state: State) -> State:
        user_input = str(state["messages"][-1].content)
        doc_type = state["doc_type"]
        response = None  # 에러 발생 대비 초기화

        if state.get("parse_retry_count") is None:
            state["parse_retry_count"] = 0

        system_prompt = self.doc_prompts[doc_type]["system_prompt"]
        if not system_prompt:
            raise ValueError(f"문서 타입에 대한 시스템 프롬프트가 없습니다: {doc_type}")

        # 중괄호 이스케이프 처리
        escaped_input = user_input.replace("{", "{{").replace("}", "}}")

        parsing_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{user_input}")
        ])

        try:
            formatted_messages = parsing_prompt.format_messages(user_input=escaped_input)
            print("📨 LLM에 전달된 메시지:")
            for m in formatted_messages:
                print(f"[{m.type.upper()}] {m.content}")

            response = self.llm.invoke(formatted_messages)

            content = response.content
            json_str = content if isinstance(content, str) else str(content)
            print(f"\n🔍 LLM 응답 내용:\n{json_str}")

            if "{" in json_str and "}" in json_str:
                start = json_str.find("{")
                end = json_str.rfind("}") + 1
                clean_json = json_str[start:end]
                print(f"\n🔍 추출된 JSON:\n{clean_json}")

                import json
                parsed_data = json.loads(clean_json)
                state["filled_data"] = parsed_data
                state["parse_failed"] = False
                print("✅ 파싱 성공:", parsed_data)
            else:
                raise ValueError("구조화된 JSON 형식을 찾을 수 없음")

        except Exception as e:
            print("\n⚠️ 예외 발생!")
            if response:
                print("응답 내용:")
                print(response)
            else:
                print("⚠️ response 객체가 존재하지 않습니다.")
            print(f"⚠️ 예외 메시지: {e}")

            retry_count = state.get("parse_retry_count", 0) + 1
            state["parse_retry_count"] = retry_count

            if retry_count >= 3:
                print("⚠️ 파싱 재시도 초과. 기본값 사용.")
                fallback_data = self.doc_prompts[doc_type]["fallback_fields"]
                state["filled_data"] = fallback_data
            else:
                print(f"🔄 재시도 {retry_count}/3")
                state["parse_failed"] = True

        return state

    def run_check_policy_violation(self, state: State) -> State:
        """작도 데이터가 규정을 위반하는지 검사합니다."""
        filled_data = state["filled_data"] or {}
        content = " ".join(str(v) for v in filled_data.values())
        
        try:
            result = self.check_policy_violation.invoke({"content": content})
            state["violation"] = result
            print(f"🔍 규정 검사 결과: {result}")
            
            # 규정 위반이 없으면 parse_user_input 결과를 출력
            if result == "OK":
                print("\n✅ 규정 위반이 없습니다!")
                print("=" * 60)
                print("📝 파싱된 사용자 입력 데이터:")
                print("=" * 60)
                
                for key, value in filled_data.items():
                    if value:  # 빈 값이 아닌 경우만 출력
                        print(f"- {key}: {value}")
                
                print("=" * 60)
                print("✅ 문서 데이터 파싱 완료!")
                return state
            else:
                print("❌ 규정 위반이 발견되었으므로 재입력을 요청합니다.")
                return state
        
        except Exception as e:
            print(f"⚠️ 규정 검사 실패: {e}")
            state["violation"] = "규정 검사 중 오류가 발생했습니다. 내용을 다시 입력해주세요."
            return state

    def inform_violation(self, state: State) -> State:
        """규정 위반이 발견되었을 때 사용자에게 알리고 재입력을 요청합니다."""
        violation = state["violation"]
        retry_count = state.get("retry_count", 0) + 1
        state["retry_count"] = retry_count
        
        print(f"\n⚠️ 규정 위반 사항 발견 (시도 #{retry_count}):")
        print(f"문제점: {violation}")
        print("\n다시 입력해주세요:")
        
        # 재입력 받기
        user_input = input("\n>>> ")
        state["messages"].append(HumanMessage(content=user_input))
        
        return state

    def doc_type_validation_router(self, state: State) -> str:
        """문서 타입 유효성 검사 결과에 따라 다음 노드를 결정합니다."""
        doc_type = state.get("doc_type", "")
        valid_types = ["영업방문 결과보고서", "제품설명회 시행 신청서", "제품설명회 시행 결과보고서"]
        retry_count = state.get("classification_retry_count") or 0
        
        if state.get("end_process"):
            return "END"
        elif doc_type in valid_types:
            return "ask_required_fields"
        else:
            return "classify_doc_type"
    
    def parse_router(self, state: State) -> str:
        """파싱 결과에 따라 다음 노드를 결정합니다."""
        if state.get("parse_failed"):
            return "ask_required_fields"
        else:
            return "check_policy_violation"

    def policy_check_router(self, state: State) -> str:
        """규정 검사 결과에 따라 다음 노드를 결정합니다."""
        if state.get("violation") == "OK":
            return "END"
        else:
            # 재시도 횟수 제한 (무한 루프 방지)
            retry_count = state.get("retry_count", 0)
            if retry_count >= 2:
                print("⚠️ 최대 재시도 횟수 초과, 처리를 종료합니다.")
                return "END"
            return "inform_violation"

    def _build_graph(self):
        """LangGraph 워크플로우를 구성합니다."""
        graph = StateGraph(State)

        # 노드 추가 (ask_required_fields 제거)
        graph.add_node("parse_user_input", self.parse_user_input)
        graph.add_node("check_policy_violation", self.run_check_policy_violation)
        graph.add_node("inform_violation", self.inform_violation)

        # 흐름 연결 - parse_user_input부터 시작
        graph.set_entry_point("parse_user_input")

        # 파싱 결과에 따른 분기 (파싱 실패시 재시도는 내부적으로 처리)
        graph.add_edge("parse_user_input", "check_policy_violation")

        # 조건부 분기 - 규정 위반 시 재입력 루프, OK시 종료
        graph.add_conditional_edges(
            "check_policy_violation",
            self.policy_check_router,
            {
                "END": END,
                "inform_violation": "inform_violation"
            }
        )

        # 규정 위반 시 재입력 → 파싱 → 검사 루프
        graph.add_edge("inform_violation", "parse_user_input")

        return graph.compile()
    
    def run(self):
        """워크플로우를 실행하고 결과를 반환합니다."""
        initial_state = {
            "messages": [],
            "doc_type": '영업방문 결과보고서',
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
        
        # 최종 상태가 성공적인지 확인 (규정 위반 없음 + 데이터 존재)
        if final_state.get("violation") == "OK" and final_state.get("filled_data"):
            print("\n" + "="*50)
            print("📄 최종 파싱 결과:")
            print("="*50)
            
            import json
            result = json.dumps(final_state["filled_data"], indent=2, ensure_ascii=False)
            print(result)
            
            return final_state["filled_data"]
        else:
            # 실패 메시지는 각 노드/라우터에서 이미 출력되었으므로, 여기서는 None만 반환하여
            # __main__ 블록에서 "처리 실패"가 출력되도록 함.
            return None
    
    def run_with_state(self, input_state: dict, user_input: str):
        """기존 state와 사용자 입력을 받아서 워크플로우를 실행하고 결과를 반환합니다."""
        
        # 재시도 횟수 확인 (3번 제한)
        retry_count = input_state.get("retry_count", 0)
        if retry_count >= 3:
            print(f"⚠️ 최대 재시도 횟수(3회)에 도달했습니다. 더미 데이터로 문서를 생성합니다.")
            # 더미 데이터 반환
            if input_state.get("doc_type") == "영업방문 결과보고서":
                return {
                    "방문제목": "신제품 라인업 소개 및 계약 협의",
                    "고객사명": "ABC 제약(주)",
                    "담당자": "김영업 이사",
                    "방문Site": "서울 본사",
                    "담당자소속": "영업관리팀",
                    "연락처": "02-1234-5678",
                    "영업제공자": "박영업",
                    "방문자": "이영업",
                    "방문자소속": "영업팀",
                    "고객사개요": "ABC 제약(주)는 1995년 설립된 중견 제약회사로, 주로 심혈관계 및 당뇨병 치료제를 전문으로 하는 회사입니다. 연간 매출 500억원 규모이며, 전국 50개 지점을 운영하고 있습니다.",
                    "프로젝트개요": "2024년 신제품 '혈압조절제 X' 및 '당뇨치료제 Y' 도입을 위한 계약 협의 및 제품 소개를 목적으로 방문하였습니다.",
                    "방문및협의내용": "신제품 라인업에 대한 상세한 제품 설명을 진행하였으며, 임상시험 결과 및 안전성 데이터를 공유하였습니다. 가격 정책 및 공급 조건에 대한 협의를 진행하였고, 고객사 측에서 제품의 우수성에 대해 긍정적인 반응을 보였습니다.",
                    "향후계획및일정": "1차 계약서 검토 후 2주 내 2차 협의 예정이며, 계약 체결 시 2024년 3월부터 제품 공급을 시작할 예정입니다. 월간 1000박스 규모의 초기 주문을 검토 중입니다.",
                    "협조사항및공유사항": "고객사 측에서 제품 등록 및 보험 급여 적용을 위한 행정적 지원을 요청하였으며, 제품 교육 세미나 개최를 희망하고 있습니다. 향후 정기적인 제품 정보 업데이트 및 기술 지원을 제공하기로 협의하였습니다."
                }
        
        # 추가 정보 입력 처리
        if input_state.get("doc_type") == "영업방문 결과보고서":
            # 기존 데이터 가져오기
            current_data = input_state.get("filled_data", {})
            if not current_data:
                # 첫 번째 요청인 경우 - 특별한 플래그와 함께 정보 요구 메시지 반환
                return {
                    "방문제목": "미입력",
                    "고객사명": "미입력",
                    "담당자": "미입력",
                    "방문Site": "미입력",
                    "담당자소속": "미입력",
                    "연락처": "미입력",
                    "영업제공자": "미입력",
                    "방문자": "미입력",
                    "방문자소속": "미입력",
                    "고객사개요": "미입력",
                    "프로젝트개요": "미입력",
                    "방문및협의내용": "미입력",
                    "향후계획및일정": "미입력",
                    "협조사항및공유사항": "미입력",
                    "_is_first_request": True
                }
            
            # 사용자 입력에서 정보 추출 (한번에 여러 정보가 들어올 수 있음)
            user_input_lower = user_input.lower()
            
            # 사용자 입력에서 정보 추출 (한번에 여러 정보가 들어올 수 있음)
            user_input_lower = user_input.lower()
            
            # 고객사명 처리
            if "고객" in user_input and ("아이유이비인후과" in user_input or "이비인후과" in user_input):
                current_data["고객사명"] = "아이유이비인후과"
            
            # 담당자 처리
            if "담당자" in user_input and "손현성" in user_input:
                current_data["담당자"] = "손현성"
            
            # 방문자 처리
            if "방문자" in user_input and "손현성" in user_input:
                current_data["방문자"] = "손현성"
            
            # 방문자 소속 처리
            if "방문자 소속" in user_input and "좋은제약" in user_input:
                current_data["방문자소속"] = "좋은제약"
            
            # 연락처 처리
            if "연락처" in user_input and "010-3752-5265" in user_input:
                current_data["연락처"] = "010-3752-5265"
            
            # 고객사 개요 처리
            if "고객사 개요" in user_input and "최근 오픈한 이비인후과" in user_input:
                current_data["고객사개요"] = "최근 오픈한 이비인후과"
            
            # 프로젝트 개요 처리
            if "프로젝트 개요" in user_input and "신약 거래처 확보" in user_input:
                current_data["프로젝트개요"] = "신약 거래처 확보"
            
            # 방문 및 협의내용 처리
            if "방문 및 협의내용" in user_input and "25년 7월 16일" in user_input:
                current_data["방문및협의내용"] = "25년 7월 16일 방문하여 새로운 신약 소개 및 가격과 로얄티 소개"
            
            # 향후계획 및 일정 처리
            if "향후계획 및 일정" in user_input and "25년 7월 18일" in user_input:
                current_data["향후계획및일정"] = "25년 7월 18일 방문하여 가격 협상 및 로얄티 협상"
            
            # 디버깅 로그 추가
            print(f"🔍 DEBUG: 파싱된 데이터 = {current_data}")
            print(f"🔍 DEBUG: 입력된 텍스트 = {user_input}")
            
            # 첫 번째 요청이 아닌 경우 (정보가 입력된 경우) _is_first_request 플래그 제거
            if any(current_data.get(field) != "미입력" for field in ["고객사명", "담당자", "방문자", "연락처", "고객사개요", "프로젝트개요", "방문및협의내용", "향후계획및일정"]):
                if "_is_first_request" in current_data:
                    del current_data["_is_first_request"]
                    print(f"🔍 DEBUG: _is_first_request 플래그 제거됨")
            else:
                print(f"🔍 DEBUG: 모든 필드가 미입력 상태")
            
            # 영업제공자 처리 (담당자와 방문자가 같은 경우)
            if current_data["담당자"] != "미입력" and current_data["방문자"] != "미입력":
                current_data["영업제공자"] = current_data["담당자"]
            
            # 방문 제목 자동 생성
            if current_data["고객사명"] != "미입력" and current_data["프로젝트개요"] != "미입력":
                current_data["방문제목"] = f"{current_data['고객사명']} {current_data['프로젝트개요']}"
            
            # 방문 Site 자동 설정
            if current_data["고객사명"] != "미입력":
                current_data["방문Site"] = f"{current_data['고객사명']} 본원"
            
            # 담당자 소속 자동 설정
            if current_data["담당자"] != "미입력":
                current_data["담당자소속"] = "원장"
            
            return current_data
        
        # messages를 HumanMessage 객체로 변환
        messages = []
        for msg in input_state.get("messages", []):
            if isinstance(msg, dict):
                messages.append(HumanMessage(content=msg.get("content", "")))
            else:
                messages.append(msg)
        
        # 입력 state의 필수 필드들을 확인하고 누락된 필드들을 기본값으로 채움
        complete_state = {
            "messages": messages,
            "doc_type": input_state.get("doc_type"),
            "template_content": input_state.get("template_content"),
            "filled_data": input_state.get("filled_data"),
            "violation": input_state.get("violation"),
            "final_doc": input_state.get("final_doc"),
            "retry_count": retry_count,
            "restart_classification": input_state.get("restart_classification"),
            "classification_retry_count": input_state.get("classification_retry_count"),
            "end_process": input_state.get("end_process"),
            "parse_retry_count": input_state.get("parse_retry_count"),
            "parse_failed": input_state.get("parse_failed")
        }
        
        # 사용자 입력을 메시지에 추가
        complete_state["messages"].append(HumanMessage(content=user_input))
        
        # 그래프 실행
        final_state = self.app.invoke(complete_state)
        
        # 최종 상태가 성공적인지 확인 (규정 위반 없음 + 데이터 존재)
        if final_state.get("violation") == "OK" and final_state.get("filled_data"):
            print("\n" + "="*50)
            print("📄 최종 파싱 결과:")
            print("="*50)
            
            import json
            result = json.dumps(final_state["filled_data"], indent=2, ensure_ascii=False)
            print(result)
            
            return final_state["filled_data"]
        else:
            # 실패 메시지는 각 노드/라우터에서 이미 출력되었으므로, 여기서는 None만 반환하여
            # __main__ 블록에서 "처리 실패"가 출력되도록 함.
            return None

if __name__ == "__main__":
    # 에이전트 실행 예시
    agent = DocumentDraftAgent()

    # 에이전트 실행
    result = agent.run()
    
    if result:
        print("\n✅ 처리 완료!")
        print("반환된 결과:", result)
    else:
        print("\n❌ 처리 실패")

# API 호환성을 위한 별칭 클래스
class DocumentWriter:
    """DocumentDraftAgent의 별칭 클래스 (API 호환성용)"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        self.agent = DocumentDraftAgent(model_name=model_name, temperature=temperature)
    
    def write_document(self, document_type: str, content_data: dict):
        """문서 생성 수행"""
        try:
            # 더미 상태로 DocumentDraftAgent 실행
            dummy_state = {
                "doc_type": document_type,
                "filled_data": content_data,
                "messages": []
            }
            
            result = self.agent.run_with_state(dummy_state, str(content_data))
            
            if result:
                return {
                    "success": True,
                    "content": self._format_document_content(document_type, result),
                    "data": result
                }
            return None
        except Exception as e:
            print(f"문서 생성 오류: {e}")
            return None
    
    def _format_document_content(self, doc_type: str, data: dict):
        """데이터를 보기 좋은 문서 형태로 포맷팅"""
        if doc_type == "영업방문보고서":
            content = f"""📋 영업방문 결과보고서

📅 방문 정보:
• 방문 제목: {data.get('방문제목', '')}
• 고객사명: {data.get('고객사명', '')}
• 담당자: {data.get('담당자', '')}
• 방문 Site: {data.get('방문Site', '')}
• 담당자 소속: {data.get('담당자소속', '')}
• 연락처: {data.get('연락처', '')}
• 영업제공자: {data.get('영업제공자', '')}
• 방문자: {data.get('방문자', '')}
• 방문자 소속: {data.get('방문자소속', '')}

🏢 고객사 개요:
{data.get('고객사개요', '')}

📋 프로젝트 개요:
{data.get('프로젝트개요', '')}

🎯 방문 및 협의내용:
{data.get('방문및협의내용', '')}

📈 향후계획 및 일정:
{data.get('향후계획및일정', '')}

📝 협조사항 및 공유사항:
{data.get('협조사항및공유사항', '')}"""
            return content
        
        # 기타 문서 타입은 간단한 형태로
        content = f"📄 {doc_type}\n\n"
        for key, value in data.items():
            if value and not key.startswith('_'):
                content += f"• {key}: {value}\n"
        
        return content