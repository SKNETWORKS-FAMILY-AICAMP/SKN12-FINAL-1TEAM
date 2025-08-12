from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import openai
import os
import json

class EmployeeQueryAnalyzer:
    """직원 실적 분석 쿼리 분석 클래스 - LLM 기반 통합 분석"""
    
    def __init__(self):
        pass  # 직원명 처리 불필요
    
    def analyze_query(self, query: str) -> Optional[Dict[str, Any]]:
        """사용자 쿼리를 LLM을 사용하여 분석합니다."""
        # LLM 분석 시도
        llm_analysis = self.analyze_with_llm(query)
        
        if llm_analysis:
            # LLM 분석 결과에 기본값 설정
            return self._set_defaults(llm_analysis)
        else:
            # LLM 분석 실패 시 None 반환
            return None
    
    def analyze_with_llm(self, query: str) -> Optional[Dict[str, Any]]:
        """LLM을 사용하여 쿼리를 정확히 분석합니다."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return None
            
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
다음 직원 실적 분석 요청을 분석하여 JSON 형태로 정보를 추출해주세요:

요청: "{query}"

추출해야 할 정보:
1. employee_name: null (직원명은 세션에서 처리하므로 항상 null)
2. start_period: 시작 기간 (YYYYMM 형식, 예: "202312")
3. end_period: 종료 기간 (YYYYMM 형식, 예: "202403")

기간 추출 규칙:
- "작년": {datetime.now().year - 1}01 ~ {datetime.now().year - 1}12
- "올해": {datetime.now().year}01 ~ {datetime.now().year}12
- "이번 달": {datetime.now().strftime('%Y%m')} ~ {datetime.now().strftime('%Y%m')}
- "지난 달": {(datetime.now() - timedelta(days=30)).strftime('%Y%m')} ~ {(datetime.now() - timedelta(days=30)).strftime('%Y%m')}
- "최근 N개월": 현재 기준으로 N개월 전부터 현재까지
- "1분기", "2분기", "3분기", "4분기": 해당 분기 기간
- "상반기": 1월~6월, "하반기": 7월~12월
- 구체적 날짜: YYYYMM 형식으로 변환

응답은 다음 JSON 형식으로만 해주세요:
{{
    "employee_name": null,
    "start_period": "202312",
    "end_period": "202403"
}}

주의사항:
- employee_name은 항상 null (직원명은 API에서 별도 처리)
- 기간이 명시되지 않으면 최근 3개월로 설정
- 쿼리에 직원명이 포함되어도 무시하고 기간만 추출
"""
            
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),  # 환경변수로 모델 설정 가능
                messages=[
                    {"role": "system", "content": "당신은 기간 정보를 추출하는 전문가입니다. 직원명은 무시하고 기간 정보만 추출하세요. 항상 유효한 JSON 형식으로만 응답하세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 결과 검증 및 정규화
            result = self._validate_and_normalize_result(result)
            
            return result
            
        except Exception as e:
            print(f"LLM 쿼리 분석 오류: {e}")
            return None
    
    def _validate_and_normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 분석 결과를 검증하고 정규화합니다."""
        # 필수 필드 확인 및 기본값 설정
        validated_result = {
            "employee_name": None,  # 항상 None (직원명은 API에서 처리)
            "start_period": result.get("start_period"),
            "end_period": result.get("end_period")
        }
        
        # 기간 형식 검증
        for period_key in ["start_period", "end_period"]:
            period = validated_result[period_key]
            if period:
                period_str = str(period)
                # 6자리 숫자인지 확인 (YYYYMM 형식)
                if not (len(period_str) == 6 and period_str.isdigit()):
                    # 잘못된 형식이면 null로 설정
                    validated_result[period_key] = None
        
        return validated_result
    
    def _set_defaults(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """기본값을 설정합니다."""
        # 직원명은 항상 None (API에서 처리)
        analysis_result["employee_name"] = None
        
        # 기간이 없으면 None으로 설정 (오류 처리로 넘김)
        if not analysis_result.get("start_period"):
            analysis_result["start_period"] = None
        if not analysis_result.get("end_period"):
            analysis_result["end_period"] = None
        
        return analysis_result
    
    def get_enhanced_analysis(self, query: str) -> Optional[Dict[str, Any]]:
        """LLM 기반 통합 분석을 수행합니다."""
        return self.analyze_query(query)