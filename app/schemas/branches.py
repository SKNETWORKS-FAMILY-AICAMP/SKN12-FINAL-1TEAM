"""
지점 정보 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BranchBase(BaseModel):
    """지점 기본 스키마"""
    headquarters: str = Field(..., description="본부")
    department: str = Field(..., description="부서")
    branch_name: str = Field(..., description="지점명")
    contact_number: Optional[str] = Field(None, description="연락처")
    status: Optional[str] = Field("active", description="상태 (active/inactive)")
    notes: Optional[str] = Field(None, description="비고")

class BranchCreate(BranchBase):
    """지점 생성 스키마"""
    pass

class BranchUpdate(BaseModel):
    """지점 수정 스키마"""
    headquarters: Optional[str] = Field(None, description="본부")
    department: Optional[str] = Field(None, description="부서")
    branch_name: Optional[str] = Field(None, description="지점명")
    contact_number: Optional[str] = Field(None, description="연락처")
    status: Optional[str] = Field(None, description="상태")
    notes: Optional[str] = Field(None, description="비고")

class Branch(BranchBase):
    """지점 응답 스키마"""
    branch_id: int = Field(..., description="지점 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")
    
    class Config:
        from_attributes = True

class BranchList(BaseModel):
    """지점 목록 응답 스키마"""
    total: int = Field(..., description="전체 개수")
    items: List[Branch] = Field(..., description="지점 목록")

class BranchWithStats(Branch):
    """지점 통계 포함 응답 스키마"""
    total_employees: Optional[int] = Field(0, description="총 직원 수")
    total_targets: Optional[int] = Field(0, description="총 목표 수")
    avg_achievement_rate: Optional[float] = Field(0.0, description="평균 달성률")