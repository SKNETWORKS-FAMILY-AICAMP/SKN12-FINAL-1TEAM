from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.database import get_db
from app.models import Employee

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/employee-performance", tags=["Employee Performance"])

# Request/Response Models
class PerformanceRequest(BaseModel):
    employee_name: str
    start_period: str  # YYYYMM format
    end_period: str    # YYYYMM format

class PerformanceResponse(BaseModel):
    employee_name: str
    period: str
    total_performance: int
    monthly_breakdown: List[Dict[str, Any]]
    product_breakdown: List[Dict[str, Any]]
    client_breakdown: List[Dict[str, Any]]

class TargetComparisonResponse(BaseModel):
    total_performance: int
    total_target: int
    achievement_rate: float
    gap_amount: int
    evaluation: str
    grade: str

class TrendAnalysisResponse(BaseModel):
    trend: str
    trend_strength: str
    analysis: str
    monthly_amounts: Optional[List[int]] = None

@router.get("/employees", response_model=List[str])
async def get_available_employees(db: Session = Depends(get_db)):
    """사용 가능한 직원 목록을 반환합니다."""
    try:
        # employees 테이블에서 직원명 조회
        result = db.execute(
            text("SELECT DISTINCT name FROM employees WHERE is_active = true AND is_deleted = false")
        )
        employees = [row[0] for row in result.fetchall()]
        
        if not employees:
            # 실적 테이블에서 직접 조회
            result = db.execute(
                text("SELECT DISTINCT 담당자 FROM sales_performance WHERE 담당자 IS NOT NULL")
            )
            employees = [row[0] for row in result.fetchall()]
        
        return employees
    except Exception as e:
        logger.error(f"직원 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/performance", response_model=PerformanceResponse)
async def get_employee_performance(
    request: PerformanceRequest,
    db: Session = Depends(get_db)
):
    """직원의 실적 데이터를 조회합니다."""
    try:
        # 기간에 해당하는 실적 데이터 조회
        query = text("""
            SELECT 
                sp.담당자,
                sp.품목,
                sp.거래처,
                sp.년월,
                sp.금액
            FROM sales_performance sp
            WHERE sp.담당자 = :employee_name
                AND sp.년월 >= :start_period
                AND sp.년월 <= :end_period
            ORDER BY sp.년월, sp.품목
        """)
        
        result = db.execute(query, {
            "employee_name": request.employee_name,
            "start_period": int(request.start_period),
            "end_period": int(request.end_period)
        })
        
        rows = result.fetchall()
        
        # 데이터 집계
        total_performance = 0
        monthly_data = {}
        product_data = {}
        client_data = {}
        
        for row in rows:
            담당자, 품목, 거래처, 년월, 금액 = row
            
            # 월별 집계
            month_str = str(년월)
            if month_str not in monthly_data:
                monthly_data[month_str] = 0
            monthly_data[month_str] += 금액
            
            # 제품별 집계
            if 품목 not in product_data:
                product_data[품목] = 0
            product_data[품목] += 금액
            
            # 거래처별 집계
            if 거래처 not in client_data:
                client_data[거래처] = 0
            client_data[거래처] += 금액
            
            total_performance += 금액
        
        # Response 형식으로 변환
        monthly_breakdown = [
            {"month": month, "amount": amount}
            for month, amount in sorted(monthly_data.items())
        ]
        
        product_breakdown = [
            {"name": name, "amount": amount}
            for name, amount in sorted(product_data.items(), key=lambda x: x[1], reverse=True)
        ]
        
        client_breakdown = [
            {"name": name, "amount": amount}
            for name, amount in sorted(client_data.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return PerformanceResponse(
            employee_name=request.employee_name,
            period=f"{request.start_period}~{request.end_period}",
            total_performance=total_performance,
            monthly_breakdown=monthly_breakdown,
            product_breakdown=product_breakdown,
            client_breakdown=client_breakdown
        )
        
    except Exception as e:
        logger.error(f"실적 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/target-comparison", response_model=TargetComparisonResponse)
async def get_target_comparison(
    request: PerformanceRequest,
    db: Session = Depends(get_db)
):
    """목표 대비 실적을 비교합니다."""
    try:
        # 실적 조회
        perf_query = text("""
            SELECT SUM(금액) as total_performance
            FROM sales_performance
            WHERE 담당자 = :employee_name
                AND 년월 >= :start_period
                AND 년월 <= :end_period
        """)
        
        perf_result = db.execute(perf_query, {
            "employee_name": request.employee_name,
            "start_period": int(request.start_period),
            "end_period": int(request.end_period)
        })
        
        total_performance = perf_result.scalar() or 0
        
        # 목표 조회
        target_query = text("""
            SELECT SUM(목표) as total_target
            FROM monthly_target
            WHERE 담당자 = :employee_name
                AND 년월 >= :start_period
                AND 년월 <= :end_period
        """)
        
        target_result = db.execute(target_query, {
            "employee_name": request.employee_name,
            "start_period": int(request.start_period),
            "end_period": int(request.end_period)
        })
        
        total_target = target_result.scalar() or 0
        
        # 목표가 없으면 실적의 80%를 목표로 가정
        if total_target == 0:
            total_target = int(total_performance * 0.8)
        
        # 달성률 계산
        achievement_rate = (total_performance / total_target * 100) if total_target > 0 else 0
        gap_amount = total_performance - total_target
        
        # 평가 등급
        if achievement_rate >= 120:
            evaluation = "목표 초과 달성"
            grade = "S"
        elif achievement_rate >= 100:
            evaluation = "목표 달성"
            grade = "A"
        elif achievement_rate >= 80:
            evaluation = "목표 근접"
            grade = "B"
        elif achievement_rate >= 60:
            evaluation = "목표 미달"
            grade = "C"
        else:
            evaluation = "목표 크게 미달"
            grade = "D"
        
        return TargetComparisonResponse(
            total_performance=int(total_performance),
            total_target=int(total_target),
            achievement_rate=round(achievement_rate, 2),
            gap_amount=int(gap_amount),
            evaluation=evaluation,
            grade=grade
        )
        
    except Exception as e:
        logger.error(f"목표 비교 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trend-analysis", response_model=TrendAnalysisResponse)
async def analyze_trend(
    request: PerformanceRequest,
    db: Session = Depends(get_db)
):
    """실적 트렌드를 분석합니다."""
    try:
        # 월별 실적 조회
        query = text("""
            SELECT 년월, SUM(금액) as monthly_total
            FROM sales_performance
            WHERE 담당자 = :employee_name
                AND 년월 >= :start_period
                AND 년월 <= :end_period
            GROUP BY 년월
            ORDER BY 년월
        """)
        
        result = db.execute(query, {
            "employee_name": request.employee_name,
            "start_period": int(request.start_period),
            "end_period": int(request.end_period)
        })
        
        monthly_amounts = []
        for row in result.fetchall():
            monthly_amounts.append(int(row[1]))
        
        if len(monthly_amounts) < 2:
            return TrendAnalysisResponse(
                trend="데이터 부족",
                trend_strength="없음",
                analysis="트렌드 분석을 위해서는 최소 2개월 이상의 데이터가 필요합니다."
            )
        
        # 트렌드 분석
        if len(monthly_amounts) >= 3:
            recent_avg = sum(monthly_amounts[-2:]) / 2
            early_avg = sum(monthly_amounts[:2]) / 2
            
            if recent_avg > early_avg * 1.1:
                trend = "상승"
                strength = "강함" if recent_avg > early_avg * 1.2 else "보통"
            elif recent_avg < early_avg * 0.9:
                trend = "하락"
                strength = "강함" if recent_avg < early_avg * 0.8 else "약함"
            else:
                trend = "안정"
                strength = "보통"
        else:
            if monthly_amounts[-1] > monthly_amounts[0]:
                trend = "상승"
                strength = "보통"
            elif monthly_amounts[-1] < monthly_amounts[0]:
                trend = "하락"
                strength = "보통"
            else:
                trend = "안정"
                strength = "보통"
        
        analysis = f"분석 기간 동안 실적은 {trend} 추세를 보이고 있습니다."
        
        return TrendAnalysisResponse(
            trend=trend,
            trend_strength=strength,
            analysis=analysis,
            monthly_amounts=monthly_amounts
        )
        
    except Exception as e:
        logger.error(f"트렌드 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-summary")
async def get_performance_summary(
    employee_name: str = Query(..., description="직원명"),
    start_period: str = Query(..., description="시작 기간 (YYYYMM)"),
    end_period: str = Query(..., description="종료 기간 (YYYYMM)"),
    db: Session = Depends(get_db)
):
    """직원의 전체 실적 요약을 반환합니다."""
    try:
        # 실적 데이터 조회
        performance = await get_employee_performance(
            PerformanceRequest(
                employee_name=employee_name,
                start_period=start_period,
                end_period=end_period
            ),
            db
        )
        
        # 목표 비교 조회
        target_comparison = await get_target_comparison(
            PerformanceRequest(
                employee_name=employee_name,
                start_period=start_period,
                end_period=end_period
            ),
            db
        )
        
        # 트렌드 분석
        trend = await analyze_trend(
            PerformanceRequest(
                employee_name=employee_name,
                start_period=start_period,
                end_period=end_period
            ),
            db
        )
        
        return {
            "performance": performance,
            "target_comparison": target_comparison,
            "trend_analysis": trend
        }
        
    except Exception as e:
        logger.error(f"실적 요약 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))