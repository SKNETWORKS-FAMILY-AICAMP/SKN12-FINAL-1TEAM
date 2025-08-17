"""
거래처(고객) 관련 라우터
거래처별 월간 성과 정보 조회 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from pydantic import BaseModel

from app.services.utils.db import get_db
from app.services.core.customer_performance_service import CustomerPerformanceService
from app.routers.user_router import get_current_user
from app.models.customers import Customer
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class CustomerInfo(BaseModel):
    """거래처 정보 스키마"""
    customer_id: int
    customer_name: str
    customer_grade: Optional[str] = None
    address: Optional[str] = None
    doctor_name: Optional[str] = None
    contact_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

@router.get("/{customer_id}/performance")
def get_customer_performance(
    customer_id: int,
    start_month: str = Query(..., description="시작 월 (YYYYMM 형식)", regex="^\\d{6}$"),
    end_month: str = Query(..., description="종료 월 (YYYYMM 형식)", regex="^\\d{6}$"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    특정 거래처의 기간별 성과 정보 조회
    
    Args:
        customer_id: 거래처 ID
        start_month: 조회 시작 월 (YYYYMM 형식, 예: 202401)
        end_month: 조회 종료 월 (YYYYMM 형식, 예: 202412)
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        Dict: 거래처 정보 및 월별 성과 데이터
        {
            "customer_id": 1,
            "customer_name": "서울병원",
            "period": {
                "start": "202401",
                "end": "202412"
            },
            "monthly_data": [
                {
                    "month": "202401",
                    "매출": 2500000,
                    "사용예산": 400000,
                    "총환자수": 2400
                },
                ...
            ],
            "summary": {
                "total_sales": 30000000,
                "total_budget": 4800000,
                "total_patients": 28800,
                "average_monthly_sales": 2500000,
                "average_monthly_budget": 400000,
                "average_monthly_patients": 2400
            }
        }
    """
    try:
        # 날짜 형식 검증
        try:
            start_date = datetime.strptime(start_month, "%Y%m")
            end_date = datetime.strptime(end_month, "%Y%m")
            
            if start_date > end_date:
                raise HTTPException(
                    status_code=400, 
                    detail="시작 월이 종료 월보다 늦을 수 없습니다."
                )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="잘못된 날짜 형식입니다. YYYYMM 형식을 사용하세요."
            )
        
        # 서비스 클래스를 통해 데이터 조회
        service = CustomerPerformanceService(db)
        
        # 거래처 정보 조회
        customer_info = service.get_customer_info(customer_id)
        if not customer_info:
            raise HTTPException(
                status_code=404,
                detail=f"거래처 ID {customer_id}를 찾을 수 없습니다."
            )
        
        # 월별 성과 데이터 조회
        monthly_data = service.get_monthly_performance(
            customer_id, 
            start_month, 
            end_month
        )
        
        # 요약 통계 계산
        summary = service.calculate_summary(monthly_data)
        
        # 응답 구성
        result = {
            "customer_id": customer_id,
            "customer_name": customer_info["customer_name"],
            "customer_grade": customer_info.get("customer_grade"),
            "period": {
                "start": start_month,
                "end": end_month
            },
            "monthly_data": monthly_data,
            "summary": summary
        }
        
        logger.info(
            f"거래처 성과 조회 완료: customer_id={customer_id}, "
            f"period={start_month}~{end_month}, "
            f"data_count={len(monthly_data)}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"거래처 성과 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"거래처 성과 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/performance")
def get_multiple_customers_performance(
    customer_ids: str = Query(..., description="거래처 ID 목록 (쉼표 구분)", example="1,2,3"),
    start_month: str = Query(..., description="시작 월 (YYYYMM 형식)", regex="^\\d{6}$"),
    end_month: str = Query(..., description="종료 월 (YYYYMM 형식)", regex="^\\d{6}$"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    여러 거래처의 기간별 성과 정보 조회
    
    Args:
        customer_ids: 거래처 ID 목록 (쉼표로 구분)
        start_month: 조회 시작 월 (YYYYMM 형식)
        end_month: 조회 종료 월 (YYYYMM 형식)
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        List[Dict]: 거래처별 성과 정보 목록
    """
    try:
        # 거래처 ID 파싱
        try:
            customer_id_list = [int(id.strip()) for id in customer_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="잘못된 거래처 ID 형식입니다. 숫자를 쉼표로 구분하여 입력하세요."
            )
        
        # 날짜 형식 검증
        try:
            start_date = datetime.strptime(start_month, "%Y%m")
            end_date = datetime.strptime(end_month, "%Y%m")
            
            if start_date > end_date:
                raise HTTPException(
                    status_code=400,
                    detail="시작 월이 종료 월보다 늦을 수 없습니다."
                )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="잘못된 날짜 형식입니다. YYYYMM 형식을 사용하세요."
            )
        
        # 서비스 클래스를 통해 데이터 조회
        service = CustomerPerformanceService(db)
        
        results = []
        for customer_id in customer_id_list:
            try:
                # 거래처 정보 조회
                customer_info = service.get_customer_info(customer_id)
                if not customer_info:
                    logger.warning(f"거래처 ID {customer_id}를 찾을 수 없습니다.")
                    continue
                
                # 월별 성과 데이터 조회
                monthly_data = service.get_monthly_performance(
                    customer_id,
                    start_month,
                    end_month
                )
                
                # 요약 통계 계산
                summary = service.calculate_summary(monthly_data)
                
                # 결과 추가
                results.append({
                    "customer_id": customer_id,
                    "customer_name": customer_info["customer_name"],
                    "customer_grade": customer_info.get("customer_grade"),
                    "period": {
                        "start": start_month,
                        "end": end_month
                    },
                    "monthly_data": monthly_data,
                    "summary": summary
                })
            except Exception as e:
                logger.error(f"거래처 ID {customer_id} 처리 중 오류: {e}")
        
        logger.info(
            f"다중 거래처 성과 조회 완료: customer_count={len(results)}, "
            f"period={start_month}~{end_month}"
        )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"다중 거래처 성과 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"다중 거래처 성과 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{customer_id}/performance/comparison")
def compare_customer_performance(
    customer_id: int,
    period1_start: str = Query(..., description="첫 번째 기간 시작 월 (YYYYMM)", regex="^\\d{6}$"),
    period1_end: str = Query(..., description="첫 번째 기간 종료 월 (YYYYMM)", regex="^\\d{6}$"),
    period2_start: str = Query(..., description="두 번째 기간 시작 월 (YYYYMM)", regex="^\\d{6}$"),
    period2_end: str = Query(..., description="두 번째 기간 종료 월 (YYYYMM)", regex="^\\d{6}$"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    특정 거래처의 두 기간 성과 비교
    
    Args:
        customer_id: 거래처 ID
        period1_start: 첫 번째 기간 시작 월
        period1_end: 첫 번째 기간 종료 월
        period2_start: 두 번째 기간 시작 월
        period2_end: 두 번째 기간 종료 월
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        Dict: 두 기간의 성과 비교 데이터
    """
    try:
        # 서비스 클래스를 통해 데이터 조회
        service = CustomerPerformanceService(db)
        
        # 거래처 정보 조회
        customer_info = service.get_customer_info(customer_id)
        if not customer_info:
            raise HTTPException(
                status_code=404,
                detail=f"거래처 ID {customer_id}를 찾을 수 없습니다."
            )
        
        # 첫 번째 기간 데이터
        period1_data = service.get_monthly_performance(
            customer_id,
            period1_start,
            period1_end
        )
        period1_summary = service.calculate_summary(period1_data)
        
        # 두 번째 기간 데이터
        period2_data = service.get_monthly_performance(
            customer_id,
            period2_start,
            period2_end
        )
        period2_summary = service.calculate_summary(period2_data)
        
        # 비교 분석
        comparison = service.compare_periods(period1_summary, period2_summary)
        
        result = {
            "customer_id": customer_id,
            "customer_name": customer_info["customer_name"],
            "period1": {
                "range": f"{period1_start}~{period1_end}",
                "summary": period1_summary
            },
            "period2": {
                "range": f"{period2_start}~{period2_end}",
                "summary": period2_summary
            },
            "comparison": comparison
        }
        
        logger.info(
            f"거래처 성과 비교 완료: customer_id={customer_id}, "
            f"period1={period1_start}~{period1_end}, "
            f"period2={period2_start}~{period2_end}"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"거래처 성과 비교 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"거래처 성과 비교 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/", response_model=List[CustomerInfo])
def get_all_customers(
    skip: int = Query(0, description="건너뛸 항목 수"),
    limit: int = Query(100, description="조회할 최대 항목 수"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[CustomerInfo]:
    """
    모든 거래처 정보 목록 조회
    
    Args:
        skip: 건너뛸 항목 수 (페이지네이션용)
        limit: 조회할 최대 항목 수
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        List[CustomerInfo]: 거래처 정보 목록
    """
    try:
        # 삭제되지 않은 거래처만 조회
        customers = db.query(Customer).filter(
            Customer.is_deleted == False
        ).offset(skip).limit(limit).all()
        
        logger.info(f"거래처 목록 조회 완료: {len(customers)}개")
        
        return [CustomerInfo.from_orm(customer) for customer in customers]
        
    except Exception as e:
        logger.error(f"거래처 목록 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"거래처 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/search", response_model=Dict[str, Any])
def search_customer_by_name(
    name: str = Query(..., description="검색할 거래처명"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    거래처명으로 거래처 ID 조회
    
    Args:
        name: 검색할 거래처명 (부분 일치 검색)
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        Dict: 검색 결과
        {
            "search_term": "검색어",
            "count": 1,
            "results": [
                {
                    "customer_id": 1,
                    "customer_name": "서울병원",
                    "customer_grade": "A",
                    "address": "서울시 강남구"
                }
            ]
        }
    """
    try:
        # 부분 일치 검색 (대소문자 구분 없음)
        customers = db.query(Customer).filter(
            Customer.customer_name.ilike(f"%{name}%"),
            Customer.is_deleted == False
        ).all()
        
        if not customers:
            logger.info(f"거래처명 '{name}' 검색 결과 없음")
            return {
                "search_term": name,
                "count": 0,
                "results": []
            }
        
        results = []
        for customer in customers:
            results.append({
                "customer_id": customer.customer_id,
                "customer_name": customer.customer_name,
                "customer_grade": customer.customer_grade,
                "address": customer.address
            })
        
        logger.info(f"거래처명 '{name}' 검색 완료: {len(results)}개 발견")
        
        return {
            "search_term": name,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"거래처명 검색 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"거래처명 검색 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{customer_id}", response_model=CustomerInfo)
def get_customer_detail(
    customer_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> CustomerInfo:
    """
    특정 거래처의 상세 정보 조회
    
    Args:
        customer_id: 거래처 ID
        db: 데이터베이스 세션
        user: 현재 인증된 사용자
        
    Returns:
        CustomerInfo: 거래처 상세 정보
    """
    try:
        customer = db.query(Customer).filter(
            Customer.customer_id == customer_id,
            Customer.is_deleted == False
        ).first()
        
        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"거래처 ID {customer_id}를 찾을 수 없습니다."
            )
        
        logger.info(f"거래처 상세 정보 조회 완료: ID={customer_id}")
        
        return CustomerInfo.from_orm(customer)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"거래처 상세 정보 조회 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"거래처 상세 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )