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

# 중앙 설정 import
from app.core.config import config


async def parse_query_params(query: str) -> Dict:
    """쿼리에서 거래처명과 기간 추출"""
    try:
        # OpenAI API 사용 가능 여부 확인
        if not config.get_openai_api_key():
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
    avg_patients = filtered_df["총환자수"].mean()
    avg_visits = filtered_df["월방문횟수"].mean()
    
    # 등급 판정
    revenue_grade = _get_grade(avg_revenue, thresholds.revenue_threshold)
    profit_grade = _get_grade(profit_rate, thresholds.profit_threshold, reverse=True)
    patient_grade = _get_grade(avg_patients, thresholds.patience_threshold)
    visit_grade = _get_grade(avg_visits, thresholds.interaction_threshold)
    
    # 점수 계산
    scores = {
        "매출액": map_grade_to_score(revenue_grade),
        "수익률": map_grade_to_score(profit_grade),
        "환자수": map_grade_to_score(patient_grade),
        "관계도": map_grade_to_score(visit_grade)
    }
    
    # 가중치 적용
    weights = {"매출액": 0.4, "수익률": 0.3, "환자수": 0.2, "관계도": 0.1}
    total_score = sum(scores[k] * weights[k] for k in scores)
    final_grade = map_score_to_grade(total_score)
    
    return {
        "거래처명": company_name,
        "최종등급": final_grade,
        "총점": round(total_score, 2),
        "분석기간": f"{start_month}~{end_month}" if start_month else "전체기간",
        "세부등급": {
            "매출액": {
                "등급": revenue_grade,
                "평균": int(avg_revenue),
                "총액": int(total_revenue)
            },
            "수익률": {
                "등급": profit_grade,
                "비율": round(profit_rate, 1)
            },
            "환자수": {
                "등급": patient_grade,
                "평균": int(avg_patients)
            },
            "관계도": {
                "등급": visit_grade,
                "평균방문": round(avg_visits, 1)
            }
        },
        "요약": {
            "총매출": int(total_revenue),
            "월평균매출": int(avg_revenue),
            "평균환자수": int(avg_patients),
            "월평균방문": round(avg_visits, 1)
        }
    }


def _get_grade(value: float, threshold_dict: Dict, reverse: bool = False) -> str:
    """임계값 기준으로 등급 판정"""
    if reverse:  # 수익률처럼 낮을수록 좋은 경우
        if value <= threshold_dict.get("A", 10):
            return "A"
        elif value <= threshold_dict.get("B", 15):
            return "B"
        elif value <= threshold_dict.get("C", 20):
            return "C"
        elif value <= threshold_dict.get("D", 25):
            return "D"
        else:
            return "E"
    else:
        if value >= threshold_dict.get("A", 1000000):
            return "A"
        elif value >= threshold_dict.get("B", 500000):
            return "B"
        elif value >= threshold_dict.get("C", 100000):
            return "C"
        elif value >= threshold_dict.get("D", 50000):
            return "D"
        else:
            return "E"


async def generate_analysis_report(company_name: str, grade_result: Dict, 
                                 df: pd.DataFrame, start_month: Optional[int] = None,
                                 end_month: Optional[int] = None) -> str:
    """종합 분석 레포트 생성"""
    
    # 기본 레포트 생성
    report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 거래처 분석 레포트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏢 거래처명: {company_name}
📅 분석기간: {grade_result.get('분석기간', '전체기간')}

🎯 종합 평가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 최종 등급: {grade_result['최종등급']}등급
• 종합 점수: {grade_result['총점']}점

📈 세부 평가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 매출액 등급: {grade_result['세부등급']['매출액']['등급']} (월평균: {grade_result['세부등급']['매출액']['평균']:,}원)
• 수익률 등급: {grade_result['세부등급']['수익률']['등급']} (비율: {grade_result['세부등급']['수익률']['비율']}%)
• 환자수 등급: {grade_result['세부등급']['환자수']['등급']} (평균: {grade_result['세부등급']['환자수']['평균']:,}명)
• 관계도 등급: {grade_result['세부등급']['관계도']['등급']} (월평균 방문: {grade_result['세부등급']['관계도']['평균방문']}회)

💼 거래 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 총 매출액: {grade_result['요약']['총매출']:,}원
• 월평균 매출: {grade_result['요약']['월평균매출']:,}원
• 평균 환자수: {grade_result['요약']['평균환자수']:,}명
• 월평균 방문: {grade_result['요약']['월평균방문']}회
"""
    
    # OpenAI API를 사용한 상세 분석 (가능한 경우)
    if config.get_openai_api_key():
        try:
            detailed_analysis = await _generate_ai_analysis(company_name, grade_result, df)
            report += f"\n\n📋 상세 분석\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{detailed_analysis}"
        except:
            pass
    
    # 추천사항 추가
    recommendations = _generate_recommendations(grade_result)
    report += f"\n\n💡 추천사항\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{recommendations}"
    
    return report


async def _generate_ai_analysis(company_name: str, grade_result: Dict, df: pd.DataFrame) -> str:
    """AI를 사용한 상세 분석"""
    client = AsyncOpenAI()
    
    prompt = f"""
거래처 분석 결과를 바탕으로 간단한 분석 코멘트를 작성해주세요.

거래처: {company_name}
최종등급: {grade_result['최종등급']}
세부등급: 매출({grade_result['세부등급']['매출액']['등급']}), 수익률({grade_result['세부등급']['수익률']['등급']}), 
환자수({grade_result['세부등급']['환자수']['등급']}), 관계도({grade_result['세부등급']['관계도']['등급']})

3-4문장으로 핵심만 작성해주세요.
"""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )
    
    return response.choices[0].message.content


def _generate_recommendations(grade_result: Dict) -> str:
    """등급별 추천사항 생성"""
    final_grade = grade_result['최종등급']
    weak_areas = []
    
    # 약점 분석
    for area, data in grade_result['세부등급'].items():
        if data['등급'] in ['D', 'E']:
            weak_areas.append(area)
    
    recommendations = []
    
    # 등급별 기본 추천
    if final_grade in ['A', 'B']:
        recommendations.append("• 현재 우수한 거래 관계를 유지하고 있습니다")
        recommendations.append("• 정기적인 신제품 소개로 매출 확대 기회 모색")
    elif final_grade == 'C':
        recommendations.append("• 거래 관계 개선을 위한 적극적인 관리 필요")
        recommendations.append("• 맞춤형 프로모션으로 거래 활성화 추진")
    else:
        recommendations.append("• 시급한 관계 개선이 필요합니다")
        recommendations.append("• 담당자 방문 빈도 증가 및 특별 관리")
    
    # 약점별 추천
    if "매출액" in weak_areas:
        recommendations.append("• 제품 포트폴리오 다양화로 매출 증대")
    if "환자수" in weak_areas:
        recommendations.append("• 환자 증가에 따른 수요 대응 전략 수립")
    if "관계도" in weak_areas:
        recommendations.append("• 방문 횟수 증가 및 관계 강화 필요")
    
    return "\n".join(recommendations)