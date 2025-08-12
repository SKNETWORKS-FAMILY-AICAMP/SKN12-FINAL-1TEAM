import pandas as pd
import json
import re
from typing import Dict, Any, Optional, TypedDict
from pathlib import Path
from openai import AsyncOpenAI
import os
import logging
from typing_extensions import Annotated
from langgraph.graph import StateGraph, START, END

# 스테이트정의

class ReportState(TypedDict):
    company_name: str
    start_month: Optional[int]
    end_month: Optional[int]
    grade: Optional[str]
    grade_report: Optional[str]
    final_report: Optional[str]
    grade_result: Optional[Dict[str, Any]]
    same_grade_report: Optional[str]     
    growth_report: Optional[str]         
    strategy_report: Optional[str]    

# 클래스 정의 
class ClientAgent:
    def __init__(self):
        self.data_path = Path(__file__).parent / "좋은제약_거래처정보.xlsx"
        self.df = None
        self._load_data()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        self.client = AsyncOpenAI(api_key=api_key)
        
        # 임계값 정의
        self.revenue_threshold = {"A":3000000, "B":2000000, "C":1000000, "D":500000, "E":100000}
        self.profit_threshold = {"A":10, "B":15, "C":20, "D":25, "E":30}  # reverse=True
        self.patience_threshold = {"A":2200, "B":1800, "C":1400, "D":1000, "E":500}
        self.interaction_threshold = {"A":60, "B":45, "C":30, "D":15, "E":0}

    
    async def run_full_pipeline(self, company_name: str,
                                start_month: Optional[int] = None,
                                end_month: Optional[int] = None):
        """
        파싱된 파라미터 기반으로 LangGraph 파이프라인 실행
        """
        initial_state: ReportState = {
            "company_name": company_name,
            "start_month": start_month,
            "end_month": end_month,
            "grade": None,
            "grade_report": None,
            "final_report": None,
            "grade_result": None,
            "same_grade_report": None,     
            "growth_report": None,         
            "strategy_report": None        
        }

        graph = build_full_graph(self)
        final_state = await graph.ainvoke(initial_state)

        return final_state


    def _load_data(self):
        try:
            self.df = pd.read_excel(self.data_path)
            self.df['월'] = pd.to_datetime(self.df['월'].astype(str), format='%Y%m', errors='coerce')
        # 월_int 컬럼 미리 생성
            self.df['월_int'] = self.df['월'].dt.strftime('%Y%m').astype(int)
            print(f"[OK] 데이터 로드 완료: {len(self.df)}건")
            print("[DEBUG] 컬럼 목록:", self.df.columns.tolist())
              
        except Exception as e:
            print(f"[ERROR] 데이터 로드 실패: {e}")
            self.df = pd.DataFrame()

        
    async def run_pipeline_from_query(self, query: str) -> Dict[str, Any]:
        """
        자연어 쿼리를 받아서 파라미터 추출 후 전체 LangGraph 파이프라인 실행
        """
        parsed = await self.parse_query_params(query)
        if not parsed["success"]:
            return {
                "error": "❌ 파라미터 추출 실패",
                "detail": parsed.get("error", "Unknown error")
            }

        result = await self.run_full_pipeline(
            company_name=parsed["company_name"],
            start_month=parsed["start_month"],
            end_month=parsed["end_month"]
        )

        return result
    

    async def parse_query_params(self, query: str) -> Dict:
        prompt = f"""
다음 쿼리에서 거래처명과 분석 기간을 추출해주세요.
쿼리: {query}

규칙:
1. 거래처명은 괄호 포함 전체를 추출 (예: '우리가족의원(강서구 가양동)')
2. 날짜는 YYYYMM 형식으로 변환
3. 오늘 날짜는 2024년 11월로 가정

JSON 형식으로만 응답:
{{
    "company_name": "거래처명",
    "start_month": "YYYYMM 또는 null",
    "end_month": "YYYYMM 또는 null"
}}
"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            json_text = response.choices[0].message.content
            json_text = re.sub(r"^```json\s*|\s*```$", "", json_text.strip())
            result = json.loads(json_text)
            
            # 퍼지 매칭 추가: 정확한 거래처명이 없으면 부분 일치 검색
            company_name = result["company_name"]
            if company_name and company_name not in self.df["거래처ID"].values:
                # 부분 일치 검색
                partial_matches = self.df[
                    self.df["거래처ID"].str.contains(company_name, na=False, case=False)
                ]
                if not partial_matches.empty:
                    # 첫 번째 매칭 결과 사용
                    matched_name = partial_matches["거래처ID"].iloc[0]
                    print(f"[INFO] 거래처명 자동 매칭: '{company_name}' → '{matched_name}'")
                    company_name = matched_name
                else:
                    print(f"[WARNING] '{company_name}'와 일치하는 거래처를 찾을 수 없습니다.")
            
            return {
                "success": True,
                "company_name": company_name,
                "start_month": int(result["start_month"]) if result["start_month"] else None,
                "end_month": int(result["end_month"]) if result["end_month"] else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        


    def _get_grade(self, value: float, threshold_dict: Dict[str, float], reverse: bool = False) -> str:
        grades = ["A", "B", "C", "D", "E"]
        if reverse:
            for grade in grades:
                if value <= threshold_dict[grade]: #self.profit_threshold = {"A":10, "B":15, "C":20, "D":25, "E":30}
                    return grade
            return "E"
        else:
            for grade in grades:
                if value >= threshold_dict[grade]:
                    return grade
            return "E"

    def map_grade_to_score(self, grade: str) -> int:
        mapping = {"A": 5, "B":4, "C":3, "D":2, "E":1}
        return mapping.get(grade.upper(), 0)

    def map_score_to_grade(self, score: int) -> str:
        mapping = {5:"A",4:"B",3:"C",2:"D",1:"E"}
        return mapping.get(score, "E")

    def calculate_company_grade(self, company_name: str, start_month: Optional[int] = None,
                                end_month: Optional[int] = None) -> Dict:
        df = self.df
        filtered_df = df[df["거래처ID"] == company_name].copy()
        if start_month and end_month:
            filtered_df = filtered_df[(filtered_df["월_int"] >= start_month) & (filtered_df["월_int"] <= end_month)]

        if filtered_df.empty:
            return {"error": "해당 기간의 데이터가 없습니다", "최종등급": "N/A"}

        avg_revenue = filtered_df["매출"].mean()
        total_revenue = filtered_df["매출"].sum()
        total_budget = filtered_df["사용 예산"].sum()
        profit_rate = (total_budget / total_revenue * 100) if total_revenue > 0 else 0
        avg_patience = filtered_df["총환자수"].mean()
        interaction_rate = (filtered_df["총환자수"].sum() * 30000 / total_revenue) * 100 if total_revenue > 0 else 0

        revenue_grade = self._get_grade(avg_revenue, self.revenue_threshold)
        profit_grade = self._get_grade(profit_rate, self.profit_threshold, reverse=True)
        patience_grade = self._get_grade(avg_patience, self.patience_threshold)
        interaction_grade = self._get_grade(interaction_rate, self.interaction_threshold)

        scores = {
            "매출액": self.map_grade_to_score(revenue_grade),
            "수익률": self.map_grade_to_score(profit_grade),
            "환자수": self.map_grade_to_score(patience_grade),
            "관계도": self.map_grade_to_score(interaction_grade)
        }

        average_score = sum(scores.values()) / len(scores)
        final_grade = self.map_score_to_grade(round(average_score))

        return {
            "거래처명": company_name,
            "매출등급": revenue_grade,
            "수익률등급": profit_grade,
            "환자수등급": patience_grade,
            "관계도등급": interaction_grade,
            "최종등급": final_grade
        }
    

    async def use_llm_analysis_report(self, prompt: str) -> str:  # LLM이용하는 LLM호출함수
        try:
          response = await self.client.chat.completions.create(
              model="gpt-4o",
              messages=[{"role": "user", "content": prompt}],
              temperature=0.3
          )
          return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"LLM 분석 생성 실패: {e}")
            raise


    async def generate_grade_analysis_report(self, company_name: str, grade_result: Dict,
                                             start_month: Optional[int] = None, end_month: Optional[int] = None) -> str:
        prompt = f"""
너는 제약사 영업 데이터 분석 전문가이며, 
주어진 거래처의 종합 등급과 세부 지표를 바탕으로 **왜 해당 거래처가 그 등급에 선정되었는지**를 설명하는 분석 보고서를 작성해야 한다.

### 분석 대상
- 거래처명: {company_name}
- 분석 기간: {start_month or '전체기간'} ~ {end_month or '전체기간'}

등급 결과 요약
{json.dumps(grade_result, ensure_ascii=False, indent=2)}

### 작성 지침
1. 먼저 등급 산출 배경을 설명하라 (어떤 지표가 강점이고 어떤 지표가 약점인지).
2. 주요 지표(매출, 수익률, 환자수, 관계도)를 각각 분석하라.
3. 해당 거래처가 이 등급에 속한 이유를 중심으로 구체적으로 기술하라.
"""
        try:
            result = await self.use_llm_analysis_report(prompt)
            return result
        except Exception as e:
            return f"AI 분석 생성 실패: {e}"

    def get_same_grade_companies(self, company_name: str,
                                 start_month: Optional[int] = None,
                                 end_month: Optional[int] = None) -> Dict[str, Any]:
        target_grade_data = self.calculate_company_grade(company_name, start_month, end_month)
        target_grade = target_grade_data.get("최종등급", "N/A")

        filtered_df = self.df.copy()
        if start_month and end_month:
            filtered_df = filtered_df[(filtered_df["월_int"] >= start_month) & (filtered_df["월_int"] <= end_month)]

        same_grade_companies = []
        for cid in filtered_df["거래처ID"].unique():
            if cid == company_name:
                continue
            grade_data = self.calculate_company_grade(cid, start_month, end_month)
            if grade_data.get("최종등급") == target_grade:
                subset = filtered_df[filtered_df["거래처ID"] == cid]
                # 안전한 데이터 접근
                if not subset.empty:
                    try:
                        진료과값 = str(subset["과"].iloc[0]) if "과" in subset.columns else "정보없음"
                    except (IndexError, KeyError):
                        진료과값 = "정보없음"
                    평균매출 = subset["매출"].mean() if "매출" in subset.columns else 0
                    평균예산 = subset["사용 예산"].mean() if "사용 예산" in subset.columns else 0
                else:
                    진료과값 = "정보없음"
                    평균매출 = 0
                    평균예산 = 0

                same_grade_companies.append({
                    "거래처ID": cid,
                    "과": 진료과값,
                    "매출": 평균매출,
                    "사용 예산": 평균예산
                })

        return {
            "target_grade": target_grade,
            "target_info": target_grade_data,
            "same_grade_companies": same_grade_companies
        }

    def split_companies_by_department(self, company_name: str, same_grade_result: Dict) -> Dict[str, Any]:
        subset = self.df[self.df["거래처ID"] == company_name]["과"]

        if not subset.empty:
            target_department = str(subset.iloc[0])  # 🔥 핵심 수정
        else:
            target_department = "정보없음"

        same_grade_df = pd.DataFrame(same_grade_result["same_grade_companies"])

    # 🔐 이제 비교가 안전하게 동작
        same_department_df = same_grade_df[same_grade_df["과"] == target_department]
        diff_department_df = same_grade_df[same_grade_df["과"] != target_department]

        return {
            "same_department": same_department_df,
            "diff_department": diff_department_df,
            "target_department": target_department
        }


    async def analyze_same_grade_departments(self, company_name: str,
                                             start_month: Optional[int] = None,
                                             end_month: Optional[int] = None) -> str:
        same_grade_result = self.get_same_grade_companies(company_name, start_month, end_month)
        split_result = self.split_companies_by_department(company_name, same_grade_result)

        target_df = self.df[self.df["거래처ID"] == company_name].copy()
        if start_month and end_month:
            target_df = target_df[(target_df["월_int"] >= start_month) & (target_df["월_int"] <= end_month)]

        target_avg_revenue = target_df["매출"].mean() or 0
        target_avg_budget = target_df["사용 예산"].mean() or 0

        same_dept_avg_revenue = split_result["same_department"]["매출"].mean() if not split_result["same_department"].empty else 0
        diff_dept_avg_budget = split_result["diff_department"]["사용 예산"].mean() if not split_result["diff_department"].empty else 0

        prompt = f"""
너는 제약사 영업 데이터 분석 전문가이다.
아래 데이터를 기반으로 **대상 병원의 매출과 사용 예산을 같은/다른 진료과 병원들과 비교 분석**하는 보고서를 작성하라.

### 대상 병원
- 이름: {company_name}
- 분석 기간: {start_month or '전체기간'} ~ {end_month or '전체기간'}
- 대상 병원 평균 매출: {target_avg_revenue:,.0f}원
- 대상 병원 평균 사용 예산: {target_avg_budget:,.0f}원
- 진료과: {split_result['target_department']}

### 비교 그룹
1. 같은 진료과 & 동일 등급 병원 평균 매출: {same_dept_avg_revenue:,.0f}원
2. 다른 진료과 & 동일 등급 병원 평균 사용 예산: {diff_dept_avg_budget:,.0f}원

### 작성 지침
- 먼저 대상 병원의 매출을 같은 진료과 병원 평균과 비교 분석하라.
- 그 다음 대상 병원의 사용 예산을 다른 진료과 병원 평균과 비교 분석하라.
- 분석 시 어떤 지표가 우위인지, 개선할 부분이 무엇인지 제안하라.
- 구체적인 수치 기반 비교를 포함하라.
"""

        try:
            analysis_report = await self.use_llm_analysis_report(prompt)
        except Exception as e:
            analysis_report = f"AI 분석 생성 실패: {e}"

        return analysis_report

    async def generate_growth_analysis_report(self, company_name: str,
                                             start_month: Optional[int] = None,
                                             end_month: Optional[int] = None) -> str:
        
        company_df = self.df[self.df["거래처ID"] == company_name].copy()

        if start_month and end_month:
            company_df = company_df[(company_df["월_int"] >= start_month) & (company_df["월_int"] <= end_month)]

        if company_df.empty:
            return f"{company_name}의 해당 기간 데이터가 없습니다."

        monthly_data = company_df.sort_values(by="월_int")[["월_int", "매출", "사용 예산", "월방문횟수"]]


        monthly_data_md = monthly_data.to_markdown(index=False) #LLM을 위해

        start_visits = monthly_data["월방문횟수"].iloc[0]
        end_visits = monthly_data["월방문횟수"].iloc[-1]
        avg_visits = monthly_data["월방문횟수"].mean()

        start_revenue = monthly_data["매출"].iloc[0]
        end_revenue = monthly_data["매출"].iloc[-1]
        revenue_growth = ((end_revenue - start_revenue) / start_revenue * 100) if start_revenue else "데이터 없음"

        start_budget = monthly_data["사용 예산"].iloc[0]
        end_budget = monthly_data["사용 예산"].iloc[-1]
        budget_growth = ((end_budget - start_budget) / start_budget * 100) if start_budget else "데이터 없음"

        prompt = f"""
너는 제약사 영업 데이터 분석 전문가이며,
아래 월별 데이터를 기반으로 **우리 제약사와 거래처 간 관계의 성장성**을 분석하는 보고서를 작성해야 한다.

### 대상 병원
- 이름: {company_name}
- 분석 기간: {start_month or '전체기간'} ~ {end_month or '전체기간'}

### 월별 데이터 (매출/예산)
{monthly_data_md}

### 참고 지표

- 매출 성장률: {revenue_growth:.2f}%
- 예산 성장률: {budget_growth:.2f}%

- 시작 월 방문 횟수: {start_visits}
- 기간 평균 방문 횟수: {avg_visits:.2f}
- 종료 월 방문 횟수: {end_visits}

### 작성 지침
1. 월별 매출 추이와 예산 추이를 함께 분석해, **협력 관계가 균형적으로 성장하고 있는지** 설명하라.
2. 매출만 증가하거나 예산만 증가하는 경우 **관계 불균형 가능성**을 지적하라.
3. 수요(병원 측)와 공급(우리 회사) 관점에서 상호작용 분석을 하라.
4. 방문 횟수 추이를 기반으로 영업 활동 강도 변화(증가/감소/안정)를 평가하라.
"""

        try:
            growth_report = await self.use_llm_analysis_report(prompt)
        except Exception as e:
            growth_report = f"AI 분석 생성 실패: {e}"

        return growth_report
    
    async def generate_sales_strategy_report(self, company_name: str) -> str:
        overall_avg_patients = self.df["총환자수"].mean() or 0
        overall_avg_visits = self.df["월방문횟수"].mean() or 0
        overall_avg_revenue = self.df["매출"].mean() or 0 

        company_df = self.df[self.df["거래처ID"] == company_name].copy()
        if company_df.empty:
            return f"{company_name}의 데이터가 존재하지 않습니다."

        company_avg_patients = company_df["총환자수"].mean() or 0
        company_avg_visits = company_df["월방문횟수"].mean() or 0
        company_avg_revenue = company_df["매출"].mean() or 0

        insights = []
        
        patients_ratio = (company_avg_patients - overall_avg_patients) / (overall_avg_patients or 1) * 100
        revenue_ratio = (company_avg_revenue - overall_avg_revenue) / (overall_avg_revenue or 1) * 100
        visits_ratio = (company_avg_visits - overall_avg_visits) / (overall_avg_visits or 1) * 100
        recent_revenue = company_df.sort_values("월")["매출"].tail(3).mean()
        recent_ratio = (recent_revenue - company_avg_revenue) / (company_avg_revenue or 1) * 100

        if patients_ratio > 15 and revenue_ratio < 0:
            insights.append("환자 수는 높지만 매출은 평균 이하로, 미개척 잠재 시장 가능성이 있습니다.")

        if patients_ratio > 15 and revenue_ratio > 15:
            insights.append("환자 수와 매출 모두 평균 이상으로 핵심 고객군에 속합니다.")

        if visits_ratio > 15 and revenue_ratio < 0:
            insights.append("방문 횟수는 많으나 매출이 낮아 방문 전략 재검토가 필요합니다.")
        
        if recent_ratio > 15:
            insights.append("최근 3개월 매출이 급상승, 성장세 유지 전략 필요.")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
        if recent_ratio < -15:
            insights.append("최근 3개월 매출이 급감, 원인 파악 및 리커버리 전략 필요.")
        
        if not insights:
            insights.append("모든 지표가 평균 범위 내에 있어 안정적이나, 추가 성장 기회 탐색 필요.")


        monthly_revenue_trend = company_df.sort_values("월")[["월", "매출"]].to_dict("records")

        prompt = f"""
너는 제약사 영업전략 컨설턴트                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 이며, 
아래 데이터를 기반으로 **해당 거래처의 영업전략 분석 보고서**를 작성하라.                  
                                                 
### 대상 거래처                                                                                                     
- 이름: {company_name}                                                                                 
- 분석 기간: 전체 기간
                                                                                        
### 전체 거래처 평균
- 환자수 평균: {overall_avg_patients:.1f}
- 방문 횟수 평균: {overall_avg_visits:.1f}
- 매출 평균: {overall_avg_revenue:.1f}

### 해당 거래처 평균
- 환자수 평균: {company_avg_patients:.1f}                     
- 방문 횟수 평균: {company_avg_visits:.1f}
- 매출 평균: {company_avg_revenue:.1f}                                                              

### 월별 매출 추이
{monthly_revenue_trend}

### 분석 포인트
- {', '.join(insights) if insights else '특이사항 없음'}

### 작성 지침
1. 제공된 insights 목록을 가장 핵심 분석 포인트로 삼아, 각각의 의미를 해석하고 영향 요인을 설명하라.
2. insights에서 드러난 문제점·기회 요인을 기반으로 원인과 배경을 구체적으로 추론하라.
3. insights에 따라 실행 가능한 영업 전략(방문 전략, 제품 포트폴리오, 예산 배분, 프로모션 등)을 제안하라.
4. 숫자 지표(환자수, 방문횟수, 매출)와 insights 해석을 연결해 논리적으로 서술하라.
5. 만약 insights가 '모든 지표가 평균 범위 내에 있어 안정적이나, 추가 성장 기회 탐색 필요.'일 경우,
    전반적으로 안정적인 고객으로 평가하고 관계 유지 및 성장 가능성 탐색 전략에 중점 두어 작성하라.
"""

        try:
            strategy_report = await self.use_llm_analysis_report(prompt)
        except Exception as e:
            strategy_report = f"AI 분석 생성 실패: {e}"

        return strategy_report
    

    
def build_full_graph(agent: ClientAgent):
    graph = StateGraph(ReportState)

    # --- 1단계: 등급 계산 ---
    async def calculate_grade_node(state: ReportState):
        company_name = state["company_name"]
        start_month = state["start_month"]
        end_month = state["end_month"]
        grade_result = agent.calculate_company_grade(company_name, start_month, end_month)
        state["grade_result"] = grade_result
        return state

    # --- 2단계: 등급 분석 리포트 ---
    async def grade_analysis_node(state: ReportState):
        company_name = state["company_name"]
        grade_result = state["grade_result"]
        start_month = state["start_month"]
        end_month = state["end_month"]
        report = await agent.generate_grade_analysis_report(
            company_name=company_name,
            grade_result=grade_result,
            start_month=start_month,
            end_month=end_month
        )
        state["grade_report"] = report
        return state

    async def same_grade_node(state: ReportState):
        company_name = state["company_name"]
        start_month = state["start_month"]
        end_month = state["end_month"]
        report = await agent.analyze_same_grade_departments(company_name, start_month, end_month)
        return {"same_grade_report": report}

    async def growth_node(state: ReportState):
        company_name = state["company_name"]
        start_month = state["start_month"]
        end_month = state["end_month"]
        report = await agent.generate_growth_analysis_report(company_name, start_month, end_month)
        return {"growth_report": report}

    async def strategy_node(state: ReportState):
        company_name = state["company_name"]
        report = await agent.generate_sales_strategy_report(company_name)
        return {"strategy_report": report}

    # --- 4단계: 병합 노드 ---
    async def merge_node(state: ReportState):
        prompt = f"""
너는 제약사 영업 데이터 컨설턴트이다.
아래 리포트를 종합하여 통합 보고서를 작성하라.

### 등급 분석
{state['grade_report']}

### 동일 등급 비교 분석
{state['same_grade_report']}

### 성장성 분석
{state['growth_report']}

### 영업 전략 제안
{state['strategy_report']}
"""
        report = await agent.use_llm_analysis_report(prompt)
        state["final_report"] = report
        return state

    # --- 그래프 노드 등록 ---
    graph.add_node("calculate_grade", calculate_grade_node)
    graph.add_node("grade_analysis", grade_analysis_node)
    graph.add_node("same_grade", same_grade_node)
    graph.add_node("growth", growth_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("merge", merge_node)

    # --- 노드 연결 ---
    graph.set_entry_point("calculate_grade")
    graph.add_edge("calculate_grade", "grade_analysis")
    graph.add_edge("grade_analysis", "same_grade")
    graph.add_edge("grade_analysis", "growth")
    graph.add_edge("grade_analysis", "strategy")
    graph.add_edge("same_grade", "merge")
    graph.add_edge("growth", "merge")
    graph.add_edge("strategy", "merge")
    graph.set_finish_point("merge")

    return graph.compile()



if __name__ == "__main__":
    import asyncio

    agent = ClientAgent()

    query = "우리가족의원(강서구 가양동)의 2024년 1월부터 3월까지 분석 보고서를 생성해줘"
    result = asyncio.run(agent.run_pipeline_from_query(query))
    
    print("\n[등급 산출 결과]")
    grade_result = result.get("grade_result")
    if grade_result:
        print(json.dumps(grade_result, ensure_ascii=False, indent=2))
    else:
        print("등급 정보 없음")

    print("\n[최종 통합 리포트]")
    print(result.get("final_report", "리포트 없음"))

###########################################################################################################################################################3
                                                                #도출 예시 결과

    #[등급 산출 결과]
#{
#  "거래처명": "우리가족의원(강서구 가양동)",
#  "매출등급": "A",
#  "수익률등급": "B",
#  "환자수등급": "B",
#  "관계도등급": "A",
#  "최종등급": "B"
#}

#[최종 통합 리포트]
# 우리가족의원(강서구 가양동) 통합 보고서

## 1. 종합 평가

#우리가족의원은 2024년 1분기 동안 다양한 지표에서 우수한 성과를 보였으나, 수익률과 환자수에서의 개선이 필요합니다. 매출과 관계도에서는 A등급을 받았지만, 수익률과 환자수에서는 B등급을 기록하며 최종적으로 종합 등급은 B로 산출되었습니다. 이는 매출과 관계도에서의 강점이 수익률과 환자수에서의 상대적인 약점을 완전히 상쇄하지 못했음을 의미합니다.

## 2. 주요 지표 분석

### 매출 및 예산 사용
#- **매출**: 우리가족의원의 평균 매출은 같은 진료과의 동일 등급 병원 평균 매출에 비해 약 22.24배 높습니다. 이는 병원이 지역 내에서 높은 경쟁력을 가지고 있음을 시 사합니다.
#- **예산 사용**: 평균 사용 예산은 다른 진료과의 동일 등급 병원 평균 사용 예산에 비해 약 8.16배 높습니다. 이는 병원이 예산을 보다 적극적으로 사용하고 있음을 보여 줍니다.

### 수익률 및 환자수
#- **수익률**: 매출 대비 비용 관리의 효율성을 나타내는 지표로, B등급을 기록했습니다. 비용 절감이나 운영 효율성 측면에서 개선이 필요합니다.
#- **환자수**: B등급을 받았으며, 이는 신규 환자 유치나 기존 환자의 재방문율이 평균 수준임을 의미합니다. 차별화된 전략을 통해 환자수를 증가시킬 필요가 있습니다.   

### 관계도
#- **관계도**: 병원과 제약사 간의 협력 및 상호 신뢰 수준을 나타내며, A등급을 기록했습니다. 이는 병원이 제약사와의 관계를 잘 유지하고 있음을 보여줍니다.

## 3. 성장성 및 관계 분석

### 매출 및 예산 추이
#- **매출 추이**: 2024년 1월에 12,407만원이었던 매출은 2024년 3월에 11,721.6만원으로 감소하였습니다.
#- **예산 추이**: 2024년 1월에 2,284.15만원이었던 사용 예산은 2024년 3월에 1,181.24만원으로 크게 감소하였습니다.

### 관계 불균형 가능성
#매출과 예산의 동반 감소는 협력 관계가 균형적으로 성장하고 있지 않음을 시사합니다. 예산 감소 폭이 매출 감소 폭보다 훨씬 크다는 점에서, 장기적으로는 예산 부족으로 인해 매출 성장이 제한될 수 있는 위험이 존재합니다.

## 4. 영업 전략 제안

### 방문 및 제품 전략
#- **정기적 방문 강화**: 병원과의 긴밀한 커뮤니케이션을 유지하고, 경쟁 병원의 전략을 분석하여 차별화된 제안을 마련합니다.
#- **계절별 맞춤형 제품 제안**: 계절적 수요에 맞춘 건강 관리 제품 및 서비스를 제안합니다.

### 예산 및 프로모션 전략
#- **프로모션 강화**: 매출 감소 시기에 맞춘 프로모션 예산을 집중 투입합니다.
#- **환자 로열티 프로그램**: 기존 환자의 재방문을 유도할 수 있는 로열티 프로그램을 개발합니다.

## 5. 결론

#우리가족의원은 매출과 예산 사용 면에서 비교 그룹에 비해 우수한 성과를 보이고 있습니다. 그러나, 최근 매출 급감과 예산 감소는 해결해야 할 주요 과제입니다. 계절적  요인과 경쟁 환경 변화를 고려한 맞춤형 전략을 통해 매출을 회복하고, 장기적으로는 서비스 다각화와 프로모션 강화를 통해 지속적인 성장을 도모해야 합니다.