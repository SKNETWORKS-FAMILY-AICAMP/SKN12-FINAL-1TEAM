"""
Client Analysis Tools - 간소화된 버전
거래처 분석을 위한 도구 함수들
"""
import pandas as pd
import os
from typing import Dict, Optional, Tuple
from openai import AsyncOpenAI
import json
import re

# 같은 디렉토리의 모듈
from .grade_utils import map_grade_to_score, map_score_to_grade
from . import thresholds


async def parse_query_params(query: str) -> Dict:
    """쿼리에서 거래처명과 기간 추출"""
    try:
        # OpenAI API 사용 가능 여부 확인
        if not os.getenv("OPENAI_API_KEY"):
            # API 키가 없으면 간단한 파싱
            return _simple_parse(query)
        
        client = AsyncOpenAI()
        
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
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        # JSON 파싱
        json_text = response.choices[0].message.content
        json_text = re.sub(r"^```json\s*|\s*```$", "", json_text.strip())
        result = json.loads(json_text)
        
        return {
            "success": True,
            "company_name": result["company_name"],
            "start_month": int(result["start_month"]) if result["start_month"] else None,
            "end_month": int(result["end_month"]) if result["end_month"] else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _simple_parse(query: str) -> Dict:
    """API 키 없을 때 간단한 파싱"""
    # 쿼리에서 거래처명 찾기 (가장 긴 단어 조합)
    words = query.split()
    company_name = ""
    
    for word in words:
        if "분석" in word or "해줘" in word or "보여줘" in word:
            break
        company_name += word + " "
    
    company_name = company_name.strip()
    
    return {
        "success": True,
        "company_name": company_name,
        "start_month": None,
        "end_month": None
    }


def calculate_company_grade(company_name: str, df: pd.DataFrame, 
                          start_month: Optional[int] = None, 
                          end_month: Optional[int] = None) -> Dict:
    """거래처 종합 등급 계산"""
    
    # 데이터 필터링
    filtered_df = df[df["거래처ID"] == company_name].copy()
    
    if start_month and end_month:
        # 월을 정수로 변환하여 비교
        filtered_df["월_int"] = pd.to_datetime(filtered_df["월"]).dt.strftime('%Y%m').astype(int)
        filtered_df = filtered_df[
            (filtered_df["월_int"] >= start_month) & 
            (filtered_df["월_int"] <= end_month)
        ]
    
    if filtered_df.empty:
        return {
            "error": "해당 기간의 데이터가 없습니다",
            "최종등급": "N/A"
        }
    
    # 각 항목별 평균 계산
    avg_revenue = filtered_df["매출"].mean()
    total_revenue = filtered_df["매출"].sum()
    total_budget = filtered_df["사용 예산"].sum()
    profit_rate = (total_budget / total_revenue * 100) if total_revenue > 0 else 0
    avg_patience = filtered_df["총환자수"].mean()
    avg_visits = filtered_df["월방문횟수"].mean()
    total_patience = filtered_df["총환자수"].sum()
    interaction_rate = (total_patience * 30000 / total_revenue) * 100
    
    # 등급 판정
    revenue_grade = _get_grade(avg_revenue, thresholds.revenue_threshold)
    profit_grade = _get_grade(profit_rate, thresholds.profit_threshold, reverse=True)
    patience_grade = _get_grade(avg_patience, thresholds.patience_threshold)
    interaction_grade = _get_grade(interaction_rate, thresholds.interaction_threshold)
    
    # 점수 계산
    scores = {
        "매출액": map_grade_to_score(revenue_grade),
        "수익률": map_grade_to_score(profit_grade),
        "환자수": map_grade_to_score(patience_grade),
        "관계도": map_grade_to_score(interaction_grade)
    }
    
    # 최종 등급
    average_score = sum(scores.values()) / len(scores)  # 4개 점수 평균
    final_score = round(average_score)       
    final_grade = map_score_to_grade(final_score)
    
    return {
        "거래처명": company_name,
        "매출등급": revenue_grade,
        "수익률등급": profit_grade,
        "환자수등급": patience_grade,
        "관계도등급": interaction_grade,
        "최종등급": final_grade
    }


def _get_grade(value: float, threshold_dict: Dict[str, float], reverse: bool = False) -> str:
    """
    임계값 기준으로 등급 판정
    - reverse=False : 값이 클수록 좋은 경우 (A > B > C ...)
    - reverse=True  : 값이 작을수록 좋은 경우 (A < B < C ...)
    """
    # A~E 순서대로 비교
    grades = ["A", "B", "C", "D", "E"]

    if reverse:
        # 낮을수록 좋은 경우
        for grade in grades:
            if value <= threshold_dict[grade]:
                return grade
        return "E"
    else:
        # 높을수록 좋은 경우
        for grade in grades:
            if value >= threshold_dict[grade]:
                return grade
        return "E"

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
client = AsyncOpenAI(api_key=api_key)

#등급분류분석 함수
async def generate_grade_analysis_report(
    company_name: str,
    grade_result: Dict,
    df: pd.DataFrame,
    start_month: Optional[int] = None,
    end_month: Optional[int] = None
) -> str:
    """
    거래처 등급 분석 리포트 생성
    - grade_result: 해당 거래처의 최종 등급 및 세부 지표
    - df: 원본 데이터 
    """

    # 1. 프롬프트 구성
    prompt = f"""
너는 제약사 영업 데이터 분석 전문가이며, 
주어진 거래처의 종합 등급과 세부 지표를 바탕으로 **왜 해당 거래처가 그 등급에 선정되었는지**를 설명하는 분석 보고서를 작성해야 한다.

### 분석 대상
- 거래처명: {company_name}
- 분석 기간: {start_month or '전체기간'} ~ {end_month or '전체기간'}

필요 데이터:
company_df = df[df["거래처ID"] == company_name]

등급기준:

- 매출: A=3000000, B=2000000, C=1000000, D=500000, E=100000
- 수익률: (예산/매출)*100, A=10, B=15, C=20, D=25, E=30
- 환자수: A=2200, B=1800, C=1400, D=1000, E=500
- 관계도: (30000*환자수)/매출, A=60, B=45, C=30, D=15, E=0


### 등급 결과 요약
{json.dumps(grade_result, ensure_ascii=False, indent=2)}

### 작성 지침
1. 먼저 등급 산출 배경을 설명하라 (어떤 지표가 강점이고 어떤 지표가 약점인지).
2. 주요 지표(매출, 수익률, 환자수, 관계도)를 각각 분석하라.
3. 해당 거래처가 이 등급에 속한 이유를 중심으로 구체적으로 기술하라.
"""

    # 2. OpenAI API 호출 (AI 분석)
    detailed_analysis = ""
    if os.getenv("OPENAI_API_KEY"):
        try:
            detailed_analysis = await generate_grade_llm_analysis_report(prompt)
        except Exception as e:
            detailed_analysis = f"AI 분석 생성 실패: {e}"


    # 4. 최종 보고서 
    report = f"""
# {company_name} 거래처 등급 분석 리포트

{detailed_analysis}

"""

    return report


#llm에 요청하는 함수
async def generate_grade_llm_analysis_report(prompt):
     """프롬프트 기반 LLM 분석 호출"""
     response = await client.chat.completions.create(
        model="gpt-4.1",  # 모델 선택
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )   
     return response.choices[0].message.content.strip()



# 동일 등급 거래처 추출 함수

from typing import Dict, Optional
import pandas as pd
import json


def get_same_grade_companies(
    company_name: str,
    df: pd.DataFrame,
    start_month: Optional[int] = None,
    end_month: Optional[int] = None
):
    """
    특정 거래처와 같은 기간 내에서 같은 등급인 회사 추출
    - 대상 거래처의 최종 등급 산출
    - 동일 등급인 회사들 반환
    """

    # 1. 대상 회사 등급 계산
    target_grade_data = calculate_company_grade(company_name, df, start_month, end_month)
    target_grade = target_grade_data["최종등급"]

    # 2. 전체 데이터 기간 필터링
    filtered_df = df.copy()
    if start_month and end_month:
        filtered_df["월_int"] = pd.to_datetime(filtered_df["월"]).dt.strftime('%Y%m').astype(int)
        filtered_df = filtered_df[
            (filtered_df["월_int"] >= start_month) &
            (filtered_df["월_int"] <= end_month)
        ]

    # 3. 전체 회사별 최종등급 계산 후 같은 등급만 추출
    same_grade_companies = []
    for cid in filtered_df["거래처ID"].unique():
        if cid == company_name:
            continue
        grade_data = calculate_company_grade(cid, df, start_month, end_month)
        if grade_data["최종등급"] == target_grade:
            same_grade_companies.append({
                "거래처ID": cid,
                "진료과": filtered_df[filtered_df["거래처ID"] == cid]["진료과"].iloc[0]
            })

    return {
        "target_grade": target_grade,
        "target_info": target_grade_data,
        "same_grade_companies": pd.DataFrame(same_grade_companies)  
    }


# 동일등급 거래처들 전료과 분리 함수

def split_companies_by_department(
    company_name: str,
    df: pd.DataFrame,
    same_grade_result: Dict
):
    """
    같은 등급 회사들을 같은 진료과 / 다른 진료과로 분리
    """
    # 1. 대상 회사의 진료과 확인
    target_department = df[df["거래처ID"] == company_name]["진료과"].iloc[0]

    # 2. 같은 등급 회사 리스트 DataFrame
    same_grade_df = same_grade_result["same_grade_companies"]

    # 3. 같은 진료과 / 다른 진료과로 분리
    same_department_df = same_grade_df[same_grade_df["진료과"] == target_department]
    diff_department_df = same_grade_df[same_grade_df["진료과"] != target_department]

    return {
        "same_department": same_department_df,
        "diff_department": diff_department_df,
        "target_department": target_department
    }


# llm 동일 등급 거래처들 비교 분석 함수

async def analyze_same_grade_departments(
    company_name: str,
    df: pd.DataFrame,
    start_month: Optional[int] = None,
    end_month: Optional[int] = None
) -> str:
    """
    동일 등급 병원 중 같은 진료과 / 다른 진료과 비교 후 LLM 분석 요청
    """

    # 1. 동일 등급 병원 추출
    same_grade_result = get_same_grade_companies(company_name, df, start_month, end_month)

    # 2. 같은 진료과 / 다른 진료과 분리
    split_result = split_companies_by_department(company_name, df, same_grade_result)

    # 3. 분석 대상 데이터 준비
    target_df = df[(df["거래처ID"] == company_name)]
    if start_month and end_month:
        target_df = target_df.copy()
        target_df["월_int"] = pd.to_datetime(target_df["월"]).dt.strftime('%Y%m').astype(int)
        target_df = target_df[
            (target_df["월_int"] >= start_month) & 
            (target_df["월_int"] <= end_month)
        ]

    # 대상 거래처 매출 및 사용예산 평균
    target_avg_revenue = target_df["매출"].mean()
    target_avg_budget = target_df["사용 예산"].mean()

    # 같은 진료과 병원 평균 매출
    same_dept_avg_revenue = split_result["same_department"]["매출"].mean() if not split_result["same_department"].empty else 0

    # 다른 진료과 병원 평균 사용예산
    diff_dept_avg_budget = split_result["diff_department"]["사용 예산"].mean() if not split_result["diff_department"].empty else 0

    # 4. LLM 프롬프트 구성
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

    # 5. LLM 함수호출
    try:
        analysis_report = await generate_grade_llm_analysis_report(prompt)
    except Exception as e:
        analysis_report = f"AI 분석 생성 실패: {e}"

    return analysis_report


# 성중분석 레포트 함수

async def generate_growth_analysis_report(
    company_name: str,
    df: pd.DataFrame,
    start_month: Optional[int] = None,
    end_month: Optional[int] = None
) -> str:
    """
    특정 거래처의 성장 분석 레포트 생성 (매출-예산 관계 중심)
    """

    # 1. 대상 병원 데이터 필터링
    company_df = df[df["거래처ID"] == company_name].copy()

    # 기간 필터링
    if start_month and end_month:
        company_df["월_int"] = pd.to_datetime(company_df["월"]).dt.strftime('%Y%m').astype(int)
        company_df = company_df[
            (company_df["월_int"] >= start_month) &
            (company_df["월_int"] <= end_month)
        ]

    if company_df.empty:
        return f"{company_name}의 해당 기간 데이터가 없습니다."

    # 2. 월별 매출/예산 추이 계산
    monthly_data = company_df.sort_values(by="월_int")[["월_int", "매출", "사용 예산"]]

    # 성장률 계산 (첫달 대비 마지막달)
    start_revenue = monthly_data["매출"].iloc[0]
    end_revenue = monthly_data["매출"].iloc[-1]
    revenue_growth = ((end_revenue - start_revenue) / start_revenue * 100) if start_revenue else 0

    start_budget = monthly_data["사용 예산"].iloc[0]
    end_budget = monthly_data["사용 예산"].iloc[-1]
    budget_growth = ((end_budget - start_budget) / start_budget * 100) if start_budget else 0

    # 3. LLM 프롬프트 구성
    prompt = f"""
너는 제약사 영업 데이터 분석 전문가이며,
아래 월별 데이터를 기반으로 **우리 제약사와 거래처 간 관계의 성장성**을 분석하는 보고서를 작성해야 한다.

### 대상 병원
- 이름: {company_name}
- 분석 기간: {start_month or '전체기간'} ~ {end_month or '전체기간'}

### 월별 데이터 (매출/예산)
{monthly_data.to_string(index=False)}

### 참고 지표
- 매출 성장률: {revenue_growth:.2f}%
- 예산 성장률: {budget_growth:.2f}%

### 작성 지침
1. 월별 매출 추이와 예산 추이를 함께 분석해, **협력 관계가 균형적으로 성장하고 있는지** 설명하라.
2. 매출만 증가하거나 예산만 증가하는 경우 **관계 불균형 가능성**을 지적하라.
3. 수요(병원 측)와 공급(우리 회사) 관점에서 상호작용 분석을 하라.
4. 마지막에 관계 개선 혹은 강화 전략을 제시하라.
"""

    # 4. LLM 호출
    try:
        growth_report = await generate_grade_llm_analysis_report(prompt)
    except Exception as e:
        growth_report = f"AI 분석 생성 실패: {e}"

    return growth_report


# 영업전략 보고서 작성

async def generate_sales_strategy_report(
    company_name: str,
    df: pd.DataFrame
) -> str:
    """
    특정 거래처의 영업전략 분석 보고서 생성
    - 전체 거래처 평균 대비 환자수, 매출, 방문횟수 비교
    """

    # 1. 전체 평균 계산
    overall_avg_patients = df["총환자수"].mean()
    overall_avg_visits = df["월방문횟수"].mean()

    # 2. 특정 거래처 데이터 필터링
    company_df = df[df["거래처ID"] == company_name].copy()

    if company_df.empty:
        return f"{company_name}의 데이터가 존재하지 않습니다."

    # 3. 대상 거래처 평균 계산
    company_avg_patients = company_df["총환자수"].mean()
    company_avg_revenue = company_df["매출"].mean()
    company_avg_visits = company_df["월방문횟수"].mean()

    # 4. 전체 매출 평균 (비교용)
    overall_avg_revenue = df["매출"].mean()

    # 5. 조건 판단
    insights = []

    # 미개척시장 판단
    if company_avg_patients > overall_avg_patients and company_avg_revenue < overall_avg_revenue:
        insights.append("환자 수는 많지만 매출이 낮아 미개척 시장으로 볼 수 있습니다.")

    # 핵심고객 판단
    if company_avg_patients > overall_avg_patients and company_avg_revenue > overall_avg_revenue:
        insights.append("환자 수와 매출 모두 평균 이상으로 핵심 고객으로 간주할 수 있습니다.")

    # 개선 필요 판단
    if company_avg_visits > overall_avg_visits and company_avg_revenue < overall_avg_revenue:
        insights.append("방문 횟수는 많지만 매출이 낮아 방문 전략 개선이 필요합니다.")

    # 6. 월별 매출 추이
    monthly_revenue_trend = company_df.sort_values("월")[["월", "매출"]].to_string(index=False)

    # 7. LLM 프롬프트 작성
    prompt = f"""
너는 제약사 영업전략 컨설턴트이며, 
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
1. 위 비교 데이터를 활용해 전략적 시사점을 제시하라.
2. 매출과 환자수/방문 횟수 간 불균형 원인을 추론하라.
3. 향후 영업 전략(접근 방식, 예산 배분, 추가 활동 제안)을 구체적으로 작성하라.
"""

    # 8. LLM 호출
    try:
        strategy_report = await generate_grade_llm_analysis_report(prompt)
    except Exception as e:
        strategy_report = f"AI 분석 생성 실패: {e}"

    return strategy_report
