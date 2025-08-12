import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, TypedDict

import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI
from langgraph.graph import StateGraph

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ReportState(TypedDict):
    company_name: str
    start_month: Optional[int]
    end_month: Optional[int]
    # 결과물
    final_report: Optional[str]
    grade_result: Optional[Dict[str, Any]]
    grade_report: Optional[str]
    same_grade_report: Optional[str]
    growth_report: Optional[str]
    strategy_report: Optional[str]
    # 데이터
    target_df_markdown: Optional[str]      # LLM 프롬프트용
    target_df_summary: Optional[Dict[str, Any]]  # 요약 지표 캐시

# Agent
# -------------------------------
class ClientAgent:
    def __init__(self):
        self.data_path = Path(__file__).parent / "좋은제약_거래처정보.xlsx"
        self.df: pd.DataFrame = pd.DataFrame()
        self._load_data()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        self.client = AsyncOpenAI(api_key=api_key)

        # 임계값

        self.revenue_threshold = {"A": 3000000, "B": 2000000, "C": 1000000, "D": 500000, "E": 100000}
        self.profit_threshold  = {"A": 10, "B": 15, "C": 20, "D": 25, "E": 30}  # 낮을수록 좋음(reverse=True)
        self.patience_threshold = {"A": 2200, "B": 1800, "C": 1400, "D": 1000, "E": 500}
        self.interaction_threshold = {"A": 60, "B": 45, "C": 30, "D": 15, "E": 0}

    # 데이터 로드

    def _load_data(self):
        try:
            if not self.data_path.exists():
                raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {self.data_path}")

            df = pd.read_excel(self.data_path)

            if "월" not in df.columns:
                raise KeyError("엑셀에 '월' 컬럼이 없습니다.")

            df["월"] = pd.to_datetime(df["월"].astype(str), format="%Y%m", errors="coerce")
            df['월_int'] = df['월'].dt.strftime('%Y%m').astype(int)

            if "거래처ID" not in df.columns:
                raise KeyError("엑셀에 '거래처ID' 컬럼이 없습니다.")

            self.df = df
            logger.info(f"[OK] 데이터 로드: {len(self.df)}건")
        except Exception as e:
            logger.error(f"[ERROR] 데이터 로드 실패: {e}")
            self.df = pd.DataFrame()

    # Text2SQL 더미 구현 (✅ 1단계)
    # 실제 연결 지점: 이 함수 내부를 RDB + Text2SQL로 교체하면 됨.
    # ---------------------------
    def text2sql_fetch(self, company_name: str,
                       start_month: Optional[int],
                       end_month: Optional[int]) -> pd.DataFrame:
        """
        실제로는 NL→SQL 변환 후 DB에서 조회.
        지금은 self.df에서 안전하게 필터링하는 더미를 제공.
        """
        base = self.df
        if base.empty:
            return pd.DataFrame()

        df = base[base["거래처ID"] == company_name].copy()
        if start_month and end_month:
            df = df[(df["월_int"] >= start_month) & (df["월_int"] <= end_month)]

        return df.sort_values("월_int")

    # ---------------------------
    # 등급 계산 유틸
    # ---------------------------
    def _get_grade(self, value: float, threshold_dict: Dict[str, float], reverse: bool = False) -> str:
        grades = ["A", "B", "C", "D", "E"]
        if reverse:  # 낮을수록 좋은 지표
            for g in grades:
                if value <= threshold_dict[g]:
                    return g
            return "E"
        else:
            for g in grades:
                if value >= threshold_dict[g]:
                    return g
            return "E"

    def map_grade_to_score(self, grade: str) -> int:
        return {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}.get(grade.upper(), 0)

    def map_score_to_grade(self, score: int) -> str:
        return {5: "A", 4: "B", 3: "C", 2: "D", 1: "E"}.get(score, "E")

    def calculate_company_grade_from_df(self, df: pd.DataFrame, company_name: str) -> Dict[str, Any]:
        if df.empty:
            return {"error": "데이터 없음", "최종등급": "N/A"}

        avg_revenue = df["매출"].mean() if "매출" in df.columns else 0.0
        total_revenue = df["매출"].sum() if "매출" in df.columns else 0.0
        total_budget = df["사용 예산"].sum() if "사용 예산" in df.columns else 0.0

        profit_rate = (total_budget / total_revenue * 100) if total_revenue > 0 else 0.0

        avg_patients = df["총환자수"].mean() if "총환자수" in df.columns else 0.0
        interaction_rate = ((df["총환자수"].sum() * 30000) / total_revenue * 100) if total_revenue > 0 else 0.0

        revenue_grade = self._get_grade(avg_revenue, self.revenue_threshold, reverse=False)
        profit_grade  = self._get_grade(profit_rate,  self.profit_threshold,  reverse=True)
        patients_grade = self._get_grade(avg_patients, self.patience_threshold, reverse=False)
        interaction_grade = self._get_grade(interaction_rate, self.interaction_threshold, reverse=False)

        scores = {
            "매출액": self.map_grade_to_score(revenue_grade),
            "수익률": self.map_grade_to_score(profit_grade),
            "환자수": self.map_grade_to_score(patients_grade),
            "관계도": self.map_grade_to_score(interaction_grade),
        }
        avg_score = sum(scores.values()) / len(scores)
        final_grade = self.map_score_to_grade(round(avg_score))

        return {
            "거래처명": company_name,
            "매출등급": revenue_grade,
            "수익률등급": profit_grade,
            "환자수등급": patients_grade,
            "관계도등급": interaction_grade,
            "최종등급": final_grade,
            "지표요약": {
                "평균매출": avg_revenue,
                "총매출": total_revenue,
                "총예산": total_budget,
                "수익률(%)": profit_rate,
                "평균환자수": avg_patients,
                "관계도(%)": interaction_rate,
            }
        }

    # ---------------------------
    # LLM 공통 호출
    # ---------------------------
    async def use_llm(self, prompt: str) -> str:
        try:
            resp = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return f"AI 분석 생성 실패: {e}"

    # 2번 노드: 등급계산 + 분석(임계값/공식 설명 포함) 프롬프트 합치기 처음에 fetch함수에서 기간필터링을한 데이터를 가져오느데 여기서 start_month, end_month를 파라미터로 받는이유는 period_str위해
    # ---------------------------
    async def grade_and_analysis(self, company_name: str, target_df: pd.DataFrame,             
                                 start_month: Optional[int], end_month: Optional[int]) -> Dict[str, Any]:
        target_df = self.text2sql_fetch(company_name, start_month, end_month)
        grade_result = self.calculate_company_grade_from_df(target_df, company_name)

        thresholds_pretty = json.dumps({
            "매출 임계값": self.revenue_threshold,
            "수익률 임계값(낮을수록 좋음)": self.profit_threshold,
            "환자수 임계값": self.patience_threshold,
            "관계도 임계값": self.interaction_threshold,
            "사용된 공식": {
                "수익률(%)": "(총예산 / 총매출) * 100",
                "관계도(%)": "(총환자수 합계 * 30000) / 총매출 * 100"
            }
        }, ensure_ascii=False, indent=2)

        pretty = json.dumps(grade_result, ensure_ascii=False, indent=2)
        period_str = f"{start_month or '전체기간'} ~ {end_month or '전체기간'}"

        prompt = f"""
너는 제약사 영업 데이터 분석 전문가다.
아래 **등급 계산 결과**와 **임계값/공식**을 바탕으로, 왜 해당 거래처가 그 등급이 되었는지 분석하라.
분석할 때, 각 지표가 어느 임계값 구간에 해당했는지 근거를 들어 설명하고, 지표 간 트레이드오프도 언급하라.

### 대상
- 거래처명: {company_name}
- 분석 기간: {period_str}

### 등급 계산 결과
{pretty}

### 임계값/공식
{thresholds_pretty}

### 작성 지침
1) 매출/수익률/환자수/관계도 각각에 대해, 실제 지표값이 어느 등급 임계구간에 속하는지 근거를 제시하라.
2) 최종등급 산정 로직(지표 점수 평균→반올림)에 대해 설명하라.
3) 간단한 개선포인트 지정
"""
        grade_report = await self.use_llm(prompt)
        return {"grade_report": grade_report, "grade_result": grade_result}

    # ---------------------------
    # 기존 리포트들 (3/4/5번)
    # ---------------------------
    def get_same_grade_companies(self, company_name: str,
                                 start_month: Optional[int] = None,
                                 end_month: Optional[int] = None) -> Dict[str, Any]:
        # 동일 등급 비교는 전체 df 사용(기간 필터 적용)
        base = self.df.copy()
        if base.empty:
            return {"target_grade": "N/A", "target_info": {}, "same_grade_companies": []}

        target_df = base[base["거래처ID"] == company_name].copy()
        if start_month and end_month:
            base = base[(base["월_int"] >= start_month) & (base["월_int"] <= end_month)]
            target_df = target_df[(target_df["월_int"] >= start_month) & (target_df["월_int"] <= end_month)]

        target_grade_data = self.calculate_company_grade_from_df(target_df, company_name)
        target_grade = target_grade_data.get("최종등급", "N/A")

        same_grade_companies = []
        for cid in base["거래처ID"].dropna().unique():
            if cid == company_name:
                continue
            df_c = base[base["거래처ID"] == cid]
            g = self.calculate_company_grade_from_df(df_c, cid).get("최종등급")
            if g == target_grade:
                dept = str(df_c["과"].iloc[0]) if "과" in df_c.columns and not df_c.empty else "정보없음"
                same_grade_companies.append({
                    "거래처ID": cid,
                    "과": dept,
                    "매출": df_c["매출"].mean() if "매출" in df_c.columns else 0.0,
                    "사용 예산": df_c["사용 예산"].mean() if "사용 예산" in df_c.columns else 0.0
                })

        return {
            "target_grade": target_grade,
            "target_info": target_grade_data,
            "same_grade_companies": same_grade_companies
        }

    def split_companies_by_department(self, company_name: str, same_grade_result: Dict[str, Any]) -> Dict[str, Any]:
        subset = self.df[self.df["거래처ID"] == company_name]
        target_department = str(subset["과"].iloc[0]) if "과" in subset.columns and not subset.empty else "정보없음"

        rows = same_grade_result.get("same_grade_companies", [])
        same_grade_df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["거래처ID", "과", "매출", "사용 예산"])

        for c in ["과", "매출", "사용 예산"]:
            if c not in same_grade_df.columns:
                same_grade_df[c] = pd.Series(dtype="object" if c == "과" else "float64")

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
        split = self.split_companies_by_department(company_name, same_grade_result)

        target_df = self.df[self.df["거래처ID"] == company_name].copy()
        if start_month and end_month:
            target_df = target_df[(target_df["월_int"] >= start_month) & (target_df["월_int"] <= end_month)]

        target_avg_revenue = target_df["매출"].mean() if "매출" in target_df.columns else 0.0
        target_avg_budget = target_df["사용 예산"].mean() if "사용 예산" in target_df.columns else 0.0

        same_dept_avg_revenue = split["same_department"]["매출"].mean() if not split["same_department"].empty else 0.0
        diff_dept_avg_budget = split["diff_department"]["사용 예산"].mean() if not split["diff_department"].empty else 0.0

        prompt = f"""
너는 제약사 영업 데이터 분석 전문가이다.
아래 데이터를 기반으로 **대상 병원의 매출과 사용 예산을 같은/다른 진료과 병원들과 비교 분석**하는 보고서를 작성하라.

### 대상 병원
- 이름: {company_name}
- 분석 기간: {start_month or '전체기간'} ~ {end_month or '전체기간'}
- 대상 병원 평균 매출: {target_avg_revenue:,.0f}원
- 대상 병원 평균 사용 예산: {target_avg_budget:,.0f}원
- 진료과: {split['target_department']}

### 비교 그룹
1. 같은 진료과 & 동일 등급 병원 평균 매출: {same_dept_avg_revenue:,.0f}원
2. 다른 진료과 & 동일 등급 병원 평균 사용 예산: {diff_dept_avg_budget:,.0f}원

### 작성 지침
- 우위/열위 지표를 지적하고 개선 포인트를 제안하라.
- 구체적 수치 비교 포함.
"""
        return await self.use_llm(prompt)

    async def generate_growth_analysis_report(self, company_name: str,
                                              start_month: Optional[int] = None,
                                              end_month: Optional[int] = None) -> str:
        company_df = self.df[self.df["거래처ID"] == company_name].copy()
        if start_month and end_month:
            company_df = company_df[(company_df["월_int"] >= start_month) & (company_df["월_int"] <= end_month)]
        if company_df.empty:
            return f"{company_name}의 해당 기간 데이터가 없습니다."

        company_df = company_df.sort_values("월_int")
        cols = [c for c in ["월_int", "매출", "사용 예산", "월방문횟수"] if c in company_df.columns]
        monthly_data = company_df[cols].copy()
        monthly_data_md = monthly_data.to_markdown(index=False)

        start_visits = company_df["월방문횟수"].iloc[0] if "월방문횟수" in company_df.columns else 0.0
        end_visits = company_df["월방문횟수"].iloc[-1] if "월방문횟수" in company_df.columns else 0.0
        avg_visits = company_df["월방문횟수"].mean() if "월방문횟수" in company_df.columns else 0.0

        start_rev = company_df["매출"].iloc[0] if "매출" in company_df.columns else 0.0
        end_rev   = company_df["매출"].iloc[-1] if "매출" in company_df.columns else 0.0
        revenue_growth = (end_rev - start_rev) / start_rev * 100 if start_rev else "데이터 없음"

        start_budget = company_df["사용 예산"].iloc[0] if "사용 예산" in company_df.columns else 0.0
        end_budget   = company_df["사용 예산"].iloc[-1] if "사용 예산" in company_df.columns else 0.0
        budget_growth = ((end_budget - start_budget) / start_budget * 100) if start_budget else "데이터 없음"

        prompt = f"""
너는 제약사 영업 데이터 분석 전문가이며,
아래 월별 데이터를 기반으로 **협력 관계의 성장성**을 분석하라.

### 대상 병원
- 이름: {company_name}
- 분석 기간: {start_month or '전체기간'} ~ {end_month or '전체기간'}

### 월별 데이터 (매출/예산)
{monthly_data_md}

### 참고 지표
- 매출 성장률: {revenue_growth}
- 예산 성장률: {budget_growth}
- 시작 월 방문 횟수: {start_visits}
- 기간 평균 방문 횟수: {avg_visits:.2f}
- 종료 월 방문 횟수: {end_visits}

### 작성 지침
1. 월별 매출 추이와 예산 추이를 함께 분석해, **협력 관계가 균형적으로 성장하고 있는지** 설명하라.
2. 매출만 증가하거나 예산만 증가하는 경우 **관계 불균형 가능성**을 지적하라.
3. 수요(병원 측)와 공급(우리 회사) 관점에서 상호작용 분석을 하라.
4. 방문 횟수 추이를 기반으로 영업 활동 강도 변화(증가/감소/안정)를 평가하라.
"""
        return await self.use_llm(prompt)

    async def generate_sales_strategy_report(
        self,
        company_name: str,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None
    ) -> str:
        df = self.df
        if df is None or df.empty:
            return "데이터가 없습니다."

        # 전체 평균
        overall_avg_patients = float(df["총환자수"].mean(skipna=True)) if "총환자수" in df.columns else 0.0
        overall_avg_visits   = float(df["월방문횟수"].mean(skipna=True)) if "월방문횟수" in df.columns else 0.0
        overall_avg_revenue  = float(df["매출"].mean(skipna=True)) if "매출" in df.columns else 0.0

        # 대상 슬라이스
        company_df = self.text2sql_fetch(company_name, start_month, end_month)
        if company_df.empty:
            return f"{company_name}의 데이터가 존재하지 않습니다."

        company_avg_patients = float(company_df["총환자수"].mean(skipna=True)) if "총환자수" in company_df.columns else 0.0
        company_avg_visits   = float(company_df["월방문횟수"].mean(skipna=True)) if "월방문횟수" in company_df.columns else 0.0
        company_avg_revenue  = float(company_df["매출"].mean(skipna=True)) if "매출" in company_df.columns else 0.0

        # 비율 계산 (직접 연산)
        if overall_avg_patients != 0:
            patients_ratio = ((company_avg_patients - overall_avg_patients) / overall_avg_patients) * 100.0
        else:
            patients_ratio = 0.0

        if overall_avg_revenue != 0:
            revenue_ratio = ((company_avg_revenue - overall_avg_revenue) / overall_avg_revenue) * 100.0
        else:
            revenue_ratio = 0.0

        if overall_avg_visits != 0:
            visits_ratio = ((company_avg_visits - overall_avg_visits) / overall_avg_visits) * 100.0
        else:
            visits_ratio = 0.0

        # 최근 3개월 대비 자체 평균
        if company_avg_revenue != 0:
            recent_revenue = float(company_df["매출"].tail(3).mean(skipna=True)) if "매출" in company_df.columns else 0.0
            recent_ratio = ((recent_revenue - company_avg_revenue) / company_avg_revenue) * 100.0
        else:
            recent_revenue = 0.0
            recent_ratio = 0.0

        # 인사이트 도출
        insights = []
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
        return await self.use_llm(prompt)


# Graph (Start → 2/3/4/5 동시 → Merge)

def build_full_graph(agent: ClientAgent):
    graph = StateGraph(ReportState)

    # ✅ Start: 1단계(Text2SQL) — 데이터 확보 & 상태 저장
    async def start_node(state: ReportState):
        company = state["company_name"]
        s, e = state["start_month"], state["end_month"]

        target_df = agent.text2sql_fetch(company, s, e)
        target_df_md = target_df[["월_int", "매출", "사용 예산", "총환자수", "월방문횟수"] \
                         if set(["월_int","매출","사용 예산","총환자수","월방문횟수"]).issubset(target_df.columns) \
                         else target_df.columns].to_markdown(index=False) if not target_df.empty else "데이터 없음"


        return state

    # ✅ 2번: 등급 계산+분석 (합치기)
    async def grade_and_analysis_node(state: ReportState):
        company = state["company_name"]
        s, e = state["start_month"], state["end_month"]
        target_df = agent.text2sql_fetch(company, s, e)  # Start에서 가져왔지만 안전하게 재조회
        out = await agent.grade_and_analysis(company, target_df, s, e)
        state["grade_result"] = out["grade_result"]
        state["grade_report"] = out["grade_report"]
        return state

    # 3/4/5번: 동일 등급 / 성장성 / 전략
    async def same_grade_node(state: ReportState):
        company = state["company_name"]
        s, e = state["start_month"], state["end_month"]
        report = await agent.analyze_same_grade_departments(company, s, e)
        return {"same_grade_report": report}

    async def growth_node(state: ReportState):
        company = state["company_name"]
        s, e = state["start_month"], state["end_month"]
        report = await agent.generate_growth_analysis_report(company, s, e)
        return {"growth_report": report}

    async def strategy_node(state: ReportState):
        company = state["company_name"]
        report = await agent.generate_sales_strategy_report(company)
        return {"strategy_report": report}

    # Merge
    async def merge_node(state: ReportState):
        grade_result = json.dumps(state.get("grade_result", {}), ensure_ascii=False, indent=2)
        prompt = f"""
너는 제약사 영업 데이터 컨설턴트이다.
아래 2~5번 리포트를 종합하여 통합 보고서를 작성하라.

### (2) 등급 분석
**등급 계산 결과**
{grade_result}
{state.get('grade_report')}

### (3) 동일 등급 비교 분석
{state.get('same_grade_report')}

### (4) 성장성 분석
{state.get('growth_report')}

### (5) 영업 전략 제안
{state.get('strategy_report')}
"""
        merged = await agent.use_llm(prompt)
        state["final_report"] = merged
        return state

    
    graph.add_node("start", start_node)
    graph.add_node("grade_and_analysis", grade_and_analysis_node)  
    graph.add_node("same_grade", same_grade_node)                  
    graph.add_node("growth", growth_node)                          
    graph.add_node("strategy", strategy_node)                      
    graph.add_node("merge", merge_node)

    
    graph.set_entry_point("start")
    graph.add_edge("start", "grade_and_analysis")
    graph.add_edge("start", "same_grade")
    graph.add_edge("start", "growth")
    graph.add_edge("start", "strategy")

    graph.add_edge("grade_and_analysis", "merge")
    graph.add_edge("same_grade", "merge")
    graph.add_edge("growth", "merge")
    graph.add_edge("strategy", "merge")

    graph.set_finish_point("merge")
    return graph.compile()

# -------------------------------
# 파이프라인 엔트리
# -------------------------------
async def run_full_pipeline(agent: ClientAgent,
                            company_name: str,
                            start_month: Optional[int] = None,
                            end_month: Optional[int] = None) -> ReportState:
    initial: ReportState = {
        "company_name": company_name,
        "start_month": start_month,
        "end_month": end_month,
        "final_report": None,
        "grade_result": None,
        "grade_report": None,
        "same_grade_report": None,
        "growth_report": None,
        "strategy_report": None,    
        "target_df_markdown": None,
        "target_df_summary": None,
    }
    graph = build_full_graph(agent)
    return await graph.ainvoke(initial)
