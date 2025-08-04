from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import openai
import os
import json

class EmployeeQueryAnalyzer:
    """직원 실적 분석 쿼리 분석 클래스 - LLM 기반 통합 분석"""
    
    def __init__(self):
        self.common_employee_names = ["최수아", "조시현"]  # 알려진 직원명들
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """사용자 쿼리를 LLM을 사용하여 분석합니다."""
        # LLM 분석 시도
        llm_analysis = self.analyze_with_llm(query)
        
        if llm_analysis:
            # LLM 분석 결과에 기본값 설정
            return self._set_defaults(llm_analysis)
        else:
            # LLM 분석 실패 시 기본 분석 결과 반환
            return self._get_fallback_analysis(query)
    
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
1. employee_name: 직원명 (쿼리에서 명확히 언급된 직원명만 추출, 없으면 null)
2. start_period: 시작 기간 (YYYYMM 형식, 예: "202312")
3. end_period: 종료 기간 (YYYYMM 형식, 예: "202403")
4. analysis_type: 분석 유형 ("종합분석", "트렌드분석", "목표달성분석", "제품분석", "거래처분석", "월별분석" 중 하나)
5. specific_requests: 특정 요청사항 배열 (예: ["보고서 생성", "차트 분석", "비교 분석", "개선 방안", "예측 분석"])
6. confidence: 분석 신뢰도 (0.0 ~ 1.0)

기간 추출 규칙:
- "작년": {datetime.now().year - 1}01 ~ {datetime.now().year - 1}12
- "올해": {datetime.now().year}01 ~ {datetime.now().year}12
- "이번 달": {datetime.now().strftime('%Y%m')} ~ {datetime.now().strftime('%Y%m')}
- "지난 달": {(datetime.now() - timedelta(days=30)).strftime('%Y%m')} ~ {(datetime.now() - timedelta(days=30)).strftime('%Y%m')}
- "최근 N개월": 현재 기준으로 N개월 전부터 현재까지
- 구체적 날짜: YYYYMM 형식으로 변환

응답은 다음 JSON 형식으로만 해주세요:
{{
    "employee_name": null,
    "start_period": "202312",
    "end_period": "202403",
    "analysis_type": "종합분석",
    "specific_requests": ["보고서 생성"],
    "confidence": 0.9
}}

주의사항:
- 직원명이 명확히 언급되지 않으면 employee_name을 null로 설정
- 기간이 명시되지 않으면 기본값으로 "202312" ~ "202403" 사용
- 분석 유형이 명시되지 않으면 "종합분석" 사용
- 특정 요청사항이 없으면 빈 배열 [] 사용
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 직원 실적 분석 요청을 정확히 파싱하는 전문가입니다. 항상 유효한 JSON 형식으로만 응답하세요."},
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
            "employee_name": result.get("employee_name"),
            "start_period": result.get("start_period", "202312"),
            "end_period": result.get("end_period", "202403"),
            "analysis_type": result.get("analysis_type", "종합분석"),
            "specific_requests": result.get("specific_requests", []),
            "confidence": min(max(result.get("confidence", 0.8), 0.0), 1.0)
        }
        
        # 직원명 검증
        if validated_result["employee_name"]:
            # 알려진 직원명 목록에 있는지 확인
            if validated_result["employee_name"] not in self.common_employee_names:
                # 유사한 이름이 있는지 확인
                for known_name in self.common_employee_names:
                    if known_name in validated_result["employee_name"] or validated_result["employee_name"] in known_name:
                        validated_result["employee_name"] = known_name
                        break
                else:
                    # 유사한 이름이 없으면 null로 설정
                    validated_result["employee_name"] = None
        
        # 기간 형식 검증
        for period_key in ["start_period", "end_period"]:
            period = validated_result[period_key]
            if period:
                period_str = str(period)
                # 6자리 숫자인지 확인 (YYYYMM 형식)
                if not (len(period_str) == 6 and period_str.isdigit()):
                    # 잘못된 형식이면 기본값 사용
                    validated_result[period_key] = "202312" if period_key == "start_period" else "202403"
        
        # 분석 유형 검증
        valid_analysis_types = ["종합분석", "트렌드분석", "목표달성분석", "제품분석", "거래처분석", "월별분석"]
        if validated_result["analysis_type"] not in valid_analysis_types:
            validated_result["analysis_type"] = "종합분석"
        
        # 특정 요청사항 검증
        valid_requests = ["보고서 생성", "차트 분석", "비교 분석", "개선 방안", "예측 분석"]
        validated_requests = []
        for request in validated_result["specific_requests"]:
            if request in valid_requests:
                validated_requests.append(request)
        validated_result["specific_requests"] = validated_requests
        
        return validated_result
    
    def _get_fallback_analysis(self, query: str) -> Dict[str, Any]:
        """LLM 분석 실패 시 기본 분석 결과를 반환합니다."""
        return {
            "employee_name": None,
            "start_period": "202312",
            "end_period": "202403",
            "analysis_type": "종합분석",
            "specific_requests": [],
            "confidence": 0.3
        }
    
    def _set_defaults(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """기본값을 설정합니다."""
        # 직원명이 없으면 기본값 설정하지 않음 (오류 처리로 넘김)
        if not analysis_result.get("employee_name"):
            analysis_result["employee_name"] = None
        
        # 기간이 없으면 최근 4개월로 설정 (하드코딩된 데이터 기간)
        if not analysis_result.get("start_period"):
            analysis_result["start_period"] = "202312"  # 실제 데이터가 있는 기간
        if not analysis_result.get("end_period"):
            analysis_result["end_period"] = "202403"    # 실제 데이터가 있는 기간
        
        # 분석 유형이 없으면 종합분석으로 설정
        if not analysis_result.get("analysis_type"):
            analysis_result["analysis_type"] = "종합분석"
        
        # 특정 요청사항이 없으면 빈 배열로 설정
        if not analysis_result.get("specific_requests"):
            analysis_result["specific_requests"] = []
        
        # 신뢰도가 없으면 기본값 설정
        if "confidence" not in analysis_result:
            analysis_result["confidence"] = 0.8
        
        return analysis_result
    
    def get_enhanced_analysis(self, query: str) -> Dict[str, Any]:
        """LLM 기반 통합 분석을 수행합니다."""
        return self.analyze_query(query) 