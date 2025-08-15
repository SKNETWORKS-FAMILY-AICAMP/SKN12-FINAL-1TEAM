from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import openai
import os
from langgraph.graph import StateGraph, END
from .db_manager import EmployeeDBManager
from .query_analyzer import EmployeeQueryAnalyzer
from ..tools.calculation_tools import PerformanceCalculationTools

# 중앙 설정 import
from app.core.config import config

# 상태 정의
class AnalysisState(TypedDict):
    query: str
    query_analysis: Optional[Dict[str, Any]]
    employee_name: Optional[str]
    start_period: Optional[str]
    end_period: Optional[str]
    analysis_type: Optional[str]
    performance_data: Optional[Dict[str, Any]]
    target_data: Optional[Dict[str, Any]]
    analysis_results: Optional[Dict[str, Any]]
    report: Optional[str]
    error: Optional[str]

class EnhancedEmployeeAgent:
    """직원 실적 분석 에이전트"""
    
    def __init__(self):
        self.db_manager = EmployeeDBManager()
        self.query_analyzer = EmployeeQueryAnalyzer()
        self.calc_tools = PerformanceCalculationTools()
        self.graph = self._create_graph()
    
    def _create_graph(self):
        """LangGraph StateGraph를 생성합니다."""
        workflow = StateGraph(AnalysisState)
        
        # 노드 추가
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("load_data", self._load_data_node)
        workflow.add_node("perform_analysis", self._perform_analysis_node)
        workflow.add_node("generate_report", self._generate_report_node)
        
        # 엣지 연결
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "load_data")
        workflow.add_edge("load_data", "perform_analysis")
        workflow.add_edge("perform_analysis", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    def _analyze_query_node(self, state: AnalysisState) -> AnalysisState:
        """사용자 쿼리를 분석하는 노드"""
        try:
            query = state["query"]
            
            # 쿼리 분석 수행
            query_analysis = self.query_analyzer.get_enhanced_analysis(query)
            
            # 쿼리 분석 결과 검증
            if not query_analysis:
                state["error"] = "쿼리 분석에 실패했습니다. 예시: '최수아의 2023년 1월부터 2023년 6월까지 실적 분석해줘'"
                return state
            
            # 필수 정보 확인
            employee_name = query_analysis.get("employee_name")
            start_period = query_analysis.get("start_period") 
            end_period = query_analysis.get("end_period")
            
            # 필수 정보가 없는 경우 오류 반환
            if not employee_name:
                state["error"] = "직원명을 찾을 수 없습니다. 예시: '최수아의 2023년 1월부터 2023년 6월까지 실적 분석해줘'"
                return state
            
            if not start_period or not end_period or start_period == "None" or end_period == "None":
                state["error"] = "분석 기간을 찾을 수 없습니다. 예시: '최수아의 2023년 1월부터 2023년 6월까지 실적 분석해줘'"
                return state
            
            state["query_analysis"] = query_analysis
            state["employee_name"] = employee_name
            state["start_period"] = start_period
            state["end_period"] = end_period
            state["analysis_type"] = query_analysis.get("analysis_type", "종합분석")
            
            print(f"[OK] 쿼리 분석 완료: 직원={employee_name}, 기간={start_period}~{end_period}")
            
        except Exception as e:
            state["error"] = f"쿼리 분석 중 오류가 발생했습니다: {str(e)}"
            print(f"[ERROR] 쿼리 분석 오류: {e}")
        
        return state
    
    def _load_data_node(self, state: AnalysisState) -> AnalysisState:
        """데이터를 로드하는 노드"""
        try:
            if state.get("error"):
                return state
            
            employee_name = state["employee_name"]
            start_period = state["start_period"]
            end_period = state["end_period"]
            
            # 실적 데이터 로드
            performance_summary = self.db_manager.get_performance_summary(
                employee_name, start_period, end_period
            )
            
            # 실적 데이터가 없는 경우 오류 반환
            if performance_summary["total_performance"] <= 0:
                available_employees = self.db_manager.get_available_employees()
                if available_employees:
                    state["error"] = f"'{employee_name}' 직원의 {start_period}~{end_period} 기간 실적 데이터가 없습니다. 사용 가능한 직원: {', '.join(available_employees)}"
                else:
                    state["error"] = f"'{employee_name}' 직원의 {start_period}~{end_period} 기간 실적 데이터가 없습니다."
                return state
            
            # 목표 대비 실적 데이터 로드
            target_vs_performance = self.db_manager.get_target_vs_performance(
                state["employee_name"], start_period, end_period
            )
            
            # 성장률 분석 데이터 로드
            growth_analysis = self.db_manager.analyze_performance_trend(
                state["employee_name"], start_period, end_period
            )
            
            state["performance_data"] = performance_summary
            state["target_data"] = target_vs_performance
            
            # 추가 분석 데이터를 analysis_results에 임시 저장
            state["analysis_results"] = {
                "growth_analysis": growth_analysis
            }
            
            print(f"[OK] 데이터 로드 완료: 실적 {performance_summary['total_performance']:,.0f}원")
            
        except Exception as e:
            state["error"] = f"데이터 로드 중 오류가 발생했습니다: {str(e)}"
            print(f"[ERROR] 데이터 로드 오류: {e}")
        
        return state
    
    def _perform_analysis_node(self, state: AnalysisState) -> AnalysisState:
        
        """실적 분석을 수행하는 노드"""
        try:
            if state.get("error"):
                return state
            
            performance_data = state["performance_data"]
            target_data = state["target_data"]
            analysis_type = state["analysis_type"]
            
            analysis_results = state["analysis_results"] or {}
            
            # 1. 기본 성과 분석
            total_performance = performance_data["total_performance"]
            monthly_data = performance_data["monthly_breakdown"]
            
            # 2. 계산 도구를 사용한 고급 분석
            if len(monthly_data) >= 2:
                monthly_amounts = [data["amount"] for data in monthly_data]
                
                # 강화된 성장률 분석 (안정성 정보 포함)
                enhanced_growth = self.calc_tools.calculate_growth_analysis(monthly_amounts)
                analysis_results["enhanced_growth_analysis"] = enhanced_growth
                
                # 계절성 분석 (4개월 이상일 때만)
                seasonal_analysis = self.calc_tools.calculate_seasonal_analysis(monthly_data)
                analysis_results["seasonal_analysis"] = seasonal_analysis
            
            # 5. 달성 분석
            achievement_analysis = {
                "total_performance": target_data["total_performance"],
                "total_target": target_data["total_target"],
                "achievement_rate": target_data["achievement_rate"],
                "evaluation": target_data["evaluation"],
                "grade": target_data.get("grade", "N/A"),  # recommendation → grade로 변경
                "gap_amount": target_data["gap_amount"]
            }
            analysis_results["achievement_analysis"] = achievement_analysis
            
            # 6. 종합 평가
            comprehensive_evaluation = self._generate_comprehensive_evaluation(
                analysis_results, performance_data, target_data
            )
            analysis_results["comprehensive_evaluation"] = comprehensive_evaluation
            
            state["analysis_results"] = analysis_results
            
            print("[OK] 실적 분석 완료")
            
        except Exception as e:
            state["error"] = f"분석 수행 오류: {str(e)}"
            print(f"[ERROR] 분석 수행 오류: {e}")
        
        return state
    
    def _generate_comprehensive_evaluation(self, analysis_results: Dict[str, Any], 
                                         performance_data: Dict[str, Any], 
                                         target_data: Dict[str, Any]) -> Dict[str, Any]:
        """종합 평가를 생성합니다."""
        
        # 성과 점수 계산 (100점 만점)
        score_components = {}
        
        # 1. 목표 달성률 점수 (40점)
        achievement_rate = target_data.get("achievement_rate", 0)
        if achievement_rate >= 120:
            achievement_score = 40
        elif achievement_rate >= 100:
            achievement_score = 35
        elif achievement_rate >= 80:
            achievement_score = 25
        elif achievement_rate >= 60:
            achievement_score = 15
        else:
            achievement_score = 5
        score_components["achievement"] = achievement_score
        
        # 2. 성장률 점수 (30점)
        enhanced_growth_data = analysis_results.get("enhanced_growth_analysis", {})
        growth_trend = enhanced_growth_data.get("growth_trend", "안정")
        if growth_trend in ["강한 성장", "성장"]:
            growth_score = 30
        elif growth_trend == "안정":
            growth_score = 20
        else:
            growth_score = 10
        score_components["growth"] = growth_score
        
        # 3. 안정성 점수 (20점) - 성장률 분석에서 가져옴
        stability = enhanced_growth_data.get("stability", "보통")
        stability_score_map = {
            "매우 안정": 20, "안정": 16, "보통": 12, 
            "불안정": 8, "매우 불안정": 4
        }
        stability_score = stability_score_map.get(stability, 10)
        score_components["stability"] = stability_score
        
        # 총점 계산 (달성률 40점 + 성장률 30점 + 안정성 20점 = 90점 만점)
        total_score = sum(score_components.values())
        
        # 등급 결정 (90점 만점 기준으로 조정)
        if total_score >= 80:
            grade = "S"
            grade_desc = "탁월"
        elif total_score >= 70:
            grade = "A"
            grade_desc = "우수"
        elif total_score >= 60:
            grade = "B"
            grade_desc = "양호"
        elif total_score >= 50:
            grade = "C"
            grade_desc = "보통"
        else:
            grade = "D"
            grade_desc = "개선 필요"
        
        # 개선 우선순위 결정
        improvement_priorities = []
        sorted_components = sorted(score_components.items(), key=lambda x: x[1])
        
        for component, score in sorted_components[:2]:  # 가장 낮은 2개 영역
            if component == "achievement" and score < 30:
                improvement_priorities.append("목표 달성률 개선")
            elif component == "growth" and score < 25:
                improvement_priorities.append("실적 성장률 개선")
            elif component == "stability" and score < 15:
                improvement_priorities.append("실적 안정성 확보")
        
        return {
            "total_score": int(total_score),  # numpy 타입 방지
            "grade": grade,
            "grade_description": grade_desc,
            "score_breakdown": {k: int(v) for k, v in score_components.items()},  # numpy 타입 방지
            "improvement_priorities": improvement_priorities,
            "strengths": self._identify_strengths(score_components),
            "weaknesses": self._identify_weaknesses(score_components)
        }
    
    def _identify_strengths(self, score_components: Dict[str, int]) -> List[str]:
        """강점을 식별합니다."""
        strengths = []
        if score_components.get("achievement", 0) >= 35:
            strengths.append("목표 달성률 우수")
        if score_components.get("growth", 0) >= 25:
            strengths.append("높은 성장률")
        if score_components.get("stability", 0) >= 16:
            strengths.append("실적 안정성 확보")
        
        return strengths if strengths else ["기본 실적 유지"]
    
    def _identify_weaknesses(self, score_components: Dict[str, int]) -> List[str]:
        """약점을 식별합니다."""
        weaknesses = []
        if score_components.get("achievement", 0) < 25:
            weaknesses.append("목표 달성률 부족")
        if score_components.get("growth", 0) < 20:
            weaknesses.append("낮은 성장률")
        if score_components.get("stability", 0) < 12:
            weaknesses.append("실적 변동성 과대")
        
        return weaknesses if weaknesses else ["특별한 약점 없음"]
    
    def _generate_report_node(self, state: AnalysisState) -> AnalysisState:
        """보고서를 생성하는 노드"""
        try:
            if state.get("error"):
                return state
            
            analysis_results = state["analysis_results"]
            performance_data = state["performance_data"]
            target_data = state["target_data"]
            query_analysis = state["query_analysis"]
            
            # LLM을 사용한 지능형 보고서 생성
            report = self._generate_intelligent_report(
                analysis_results, performance_data, target_data, query_analysis
            )
            
            state["report"] = report
            
            print("[OK] 보고서 생성 완료")
            
        except Exception as e:
            state["error"] = f"보고서 생성 오류: {str(e)}"
            print(f"[ERROR] 보고서 생성 오류: {e}")
        
        return state
    
    def _generate_intelligent_report(self, analysis_results: Dict[str, Any], 
                                   performance_data: Dict[str, Any], 
                                   target_data: Dict[str, Any],
                                   query_analysis: Dict[str, Any]) -> str:
        """LLM을 활용한 지능형 보고서 생성"""
        
        try:
            api_key = config.get_openai_api_key()
            if not api_key:
                return self._generate_basic_report(analysis_results, performance_data, target_data)
            
            # 데이터 요약 준비
            employee_name = query_analysis.get("employee_name", "직원")
            period = f"{query_analysis.get('start_period')}~{query_analysis.get('end_period')}"
            
            comprehensive_eval = analysis_results.get("comprehensive_evaluation", {})
            trend_analysis = analysis_results.get("detailed_trend", {})
            achievement_analysis = analysis_results.get("achievement_analysis", {})
            
            # LLM 프롬프트 생성
            prompt = f"""
다음 직원 실적 분석 데이터를 바탕으로 전문적이고 실행 가능한 인사이트가 담긴 보고서를 작성해주세요.

## 기본 정보
- 직원명: {employee_name}
- 분석 기간: {period}
- 총 실적: {performance_data.get('total_performance', 0):,.0f}원
- 목표 달성률: {achievement_analysis.get('achievement_rate', 0):.1f}%

## 종합 평가
- 총점: {comprehensive_eval.get('total_score', 0)}점/100점
- 등급: {comprehensive_eval.get('grade', 'N/A')} ({comprehensive_eval.get('grade_description', '')})
- 강점: {', '.join(comprehensive_eval.get('strengths', []))}
- 약점: {', '.join(comprehensive_eval.get('weaknesses', []))}

## 트렌드 분석
- 추세: {trend_analysis.get('trend', '정보 없음')}
- 예측 신뢰도: {trend_analysis.get('trend_strength', '정보 없음')}

## 개선 우선순위
{chr(10).join([f"- {priority}" for priority in comprehensive_eval.get('improvement_priorities', [])])}

다음 형식으로 작성해주세요:

[직원 실적 분석 보고서]

1. 실행 요약
[전체적인 성과를 3-4줄로 요약]

2. 주요 성과 분석
[구체적인 수치와 함께 성과 분석]

3. 트렌드 및 예측
[실적 추세와 향후 전망]

4. 강점과 개선점
[명확한 강점과 개선이 필요한 영역]

5. 실행 권고사항
[구체적이고 실행 가능한 3-5개 권고사항]

주의사항:
- 전문적이지만 이해하기 쉬운 언어 사용
- 구체적인 수치와 데이터 기반 분석
- 실행 가능한 개선 방안 제시
- 긍정적 톤 유지하되 개선점 명확히 지적
- 마크다운 형식 사용하지 말고 일반 텍스트로 작성
"""
            
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 인사 성과 분석가입니다. 데이터 기반의 정확하고 실행 가능한 인사이트를 제공합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM 보고서 생성 실패: {e}")
            return self._generate_basic_report(analysis_results, performance_data, target_data)
    
    def _generate_basic_report(self, analysis_results: Dict[str, Any], 
                             performance_data: Dict[str, Any], 
                             target_data: Dict[str, Any]) -> str:
        """기본 보고서 생성 (LLM 실패시 폴백)"""
        
        comprehensive_eval = analysis_results.get("comprehensive_evaluation", {})
        achievement_analysis = analysis_results.get("achievement_analysis", {})
        trend_analysis = analysis_results.get("detailed_trend", {})
        
        report = f"""[직원 실적 분석 보고서]

1. 실행 요약

분석 결과 총 {performance_data.get('total_performance', 0):,.0f}원의 실적을 달성하였으며, 
목표 달성률은 {achievement_analysis.get('achievement_rate', 0):.1f}%입니다. 
종합 평가 점수는 {comprehensive_eval.get('total_score', 0)}점으로 {comprehensive_eval.get('grade_description', '평가 불가')} 수준입니다.

2. 주요 성과 분석

월별 실적 추이를 분석한 결과 {trend_analysis.get('trend', '안정적인')} 패턴을 보이고 있습니다. 
{achievement_analysis.get('evaluation', '목표 달성 상황')}이며, 
{achievement_analysis.get('grade', 'N/A')} 등급을 받았습니다.

3. 트렌드 및 예측

실적 트렌드는 {trend_analysis.get('trend', '안정')} 상태이며, 
예측 신뢰도는 {trend_analysis.get('trend_strength', '보통')} 수준입니다.

4. 강점과 개선점

주요 강점: {', '.join(comprehensive_eval.get('strengths', ['기본 실적 유지']))}
개선 필요 영역: {', '.join(comprehensive_eval.get('weaknesses', ['특별한 약점 없음']))}

5. 실행 권고사항

{chr(10).join([f"• {priority}" for priority in comprehensive_eval.get('improvement_priorities', ['현재 수준 유지'])])}

보고서 작성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}
"""
        
        return report
    
    async def run(self, query: str, session_id: str, messages: List[Dict] = None) -> Dict[str, Any]:
        """router_api.py에서 호출하는 표준 인터페이스 (멀티턴 대화 지원)"""
        try:
            # 컨텍스트 유틸리티 임포트
            from ..common.context_utils import resolve_references
            
            # 참조 해결 (그 사람 → 실제 이름)
            enhanced_query = resolve_references(query, messages or [])
            
            # 로깅
            if enhanced_query != query:
                print(f"[CONTEXT] 쿼리 보완: '{query}' → '{enhanced_query}'")
            
            # EnhancedEmployeeAgent를 사용하여 쿼리 분석
            initial_state = {
                "query": enhanced_query,
                "query_analysis": None,
                "employee_name": None,
                "start_period": None,
                "end_period": None,
                "analysis_type": None,
                "performance_data": None,
                "target_data": None,
                "analysis_results": None,
                "report": None,
                "error": None
            }
            
            try:
                # LangGraph 워크플로우 실행
                result = self.graph.invoke(initial_state)
                
                if result.get("error"):
                    return {
                        "success": False,
                        "error": result["error"],
                        "message": "분석 처리 중 오류가 발생했습니다.",
                        "agent": "employee_agent",
                        "session_id": session_id
                    }
                
                # 성공적인 결과 반환
                analysis_result = {
                    "success": True,
                    "employee_name": result.get("employee_name"),
                    "period": f"{result.get('start_period')}~{result.get('end_period')}",
                    "total_performance": int(result.get("performance_data", {}).get("total_performance", 0)),
                    "achievement_rate": float(result.get("target_data", {}).get("achievement_rate", 0)),
                    "evaluation": result.get("analysis_results", {}).get("comprehensive_evaluation", {}).get("grade_description", "평가 불가"),
                    "report": result.get("report", "보고서 생성 실패"),
                    "analysis_details": result.get("analysis_results", {}),
                    "message": "실적 분석이 완료되었습니다."
                }
                
                return {
                    "success": True,
                    "response": analysis_result.get("report", "분석 결과를 생성할 수 없습니다."),
                    "report": analysis_result.get("report", ""),
                    "agent": "employee_agent",
                    "session_id": session_id,
                    "employee_name": analysis_result.get("employee_name"),
                    "period": analysis_result.get("period"),
                    "total_performance": analysis_result.get("total_performance"),
                    "achievement_rate": analysis_result.get("achievement_rate"),
                    "evaluation": analysis_result.get("evaluation"),
                    "analysis_details": analysis_result.get("analysis_details", {})
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "분석 실행 중 오류가 발생했습니다.",
                    "agent": "employee_agent",
                    "session_id": session_id
                }
            

                
        except Exception as e:
            # 예외 처리
            error_message = str(e)
            print(f"[ERROR] Employee Agent 실행 오류: {error_message}")
            
            return {
                "success": False,
                "response": f"직원 실적 분석 중 오류가 발생했습니다: {error_message}",
                "error": error_message,
                "agent": "employee_agent",
                "session_id": session_id
            } 
                  