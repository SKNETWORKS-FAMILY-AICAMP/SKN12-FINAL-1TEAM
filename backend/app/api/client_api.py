import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
import logging
from typing import Optional, Dict, Any

# .env 로드
env_file = Path(__file__).resolve().parents[3] / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    print(f"✅ client_api.py - .env 로드됨: {env_file}")
else:
    print("⚠️ client_api.py - .env 파일을 찾을 수 없습니다")

# OPENAI_API_KEY 확인
api_key = os.getenv("OPENAI_API_KEY")
print("client_api.py - OPENAI_API_KEY:", api_key[:10] + "..." if api_key else "없음")

# Client Agent import
from ..services.client_agent.client_analysis_agent import ClientAnalysisAgent

logger = logging.getLogger(__name__)
router = APIRouter()

# Client Agent 인스턴스 (지연 로딩)
client_agent = None

def get_client_agent():
    """Client Agent 인스턴스 가져오기"""
    global client_agent
    if client_agent is None:
        try:
            logger.info("Client Agent 인스턴스 생성 시작...")
            client_agent = ClientAnalysisAgent()
            logger.info("Client Agent 인스턴스 생성 성공")
        except Exception as e:
            logger.error(f"Client Agent 인스턴스 생성 실패: {e}")
            raise e
    return client_agent

# Pydantic 모델 정의
class ClientAnalysisRequest(BaseModel):
    client_name: Optional[str] = "서울의료센터"
    analysis_type: Optional[str] = "종합분석"
    save_report: bool = False

class ClientAnalysisResponse(BaseModel):
    success: bool
    client_info: Optional[Dict[str, Any]] = None
    analysis_result: Optional[Dict[str, Any]] = None
    report: Optional[str] = None
    error: Optional[str] = None
    message: str

@router.get("/health")
async def client_health_check():
    """Client Agent 헬스 체크"""
    try:
        agent = get_client_agent()
        return {
            "status": "healthy",
            "agent": "Client Analysis Agent",
            "message": "Client Agent가 정상 작동 중입니다."
        }
    except Exception as e:
        logger.error(f"Client Agent 헬스 체크 오류: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Client Agent에 문제가 있습니다."
        }

@router.get("/list")
async def get_client_list():
    """거래처 목록 조회"""
    try:
        logger.info("거래처 목록 조회 시작")
        
        # 더미 데이터 반환
        client_list = [
            {
                "client_name": "서울의료센터",
                "grade": "A급",
                "monthly_amount": 2500000,
                "contract_date": "2023-01-15",
                "contact_person": "김병원",
                "location": "서울시 강남구"
            },
            {
                "client_name": "부산종합병원",
                "grade": "B급",
                "monthly_amount": 1800000,
                "contract_date": "2023-03-20",
                "contact_person": "이원장",
                "location": "부산시 해운대구"
            },
            {
                "client_name": "대구약국체인",
                "grade": "A급",
                "monthly_amount": 3200000,
                "contract_date": "2022-11-10",
                "contact_person": "박약사",
                "location": "대구시 중구"
            }
        ]
        
        return {
            "success": True,
            "clients": client_list,
            "total_count": len(client_list),
            "message": "거래처 목록 조회가 완료되었습니다."
        }
        
    except Exception as e:
        logger.error(f"거래처 목록 조회 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "거래처 목록 조회 중 오류가 발생했습니다."
        }

@router.post("/analyze", response_model=ClientAnalysisResponse)
async def analyze_client(request: ClientAnalysisRequest):
    """고객/거래처 분석 API"""
    try:
        logger.info(f"고객 분석 요청: {request}")
        
        # 더미 데이터로 분석 결과 생성
        client_info = {
            "client_name": request.client_name,
            "business_type": "종합병원",
            "grade": "A급",
            "location": "서울시 강남구",
            "contact_person": "김병원",
            "phone": "02-1234-5678",
            "contract_date": "2023-01-15",
            "contract_period": "2년",
            "status": "활성"
        }
        
        analysis_result = {
            "monthly_average": 2500000,
            "yearly_total": 30000000,
            "growth_rate": 15.3,
            "payment_score": 95,
            "loyalty_score": 88,
            "risk_level": "낮음",
            "product_categories": [
                {"category": "처방의약품", "percentage": 60, "amount": 18000000},
                {"category": "일반의약품", "percentage": 25, "amount": 7500000},
                {"category": "의료기기", "percentage": 15, "amount": 4500000}
            ],
            "recent_orders": [
                {"date": "2024-01-20", "amount": 2800000, "products": "혈압약, 당뇨약"},
                {"date": "2024-01-15", "amount": 2200000, "products": "감기약, 소염제"},
                {"date": "2024-01-10", "amount": 2600000, "products": "항생제, 진통제"}
            ],
            "recommendations": [
                "신규 제품 라인 제안 가능",
                "계약 갱신 시 할인 혜택 제공",
                "정기 방문 스케줄 증가 권장",
                "VIP 고객 서비스 적용 검토"
            ]
        }
        
        report = f"""🏥 {request.client_name} 거래처 분석 보고서

🔍 기본 정보:
• 거래처명: {request.client_name}
• 업종: 종합병원
• 등급: A급 (우수 거래처)
• 소재지: 서울시 강남구
• 담당자: 김병원
• 계약일: 2023-01-15

📊 매출 분석:
• 월 평균 매출: 2,500,000원
• 연간 총 매출: 30,000,000원
• 성장률: 15.3% (전년 대비)
• 결제 신용도: 95점 (우수)
• 고객 충성도: 88점 (높음)

🎯 제품별 매출 구성:
• 처방의약품: 60% (18,000,000원)
• 일반의약품: 25% (7,500,000원)
• 의료기기: 15% (4,500,000원)

📈 최근 주문 현황:
• 2024-01-20: 2,800,000원 (혈압약, 당뇨약)
• 2024-01-15: 2,200,000원 (감기약, 소염제)
• 2024-01-10: 2,600,000원 (항생제, 진통제)

💡 분석 결과:
{request.client_name}는 안정적인 성장세를 보이는 우수한 A급 거래처입니다. 
결제 신용도가 높고 지속적인 주문량 증가 추세를 보이고 있어 장기적 파트너십이 기대됩니다.

📝 영업 전략 권장사항:
1. 신규 제품 라인 제안 가능
2. 계약 갱신 시 할인 혜택 제공
3. 정기 방문 스케줄 증가 권장
4. VIP 고객 서비스 적용 검토

🎖️ 위험도 평가: 낮음 (신용도 우수, 결제 지연 없음)

✅ 분석 완료: {request.client_name}는 지속적인 관계 발전이 가능한 핵심 거래처입니다."""

        # 보고서 저장 (요청 시)
        message = "고객 분석이 완료되었습니다."
        if request.save_report:
            # 실제 파일 저장은 구현하지 않음 (파일 경로 문제)
            message += " (보고서 저장 요청됨)"
        
        return ClientAnalysisResponse(
            success=True,
            client_info=client_info,
            analysis_result=analysis_result,
            report=report,
            message=message
        )
        
    except Exception as e:
        logger.error(f"고객 분석 오류: {str(e)}")
        return ClientAnalysisResponse(
            success=False,
            error=str(e),
            message="고객 분석 중 오류가 발생했습니다."
        )

@router.get("/summary/{client_name}")
async def get_client_summary(client_name: str):
    """특정 거래처 요약 정보 조회"""
    try:
        logger.info(f"거래처 요약 조회: {client_name}")
        
        # 더미 데이터 반환
        summary_data = {
            "client_name": client_name,
            "grade": "A급",
            "monthly_average": 2500000,
            "yearly_total": 30000000,
            "growth_rate": 15.3,
            "last_order_date": "2024-01-20",
            "payment_status": "정상",
            "contract_status": "활성"
        }
        
        return {
            "success": True,
            "summary": summary_data,
            "message": f"{client_name} 요약 조회가 완료되었습니다."
        }
        
    except Exception as e:
        logger.error(f"거래처 요약 조회 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "거래처 요약 조회 중 오류가 발생했습니다."
        }