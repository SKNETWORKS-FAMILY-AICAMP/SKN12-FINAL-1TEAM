# Client Agent Module
from .client_agent import ClientAgent, run_full_pipeline
import re

# 인스턴스 생성
agent = ClientAgent()

# router.py와의 호환성을 위한 wrapper 함수
async def run(query: str, session_id: str = None):
    """Router에서 호출하기 위한 wrapper 함수"""
    try:
        # query에서 거래처명 추출 (예: "미라클신경과 거래처 분석")
        company_name = None
        
        # 일반적인 패턴으로 거래처명 추출
        patterns = [
            r'([가-힣]+(?:의원|병원|신경과|내과|외과|정형외과|피부과|이비인후과|안과|치과|한의원|약국|센터|클리닉))',
            r'([가-힣]+)\s*(?:거래처|분석|조회|확인)',
            r'거래처\s*([가-힣]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                company_name = match.group(1)
                break
        
        if not company_name:
            # 쿼리의 첫 단어를 거래처명으로 추정
            words = query.split()
            if words:
                company_name = words[0]
        
        # 기간 추출 (선택적)
        start_month = None
        end_month = None
        
        # 월 패턴 추출 (예: "202401", "2024년 1월")
        month_pattern = r'(\d{6})'
        months = re.findall(month_pattern, query)
        if len(months) >= 2:
            start_month = int(months[0])
            end_month = int(months[1])
        elif len(months) == 1:
            start_month = int(months[0])
            end_month = int(months[0])
        
        # run_full_pipeline 호출
        result = await run_full_pipeline(
            agent=agent,
            company_name=company_name,
            start_month=start_month,
            end_month=end_month
        )
        
        # 결과 포맷팅
        if result.get("final_report"):
            return {
                "success": True,
                "response": result["final_report"],
                "data": {
                    "company_name": company_name,
                    "grade_result": result.get("grade_result"),
                    "period": f"{start_month or '전체'} ~ {end_month or '전체'}"
                }
            }
        else:
            return {
                "success": False,
                "error": "분석 결과를 생성할 수 없습니다.",
                "response": f"{company_name} 거래처 데이터를 찾을 수 없거나 분석에 실패했습니다."
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": f"거래처 분석 중 오류가 발생했습니다: {str(e)}"
        }

__all__ = ['ClientAgent', 'run_full_pipeline', 'agent', 'run']