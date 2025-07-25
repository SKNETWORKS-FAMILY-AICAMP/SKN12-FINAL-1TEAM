import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
import logging
from typing import Optional, Dict, Any, List

# .env 로드
env_file = Path(__file__).resolve().parents[3] / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    print(f"✅ docs_api.py - .env 로드됨: {env_file}")
else:
    print("⚠️ docs_api.py - .env 파일을 찾을 수 없습니다")

# OPENAI_API_KEY 확인
api_key = os.getenv("OPENAI_API_KEY")
print("docs_api.py - OPENAI_API_KEY:", api_key[:10] + "..." if api_key else "없음")

# Docs Agent imports
from ..services.docs_agent.classify_docs import DocumentClassifyAgent
from ..services.docs_agent.write_docs import DocumentDraftAgent

logger = logging.getLogger(__name__)
router = APIRouter()

# Docs Agent 인스턴스들 (지연 로딩)
doc_classifier = None
doc_writer = None

def get_doc_classifier():
    """Document Classifier 인스턴스 가져오기"""
    global doc_classifier
    if doc_classifier is None:
        try:
            logger.info("Document Classifier 인스턴스 생성 시작...")
            doc_classifier = DocumentClassifyAgent()
            logger.info("Document Classifier 인스턴스 생성 성공")
        except Exception as e:
            logger.error(f"Document Classifier 인스턴스 생성 실패: {e}")
            raise e
    return doc_classifier

def get_doc_writer():
    """Document Writer 인스턴스 가져오기"""
    global doc_writer
    if doc_writer is None:
        try:
            logger.info("Document Writer 인스턴스 생성 시작...")
            doc_writer = DocumentDraftAgent()
            logger.info("Document Writer 인스턴스 생성 성공")
        except Exception as e:
            logger.error(f"Document Writer 인스턴스 생성 실패: {e}")
            raise e
    return doc_writer

# Pydantic 모델 정의
class DocumentClassifyRequest(BaseModel):
    session_id: str
    text: str
    file_type: Optional[str] = "auto"

class DocumentWriteRequest(BaseModel):
    session_id: str
    document_type: str  # "영업방문보고서", "영업계획서", "실적분석보고서" 등
    content_data: Dict[str, Any]
    save_file: bool = False
    filename: Optional[str] = None

class DocumentResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    content: Optional[str] = None
    error: Optional[str] = None
    message: str

@router.get("/health")
async def docs_health_check():
    """Docs Agent 헬스 체크"""
    try:
        classifier = get_doc_classifier()
        writer = get_doc_writer()
        return {
            "status": "healthy",
            "agent": "Document Agent",
            "services": {
                "classifier": "running",
                "writer": "running"
            },
            "message": "Docs Agent가 정상 작동 중입니다."
        }
    except Exception as e:
        logger.error(f"Docs Agent 헬스 체크 오류: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Docs Agent에 문제가 있습니다."
        }

@router.get("/templates")
async def get_document_templates():
    """사용 가능한 문서 템플릿 목록 조회"""
    try:
        templates = [
            {
                "type": "영업방문보고서",
                "description": "고객 방문 결과 및 협의 내용 정리",
                "fields": ["방문일시", "고객명", "방문목적", "협의내용", "결과", "후속조치"]
            },
            {
                "type": "영업계획서",
                "description": "월간/분기별 영업 계획 수립",
                "fields": ["기간", "목표", "전략", "실행계획", "예상성과"]
            },
            {
                "type": "실적분석보고서",
                "description": "직원/부서별 실적 분석 및 평가",
                "fields": ["대상", "기간", "실적데이터", "분석결과", "개선방안"]
            },
            {
                "type": "협의내용요약",
                "description": "회의 및 협의 내용 요약 정리",
                "fields": ["회의일시", "참석자", "안건", "결정사항", "후속조치"]
            }
        ]
        
        return {
            "success": True,
            "templates": templates,
            "message": "문서 템플릿 목록을 가져왔습니다."
        }
    except Exception as e:
        logger.error(f"템플릿 조회 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "템플릿 조회 중 오류가 발생했습니다."
        }

@router.post("/classify", response_model=DocumentResponse)
async def classify_document(request: DocumentClassifyRequest):
    """문서 분류 API"""
    try:
        logger.info(f"문서 분류 요청: {len(request.text)} 글자")
        
        # 더미 분류 결과 생성
        if "방문" in request.text or "고객" in request.text:
            doc_type = "영업방문보고서"
            confidence = 0.95
        elif "계획" in request.text or "목표" in request.text:
            doc_type = "영업계획서"
            confidence = 0.88
        elif "실적" in request.text or "분석" in request.text:
            doc_type = "실적분석보고서"
            confidence = 0.92
        elif "회의" in request.text or "협의" in request.text:
            doc_type = "협의내용요약"
            confidence = 0.85
        else:
            doc_type = "기타문서"
            confidence = 0.70
        
        classification_result = {
            "document_type": doc_type,
            "confidence": confidence,
            "keywords": ["영업", "보고서", "분석", "계획"],
            "suggested_template": doc_type,
            "file_type": request.file_type,
            "text_length": len(request.text),
            "classification_details": {
                "primary_category": doc_type,
                "secondary_categories": ["업무문서", "공식보고서"],
                "urgency": "보통",
                "security_level": "내부"
            }
        }
        
        return DocumentResponse(
            success=True,
            result=classification_result,
            message=f"문서가 '{doc_type}'로 분류되었습니다 (신뢰도: {confidence:.1%})"
        )
        
    except Exception as e:
        logger.error(f"문서 분류 오류: {str(e)}")
        return DocumentResponse(
            success=False,
            error=str(e),
            message="문서 분류 중 오류가 발생했습니다."
        )

@router.post("/write", response_model=DocumentResponse)
async def write_document(request: DocumentWriteRequest):
    """문서 생성 API"""
    try:
        logger.info(f"문서 생성 요청: {request.document_type}")
        
        # 문서 타입별 더미 문서 생성
        if request.document_type == "영업방문보고서":
            content = f"""📋 영업방문 결과보고서

📅 방문 정보:
• 방문일시: {request.content_data.get('visit_date', '2024-01-27')}
• 고객명: {request.content_data.get('client_name', '서울의료센터')}
• 담당자: {request.content_data.get('contact_person', '김병원')}
• 방문목적: {request.content_data.get('purpose', '신제품 소개 및 계약 협의')}

🎯 협의 내용:
• 주요 안건: {request.content_data.get('agenda', '신제품 라인 도입 논의')}
• 고객 요구사항: {request.content_data.get('requirements', '품질 보증 및 가격 할인')}
• 제안 내용: {request.content_data.get('proposal', '10% 할인 및 품질보증서 제공')}

📊 협의 결과:
• 결정 사항: {request.content_data.get('decisions', '신제품 3종 도입 결정')}
• 계약 규모: {request.content_data.get('contract_amount', '월 300만원')}
• 계약 기간: {request.content_data.get('contract_period', '1년')}

📝 후속 조치:
• 즉시 조치: 계약서 작성 및 발송
• 단기 조치: 제품 샘플 제공 (1주일 내)
• 장기 조치: 정기 방문 스케줄 수립

✅ 방문 결과: 성공적인 계약 체결"""

        elif request.document_type == "영업계획서":
            content = f"""📋 영업계획서

📅 계획 기간: {request.content_data.get('period', '2024년 2분기')}
🎯 담당자: {request.content_data.get('manager', '최수아')}

📊 목표 설정:
• 매출 목표: {request.content_data.get('sales_target', '5,000만원')}
• 신규 고객: {request.content_data.get('new_clients', '10개사')}
• 방문 목표: {request.content_data.get('visit_target', '월 40회')}

🎯 주요 전략:
1. 기존 고객 심화 관리: {request.content_data.get('existing_strategy', 'VIP 서비스 확대')}
2. 신규 고객 확보: {request.content_data.get('new_strategy', '지역별 타겟 마케팅')}
3. 제품 포트폴리오 확장: {request.content_data.get('product_strategy', '신제품 3종 런칭')}

📈 실행 계획:
• 1개월차: 기존 고객 관계 강화 및 니즈 파악
• 2개월차: 신규 고객 발굴 및 초기 접촉
• 3개월차: 계약 체결 및 성과 평가

📊 예상 성과:
• 매출 증가율: 25%
• 고객 만족도: 90% 이상
• 시장 점유율: 15% 증가"""

        elif request.document_type == "실적분석보고서":
            content = f"""📊 실적분석 보고서

📅 분석 기간: {request.content_data.get('period', '2024년 1분기')}
👤 분석 대상: {request.content_data.get('target', '최수아 사원')}

📈 주요 성과:
• 총 매출: {request.content_data.get('total_sales', '4,200만원')}
• 목표 달성률: {request.content_data.get('achievement_rate', '140%')}
• 신규 고객: {request.content_data.get('new_customers', '12개사')}

📊 세부 분석:
• 월평균 실적: 1,400만원
• 고객별 평균 계약규모: 350만원
• 방문 대비 성약률: 65%

🎯 강점 분석:
• 신규 고객 발굴 능력 우수
• 기존 고객 관계 관리 탁월
• 목표 달성 의지 강함

📝 개선 방안:
• 대형 고객 확보 전략 필요
• 제품 지식 강화 교육
• 효율적 시간 관리 개선

✅ 종합 평가: A급 (우수)"""

        else:  # 협의내용요약
            content = f"""📋 협의내용 요약

📅 회의 정보:
• 일시: {request.content_data.get('meeting_date', '2024-01-27')}
• 참석자: {request.content_data.get('attendees', '김병원, 최수아, 박영업')}
• 장소: {request.content_data.get('location', '서울의료센터 회의실')}

🎯 주요 안건:
• 안건 1: {request.content_data.get('agenda1', '신제품 도입 검토')}
• 안건 2: {request.content_data.get('agenda2', '계약 조건 협의')}
• 안건 3: {request.content_data.get('agenda3', '납기 일정 확정')}

📋 논의 내용:
• 제품 품질: 품질보증서 요구사항 논의
• 가격 조건: 10% 할인 요청 및 승인
• 납기 일정: 주문 후 2주 내 납품 합의

✅ 결정 사항:
• 신제품 3종 도입 확정
• 월 계약 규모 300만원
• 다음 회의: 2024-02-03

📝 후속 조치:
• 계약서 작성: 최수아 (1주일 내)
• 제품 샘플 제공: 박영업 (3일 내)
• 품질보증서 발급: 김병원 (2주일 내)"""

        # 파일 저장 처리 (더미)
        message = f"{request.document_type} 생성이 완료되었습니다."
        if request.save_file:
            message += f" (파일 저장 요청: {request.filename or '자동생성명'})"
        
        return DocumentResponse(
            success=True,
            content=content,
            result={
                "document_type": request.document_type,
                "word_count": len(content),
                "generated_at": "2024-01-27T10:30:00",
                "filename": request.filename or f"{request.document_type}_20240127.docx"
            },
            message=message
        )
        
    except Exception as e:
        logger.error(f"문서 생성 오류: {str(e)}")
        return DocumentResponse(
            success=False,
            error=str(e),
            message="문서 생성 중 오류가 발생했습니다."
        )

@router.get("/search")
async def search_documents(query: str, doc_type: Optional[str] = None):
    """문서 검색 API"""
    try:
        logger.info(f"문서 검색 요청: {query}")
        
        # 더미 검색 결과
        search_results = [
            {
                "title": "영업방문보고서_서울의료센터_20240120.docx",
                "type": "영업방문보고서",
                "date": "2024-01-20",
                "content_preview": "서울의료센터 방문 결과, 신제품 도입 논의...",
                "relevance": 0.95
            },
            {
                "title": "월간영업계획서_2024년2월.docx",
                "type": "영업계획서",
                "date": "2024-01-25",
                "content_preview": "2월 영업 목표 5000만원 설정, 신규 고객...",
                "relevance": 0.88
            },
            {
                "title": "실적분석_최수아_1분기.docx",
                "type": "실적분석보고서",
                "date": "2024-01-22",
                "content_preview": "1분기 실적 4200만원 달성, 목표 대비 140%...",
                "relevance": 0.82
            }
        ]
        
        # 문서 타입 필터링
        if doc_type:
            search_results = [r for r in search_results if r["type"] == doc_type]
        
        return {
            "success": True,
            "query": query,
            "results": search_results,
            "total_count": len(search_results),
            "message": f"'{query}' 검색 결과 {len(search_results)}건을 찾았습니다."
        }
        
    except Exception as e:
        logger.error(f"문서 검색 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "문서 검색 중 오류가 발생했습니다."
        }