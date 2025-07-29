import os
import re
from openai import AsyncOpenAI
from pydantic import BaseModel

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ClientAnalysisResponse(BaseModel):
    client_name: str | None = None
    analysis_type: str | None = None
    result: str
    success: bool = True

async def extract_parameters_from_query(query: str) -> tuple[str | None, str | None]:
    system_prompt = (
        "아래 질문에서 거래처 이름과 분석 유형을 추출해줘. "
        "분석 유형은 예: '종합분석', '매출추이', '성장성' 등. "
        "형식: 거래처명: XXX, 분석유형: XXX"
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

    content = response.choices[0].message.content.strip()
    # 예: 거래처명: 서울의료센터, 분석유형: 종합분석
    name_match = re.search(r"거래처명\s*[:：]\s*([^\s,]+)", content)
    type_match = re.search(r"분석유형\s*[:：]\s*([^\s,]+)", content)

    client_name = name_match.group(1) if name_match else None
    analysis_type = type_match.group(1) if type_match else None

    return client_name, analysis_type

async def analyze_client_query(query: str) -> ClientAnalysisResponse:
    try:
        client_name, analysis_type = await extract_parameters_from_query(query)

        if not client_name or not analysis_type:
            return ClientAnalysisResponse(
                result="거래처명 또는 분석유형을 추출하지 못했습니다.",
                client_name=client_name,
                analysis_type=analysis_type,
                success=False
            )

        # TODO: 실제 분석 로직 구현 (DB 조회 등)
        dummy_result = (
            f"{client_name}에 대한 {analysis_type} 결과입니다.\n"
            f"- 최근 6개월 매출 증가율: +17%\n"
            f"- 방문빈도 감소\n"
            f"- 주요 제품 매출 비중 편중"
        )

        return ClientAnalysisResponse(
            client_name=client_name,
            analysis_type=analysis_type,
            result=dummy_result,
            success=True
        )

    except Exception as e:
        return ClientAnalysisResponse(
            result=f"분석 중 오류 발생: {str(e)}",
            success=False
        )
