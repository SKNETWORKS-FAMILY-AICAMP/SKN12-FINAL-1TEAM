import os
import re
from openai import AsyncOpenAI
from pydantic import BaseModel

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class EmployeeAnalysisResponse(BaseModel):
    employee_name: str | None = None
    period: str | None = None
    result: str
    success: bool = True

async def extract_parameters_from_query(query: str) -> tuple[str | None, str | None]:
    system_prompt = (
        "사용자 질문에서 직원 이름과 기간을 추출해줘. "
        "기간은 'YYYYMM~YYYYMM' 형식으로, 없으면 'None'이라고 해줘. "
        "형식: 직원명: XXX, 기간: YYYYMM~YYYYMM"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.0
    )

    extracted_text = response.choices[0].message.content.strip()

    # 예: "직원명: 최수아, 기간: 202312~202403"
    name_match = re.search(r"직원명\s*[:：]\s*([^\s,]+)", extracted_text)
    period_match = re.search(r"기간\s*[:：]\s*([0-9]{6}~[0-9]{6})", extracted_text)

    employee_name = name_match.group(1) if name_match else None
    period = period_match.group(1) if period_match else None

    return employee_name, period

# 메인 함수
async def analyze_employee_query(query: str) -> EmployeeAnalysisResponse:
    try:
        employee_name, period = await extract_parameters_from_query(query)

        if not employee_name or not period:
            return EmployeeAnalysisResponse(
                result="직원명 또는 기간을 추출하지 못했습니다.",
                employee_name=employee_name,
                period=period,
                success=False
            )

        # ✅ 실제 분석 로직이 있다면 여기서 호출
        # 예시 결과만 반환
        analysis = (
            f"{employee_name} 직원의 {period} 기간 실적 분석입니다.\n"
            f"- 매출: 4억 5천만원\n"
            f"- 성과: 목표 대비 112%\n"
            f"- 개선점: 신규 고객 비율 낮음"
        )

        return EmployeeAnalysisResponse(
            employee_name=employee_name,
            period=period,
            result=analysis,
            success=True
        )

    except Exception as e:
        return EmployeeAnalysisResponse(
            result=f"분석 중 오류 발생: {str(e)}",
            success=False
        )
