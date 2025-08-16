#!/usr/bin/env python3

import os
import json
from typing import Dict, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일을 backend/app 디렉토리에서 로드
current_dir = Path(__file__).resolve().parent
backend_app_dir = current_dir.parent.parent
env_path = backend_app_dir / '.env'
load_dotenv(env_path)

class TextExtractor:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=api_key)

    def extract_company_and_period(self, user_text: str) -> Dict[str, Optional[str]]:
        """
        사용자 텍스트에서 병원명과 분석기간을 추출합니다.
        
        Args:
            user_text: 사용자가 입력한 텍스트
            
        Returns:
            dict: COMPANY_NAME, START_MONTH, END_MONTH를 포함한 딕셔너리
        """
        
        prompt = f"""
사용자가 입력한 텍스트에서 병원명과 분석기간을 추출해주세요.

입력 텍스트: "{user_text}"

다음 규칙에 따라 정보를 추출하고 JSON 형태로 반환해주세요:

1. COMPANY_NAME: 병원명을 추출합니다.
   - "의원", "병원", "클리닉" 등이 포함된 이름을 찾아주세요
   - 정확한 이름이 언급되지 않으면 null로 설정

2. START_MONTH, END_MONTH: 분석기간을 YYYYMM 형태로 추출합니다.
   - "24년 1분기" → START_MONTH: "202401", END_MONTH: "202403"
   - "2024년 1분기" → START_MONTH: "202401", END_MONTH: "202403"
   - "23년 2분기" → START_MONTH: "202304", END_MONTH: "202306"
   - "2023년 상반기" → START_MONTH: "202301", END_MONTH: "202306"
   - "2023년 하반기" → START_MONTH: "202307", END_MONTH: "202312"
   - "2024년 1월~3월" → START_MONTH: "202401", END_MONTH: "202403"
   - "작년" → 2023년 전체 → START_MONTH: "202301", END_MONTH: "202312"
   - "올해" → 2024년 전체 → START_MONTH: "202401", END_MONTH: "202412"
   - 구체적인 기간이 없으면 null로 설정

3. 분기 매핑:
   - 1분기: 1월~3월 (01~03)
   - 2분기: 4월~6월 (04~06)
   - 3분기: 7월~9월 (07~09)
   - 4분기: 10월~12월 (10~12)

반드시 다음 JSON 형태로만 응답해주세요:
{{
    "COMPANY_NAME": "추출된 병원명 또는 null",
    "START_MONTH": "YYYYMM 형태 또는 null",
    "END_MONTH": "YYYYMM 형태 또는 null"
}}

다른 설명은 추가하지 말고 JSON만 반환해주세요.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 텍스트에서 병원명과 기간 정보를 정확히 추출하는 전문가입니다. 반드시 JSON 형태로만 응답해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON 코드블록 제거 (```json ... ``` 형태)
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
            
            # JSON 파싱
            try:
                result = json.loads(result_text)
                
                # 결과 검증 및 정리
                validated_result = {
                    "COMPANY_NAME": result.get("COMPANY_NAME"),
                    "START_MONTH": result.get("START_MONTH"),
                    "END_MONTH": result.get("END_MONTH")
                }
                
                # null 문자열을 None으로 변환, 날짜는 정수로 변환
                for key, value in validated_result.items():
                    if value == "null" or value == "":
                        validated_result[key] = None
                    elif key in ["START_MONTH", "END_MONTH"] and value is not None:
                        try:
                            validated_result[key] = int(value)
                        except (ValueError, TypeError):
                            validated_result[key] = None
                
                return validated_result
                
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"OpenAI 응답: {result_text}")
                return {"COMPANY_NAME": None, "START_MONTH": None, "END_MONTH": None}
                
        except Exception as e:
            print(f"OpenAI API 호출 오류: {e}")
            return {"COMPANY_NAME": None, "START_MONTH": None, "END_MONTH": None}