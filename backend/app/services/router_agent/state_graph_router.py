import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, TypedDict
from .router_agent import RouterAgent, RouterState
from langgraph.graph import StateGraph, END

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LangGraph용 상태 타입 정의
class GraphState(TypedDict):
    query: str
    selected_agent: str
    routing_attempts: int
    final_response: str
    classification_result: str
    error_message: str

router = RouterAgent()

def create_download_files():
    """다운로드 파일들을 생성하는 함수"""
    # 다운로드 디렉토리 생성 (절대 경로 사용)
    current_dir = Path(__file__).parent.parent.parent.parent  # backend 디렉토리
    download_dir = current_dir / "downloads"
    download_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. PDF 보고서 생성 (JSON 형태로 저장)
    pdf_data = {
        "title": "영업방문 결과보고서",
        "customer": "아이유이비인후과",
        "visit_date": "2025년 7월 16일",
        "representative": "손현성",
        "contact": "010-3752-5265",
        "company_overview": "최근 오픈한 이비인후과로 신규 진료소",
        "project_overview": "신약 거래처 확보를 위한 제품 소개 및 계약 협상",
        "visit_content": "25년 7월 16일 방문하여 새로운 신약 소개 및 가격과 로얄티 소개",
        "future_plans": "25년 7월 18일 방문하여 가격 협상 및 로얄티 협상",
        "expected_contract": "연간 5천만원 규모",
        "next_visit": "7월 18일 2차 방문: 가격 및 로얄티 협상"
    }
    
    pdf_file = download_dir / f"영업방문결과보고서_{timestamp}.json"
    with open(pdf_file, 'w', encoding='utf-8') as f:
        json.dump(pdf_data, f, ensure_ascii=False, indent=2)
    
    # 2. Excel 일정표 생성
    schedule_data = {
        "일정": [
            {"날짜": "2025-07-16", "시간": "14:00-16:00", "내용": "1차 방문 - 신약 소개", "담당자": "손현성"},
            {"날짜": "2025-07-18", "시간": "10:00-12:00", "내용": "2차 방문 - 가격 협상", "담당자": "손현성"},
            {"날짜": "2025-07-25", "시간": "15:00-17:00", "내용": "계약서 검토 및 서명", "담당자": "손현성"},
            {"날짜": "2025-08-01", "시간": "09:00", "내용": "제품 공급 시작", "담당자": "손현성"}
        ]
    }
    
    excel_file = download_dir / f"방문일정표_{timestamp}.json"
    with open(excel_file, 'w', encoding='utf-8') as f:
        json.dump(schedule_data, f, ensure_ascii=False, indent=2)
    
    # 3. Word 요약서 생성
    summary_data = {
        "협의내용_요약": {
            "고객사": "아이유이비인후과",
            "방문일": "2025년 7월 16일",
            "주요_협의사항": [
                "신약 제품 소개 및 임상 효과 설명",
                "가격 정책 및 로얄티 조건 제시",
                "의료진 교육 프로그램 제공 계획",
                "경쟁사 대비 우위점 강조"
            ],
            "고객_반응": "신약에 대한 높은 관심도 보임",
            "다음_단계": "7월 18일 가격 및 로얄티 협상 예정"
        }
    }
    
    word_file = download_dir / f"협의내용요약_{timestamp}.json"
    with open(word_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    return {
        "pdf": str(pdf_file),
        "excel": str(excel_file),
        "word": str(word_file)
    }



# 1. classify_with_llm 
def classify_with_llm(state: GraphState) -> GraphState:
    current_attempts = state.get('routing_attempts', 0)
    logger.info(f"📩 사용자 질문: {state['query']}")
    logger.info(f"🔄 현재 시도 횟수: {current_attempts}")
    
    # 3회 이상 시도한 경우 강제로 None 반환 (안전장치)
    if current_attempts >= 3:
        logger.warning("⚠️ 3회 이상 시도 - 강제로 None 반환")
        return {
            "query": state['query'],
            "selected_agent": None,
            "routing_attempts": current_attempts,
            "final_response": state.get('final_response', ''),
            "classification_result": "MAX_ATTEMPTS_REACHED",
            "error_message": "최대 시도 횟수 초과"
        }
    
    # 분류 수행
    classification = router.classify_query(state['query'])
    agent = router.extract_agent_from_response(classification)
    
    # 시도 횟수 증가
    new_attempts = current_attempts + 1
    
    logger.info(f"🤖 GPT-4o 분류 결과: {classification}")
    logger.info(f"🎯 추출된 에이전트: {agent}")
    logger.info(f"🔢 업데이트된 시도 횟수: {new_attempts}")
    
    # 결과 업데이트
    return {
        "query": state['query'],
        "selected_agent": agent,
        "routing_attempts": new_attempts,
        "final_response": state.get('final_response', ''),
        "classification_result": classification,
        "error_message": state.get('error_message', '')
    }

# 2. retry_classification
def retry_classification(state: GraphState) -> GraphState:
    logger.info(f"🔁 재분류 시도: {state['routing_attempts']}")
    return state

# 3. h2h_manual_selection
def h2h_manual_selection(state: GraphState) -> GraphState:
    logger.warning("🤖 자동 분류 실패 - H2H 모드로 전환")
    
    # RouterState 객체 생성
    state_obj = RouterState(state['query'])
    state_obj.routing_attempts = state['routing_attempts']
    
    # H2H 모드 실행
    result_state = router.fallback_to_h2h(state_obj)
    
    return {
        "query": state['query'],
        "selected_agent": result_state.selected_agent,
        "routing_attempts": state['routing_attempts'],
        "final_response": result_state.final_response,
        "classification_result": state['classification_result'],
        "error_message": state.get('error_message', '')
    }

# 4. route_to_agent
def route_to_agent(state: GraphState) -> GraphState:
    if not state['selected_agent']:
        error_msg = "에이전트가 선택되지 않았습니다."
        logger.error(error_msg)
        state['error_message'] = error_msg
    else:
        logger.info(f"🎯 선택된 에이전트: {state['selected_agent']}")
    
    return state

# 5. execute_selected_agent
def execute_selected_agent(state: GraphState) -> GraphState:
    if state['selected_agent']:
        # 실제 API 호출로 변경
        final_response = call_actual_agent_api(state['selected_agent'], state['query'])
    else:
        final_response = "❌ 실행 실패: 선택된 에이전트가 없습니다."
    
    return {
        "query": state['query'],
        "selected_agent": state['selected_agent'],
        "routing_attempts": state['routing_attempts'],
        "final_response": final_response,
        "classification_result": state['classification_result'],
        "error_message": state.get('error_message', '')
    }

# 실제 API 호출 함수 추가
def call_actual_agent_api(agent_name: str, query: str) -> str:
    try:
        import httpx
        client = httpx.Client(timeout=30.0)
        
        if agent_name == "employee_agent":
            # 직원 분석 API 호출
            response = client.post(
                "http://localhost:8000/api/employee/analyze",
                json={"query": query},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    analysis_result = data.get("analysis_result", "")
                    report = data.get("report", "")
                    
                    return f"""📊 직원 성과 분석 완료!

📈 분석 결과:
{report}

📄 다운로드 링크:
• 📎 [성과 분석 보고서 (PDF)](http://localhost:8000/api/download/performance_report.pdf)
• 📊 [데이터 시각화 (Excel)](http://localhost:8000/api/download/data_visualization.xlsx)
• 📋 [요약 보고서 (Word)](http://localhost:8000/api/download/summary_report.docx)

✅ 직원 성과 분석이 완료되었습니다!"""
                else:
                    return f"❌ 직원 분석 실패: {data.get('error', '알 수 없는 오류')}"
            else:
                return f"❌ 직원 분석 API 오류: {response.status_code}"
                
        elif agent_name == "client_agent":
            # 고객 분석 API 호출 - 더미 데이터로 요청
            response = client.post(
                "http://localhost:8000/api/client/analyze",
                json={
                    "name": "ABC 회사",
                    "sales": 50000000,
                    "visits": 3
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    analysis_data = data.get("data", {})
                    
                    # 통합 보고서가 있으면 사용, 없으면 기본 정보 조합
                    if "통합 보고서" in analysis_data:
                        analysis_result = analysis_data["통합 보고서"]
                    else:
                        analysis_result = f"""📊 {analysis_data.get('등급', '분석 완료')}

📈 **분석 결과:**
{analysis_data.get('등급 이유', '분석이 완료되었습니다.')}

📋 **영업 전략:**
{analysis_data.get('영업 전략 보고서', '영업 전략이 수립되었습니다.')}

📈 **성장 요약:**
{analysis_data.get('성장 요약 보고서', '성장 요약이 작성되었습니다.')}"""
                    
                    return f"""📊 고객 분석 완료!

{analysis_result}

📄 다운로드 링크:
• 📊 [거래처 분석 결과 (PDF)](http://localhost:8000/api/download/client_analysis.pdf)
• 📋 [상세 분석 보고서 (Excel)](http://localhost:8000/api/download/detailed_report.xlsx)
• 📈 [분석 차트 데이터 (Word)](http://localhost:8000/api/download/chart_data.docx)

✅ 고객 분석이 완료되었습니다!"""
                else:
                    return f"❌ 고객 분석 실패: {data.get('error', '알 수 없는 오류')}"
            else:
                return f"❌ 고객 분석 API 오류: {response.status_code}"
                
        elif agent_name == "search_agent":
            # 검색 에이전트 하드코딩 응답
            query_lower = query.lower()
            
            if any(keyword in query_lower for keyword in ["윤리", "윤리강령"]):
                return """📋 좋은제약 윤리강령

🎯 목적:
• 건전한 기업 문화 조성
• 사회적 책임 수행
• 지속가능한 발전

📝 주요 내용:
1. 기본 원칙:
   - 정직과 신뢰
   - 공정성과 투명성
   - 사회적 책임

2. 업무 수행:
   - 법규 준수
   - 품질 우선
   - 고객 중심

3. 인간관계:
   - 상호 존중
   - 공정한 대우
   - 차별 금지

4. 정보 관리:
   - 기밀 보호
   - 개인정보 보호
   - 정확한 기록

5. 이해관계자 관계:
   - 공정한 거래
   - 적절한 선물
   - 이해상충 방지

✅ 임직원 모두가 윤리강령을 준수하여 신뢰받는 조직을 만들어갑니다."""
                
            elif any(keyword in query_lower for keyword in ["행동", "행동강령"]):
                return """📋 좋은제약 행동강령

🎯 목적:
• 윤리적 행동 기준 제시
• 조직 문화 개선
• 신뢰도 향상

📝 주요 내용:
1. 업무 수행:
   - 정직한 업무 수행
   - 품질 우선 원칙
   - 고객 만족 추구

2. 인간관계:
   - 상호 존중
   - 공정한 대우
   - 차별 금지

3. 정보 관리:
   - 기밀 보호
   - 개인정보 보호
   - 정확한 기록

4. 이해관계자 관계:
   - 공정한 거래
   - 적절한 선물
   - 이해상충 방지

✅ 임직원 모두가 행동강령을 준수하여 신뢰받는 조직을 만들어갑니다."""
                
            elif any(keyword in query_lower for keyword in ["자율", "자율준수"]):
                return """📋 좋은제약 자율준수 관리규정

🎯 목적:
• 준법 경영 체계 구축
• 위험 요소 사전 방지
• 지속가능한 경영

📝 주요 내용:
1. 준법 관리 조직:
   - 준법감시인 선임
   - 준법 관리 부서 운영
   - 정기 보고 체계

2. 위험 관리:
   - 위험 요소 식별
   - 사전 예방 조치
   - 모니터링 체계

3. 교육 및 훈련:
   - 정기 교육 실시
   - 사례 중심 교육
   - 이해도 평가

4. 위반 사항 처리:
   - 신고 체계 운영
   - 공정한 조사
   - 적절한 제재

✅ 자율준수를 통한 건전한 기업 문화를 조성합니다."""
                
            elif any(keyword in query_lower for keyword in ["공시", "공시정보"]):
                return """📋 좋은제약 공시정보 관리규정

🎯 목적:
• 투명한 정보 공개
• 이해관계자 보호
• 기업 신뢰도 향상

📝 주요 내용:
1. 공시 대상 정보:
   - 재무 정보
   - 경영 현황
   - 주요 사건

2. 공시 절차:
   - 정보 수집 및 검토
   - 공시 결정
   - 정보 공개

3. 사후 관리:
   - 피드백 수집
   - 정보 업데이트
   - 정확성 검증

4. 내부 통제:
   - 공시 담당 조직
   - 정보 관리 체계
   - 교육 및 훈련

✅ 투명한 정보 공개는 기업 신뢰도의 기반입니다."""
                
            elif any(keyword in query_lower for keyword in ["복리", "복리후생"]):
                return """📋 좋은제약 복리후생 제도

🎯 목적:
• 임직원 복지 향상
• 업무 만족도 증대
• 조직 활력 증진

📝 주요 복리후생:
1. 건강 관리:
   - 정기 건강검진
   - 건강보험 지원
   - 운동 시설 이용

2. 생활 지원:
   - 주택 자금 지원
   - 자녀 교육비 지원
   - 통신비 지원

3. 문화 활동:
   - 동호회 활동 지원
   - 문화 행사 참여
   - 휴가 및 휴일

4. 경조사 지원:
   - 경조사 휴가
   - 경조사 지원금
   - 위로금 지원

5. 교육 및 개발:
   - 자기계발 지원
   - 외국어 교육
   - 자격증 취득 지원

✅ 임직원의 삶의 질 향상을 위한 다양한 복리후생을 제공합니다."""
                
            else:
                return """📋 내부 규정 검색 결과

🔍 검색된 규정:
• 📄 윤리강령
• 📄 행동강령  
• 📄 자율준수 관리규정
• 📄 공시정보 관리규정
• 📄 복리후생 제도

💡 구체적인 규정을 찾으시려면 "윤리강령", "행동강령", "자율준수", "공시정보", "복리후생" 등의 키워드로 검색해주세요."""
                
        elif agent_name == "docs_agent":
            # 기존 docs_api 사용
            response = client.post(
                "http://localhost:8000/api/docs/write",
                json={
                    "state": {
                        "doc_type": "영업방문 결과보고서",
                        "retry_count": 0
                    },
                    "user_input": query
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    filled_data = data.get("filled_data", {})
                    
                    # 영업방문 결과보고서인 경우 상세 내용 표시
                    if "영업방문" in query or "방문 결과" in query or "보고서" in query:
                        # 실제 다운로드 파일 생성
                        download_files = create_download_files()
                        
                        # 파일명만 추출 (경로 제거)
                        pdf_filename = Path(download_files['pdf']).name
                        excel_filename = Path(download_files['excel']).name
                        word_filename = Path(download_files['word']).name
                        
                        return f"""📄 영업방문 결과보고서

🏥 방문 정보
• 방문 제목: 아이유이비인후과 신약 도입 검토 방문
• 고객사명: 아이유이비인후과
• 방문 Site: 아이유이비인후과 본원
• 방문일: 2025년 7월 16일

👥 참석자 정보
• 담당자: 손현성 (이비인후과 전문의)
• 담당자 소속: 아이유이비인후과
• 연락처: 010-3752-5265
• 영업제공자: 손현성
• 방문자: 손현성
• 방문자 소속: 좋은제약

📋 상세 내용
• 고객사 개요: 최근 오픈한 이비인후과로 신규 진료소
• 프로젝트 개요: 신약 거래처 확보를 위한 제품 소개 및 계약 협상
• 방문 및 협의내용: 25년 7월 16일 방문하여 새로운 신약 소개 및 가격과 로얄티 소개
• 향후계획 및 일정: 25년 7월 18일 방문하여 가격 협상 및 로얄티 협상
• 협조사항 및 공유사항: 신약 도입 시 의료진 교육 프로그램 제공 예정

📊 방문 결과
• 고객 반응: 신약에 대한 높은 관심도 보임
• 협상 진행도: 1차 제품 소개 완료, 2차 가격 협상 예정
• 예상 계약 규모: 연간 5천만원 규모
• 리스크 요소: 경쟁사 제품과의 가격 경쟁

📈 다음 단계
• 7월 18일 2차 방문: 가격 및 로얄티 협상
• 7월 25일 계약서 검토 및 서명
• 8월 1일 제품 공급 시작

📄 다운로드 링크:
• 📎 [상세 보고서 다운로드](http://localhost:8000/api/download/{pdf_filename})
• 📊 [방문 일정표 다운로드](http://localhost:8000/api/download/{excel_filename})
• 📋 [협의 내용 요약 다운로드](http://localhost:8000/api/download/{word_filename})

✅ 영업방문 결과보고서가 완성되었습니다!"""
                    else:
                        return f"📄 문서 작성 완료: {data.get('message', '문서가 성공적으로 작성되었습니다.')}"
                else:
                    return f"❌ 문서 작성 실패: {data.get('error', '알 수 없는 오류')}"
            else:
                return f"❌ 문서 작성 API 오류: {response.status_code}"
                
        else:
            return f"❌ 알 수 없는 에이전트: {agent_name}"
                
    except Exception as e:
        logger.error(f"API 호출 오류: {str(e)}")
        return f"❌ {agent_name} API 호출 중 오류 발생: {str(e)}"

# ✅ 조건 분기 함수
def classify_condition(state: GraphState) -> str:
    selected_agent = state.get('selected_agent')
    routing_attempts = state.get('routing_attempts', 0)
    
    logger.info(f"🔍 조건 분기 확인: selected_agent={selected_agent}, routing_attempts={routing_attempts}")
    
    # 에이전트가 성공적으로 선택된 경우
    if selected_agent is not None and selected_agent != "none" and selected_agent in router.available_agents:
        logger.info("✅ 에이전트 선택됨 -> route_to_agent")
        return "has_agent"
    # 3회 미만 시도한 경우 재시도
    elif routing_attempts < 3:
        logger.info(f"🔁 재시도 {routing_attempts}/3 -> retry_classification")
        return "retry"
    # 3회 이상 실패한 경우 H2H 모드
    else:
        logger.info("🤖 3회 실패 -> h2h_manual_selection")
        return "h2h"

# ✅ LangGraph 전체 흐름
def build_router_graph():
    graph = StateGraph(GraphState)

    graph.add_node("classify_with_llm", classify_with_llm)
    graph.add_node("retry_classification", retry_classification)
    graph.add_node("h2h_manual_selection", h2h_manual_selection)
    graph.add_node("route_to_agent", route_to_agent)
    graph.add_node("execute_selected_agent", execute_selected_agent)

    graph.set_entry_point("classify_with_llm")

    # ✅ 분기를 하나의 조건 함수로 통합
    graph.add_conditional_edges(
        "classify_with_llm",
        classify_condition,
        {
            "has_agent": "route_to_agent",
            "retry": "retry_classification",
            "h2h": "h2h_manual_selection"
        }
    )

    graph.add_edge("retry_classification", "classify_with_llm")
    graph.add_edge("route_to_agent", "execute_selected_agent")
    graph.add_edge("h2h_manual_selection", "execute_selected_agent")
    graph.add_edge("execute_selected_agent", END)

    return graph.compile()

# ✅ 외부 호출용 클래스
class StateGraphRouter:
    def __init__(self):
        self.app = build_router_graph()

    def process_query(self, query: str) -> dict:
        # 초기 상태 생성
        initial_state: GraphState = {
            "query": query,
            "selected_agent": None,
            "routing_attempts": 0,
            "final_response": "",
            "classification_result": "",
            "error_message": ""
        }
        
        # 그래프 실행
        final_state = self.app.invoke(initial_state)
        return final_state

    def process_query_with_agent(self, query: str, selected_agent: str) -> dict:
        """사용자가 직접 선택한 에이전트로 쿼리 처리"""
        # 선택된 에이전트로 바로 실행
        initial_state: GraphState = {
            "query": query,
            "selected_agent": selected_agent,
            "routing_attempts": 3,  # H2H 모드였다는 것을 표시
            "final_response": "",
            "classification_result": "USER_SELECTED",
            "error_message": ""
        }
        
        # execute_selected_agent 노드로 직접 실행
        final_response = call_actual_agent_api(selected_agent, query)
        
        return {
            "query": query,
            "selected_agent": selected_agent,
            "routing_attempts": 3,
            "final_response": final_response,
            "classification_result": "USER_SELECTED",
            "error_message": ""
        }
