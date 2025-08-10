"""
지점별 목표 및 실적 스키마
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, date

class BranchTargetBase(BaseModel):
    """지점 목표 기본 스키마"""
    branch_id: int = Field(..., description="지점 ID")
    employee_info_id: int = Field(..., description="직원 인사정보 ID")
    target_year: int = Field(..., description="목표 년도", ge=2000, le=2100)
    target_month: int = Field(..., description="목표 월", ge=1, le=12)
    target_amount: float = Field(0.0, description="목표 금액", ge=0)
    actual_amount: float = Field(0.0, description="실적 금액", ge=0)
    notes: Optional[str] = Field(None, description="비고")
    
    @validator('target_year')
    def validate_year(cls, v):
        if v < 2000 or v > 2100:
            raise ValueError('년도는 2000-2100 사이여야 합니다')
        return v
    
    @validator('target_month')
    def validate_month(cls, v):
        if v < 1 or v > 12:
            raise ValueError('월은 1-12 사이여야 합니다')
        return v

class BranchTargetCreate(BranchTargetBase):
    """지점 목표 생성 스키마"""
    pass

class BranchTargetUpdate(BaseModel):
    """지점 목표 수정 스키마"""
    target_amount: Optional[float] = Field(None, description="목표 금액", ge=0)
    actual_amount: Optional[float] = Field(None, description="실적 금액", ge=0)
    notes: Optional[str] = Field(None, description="비고")

class BranchTarget(BranchTargetBase):
    """지점 목표 응답 스키마"""
    target_id: int = Field(..., description="목표 ID")
    target_date: date = Field(..., description="목표 년월")
    achievement_rate: float = Field(0.0, description="달성률 (%)")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    
    class Config:
        from_attributes = True

class BranchTargetWithDetails(BranchTarget):
    """상세 정보 포함 지점 목표 스키마"""
    branch_name: Optional[str] = Field(None, description="지점명")
    employee_name: Optional[str] = Field(None, description="직원명")
    employee_number: Optional[str] = Field(None, description="사번")
    headquarters: Optional[str] = Field(None, description="본부")
    department: Optional[str] = Field(None, description="부서")

class BranchTargetSummary(BaseModel):
    """지점 목표 요약 스키마"""
    branch_id: int = Field(..., description="지점 ID")
    branch_name: str = Field(..., description="지점명")
    target_year: int = Field(..., description="년도")
    target_month: int = Field(..., description="월")
    total_target_amount: float = Field(..., description="총 목표 금액")
    total_actual_amount: float = Field(..., description="총 실적 금액")
    avg_achievement_rate: float = Field(..., description="평균 달성률")
    employee_count: int = Field(..., description="직원 수")

class BranchTargetBulkCreate(BaseModel):
    """지점 목표 일괄 생성 스키마"""
    branch_id: int = Field(..., description="지점 ID")
    target_year: int = Field(..., description="목표 년도")
    target_month: int = Field(..., description="목표 월")
    targets: list[dict] = Field(..., description="직원별 목표 리스트 [{employee_info_id: int, target_amount: float}]")