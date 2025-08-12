"""
직원 인사정보 스키마
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class EmployeeInfoBase(BaseModel):
    """직원 인사정보 기본 스키마"""
    name: str = Field(..., description="직원명")
    employee_number: Optional[str] = Field(None, description="사번")
    position: Optional[str] = Field(None, description="직급")
    branch_id: Optional[int] = Field(None, description="지점 ID")
    contact_number: Optional[str] = Field(None, description="연락처")
    base_salary: Optional[int] = Field(None, description="기본급")
    incentive_pay: Optional[int] = Field(None, description="인센티브")
    avg_monthly_budget: Optional[int] = Field(None, description="월평균 예산")
    latest_evaluation: Optional[str] = Field(None, description="최근 평가")
    responsibilities: Optional[str] = Field(None, description="담당 업무")

class EmployeeInfoCreate(EmployeeInfoBase):
    """직원 인사정보 생성 스키마"""
    pass

class EmployeeInfoUpdate(BaseModel):
    """직원 인사정보 수정 스키마"""
    name: Optional[str] = Field(None, description="직원명")
    employee_number: Optional[str] = Field(None, description="사번")
    position: Optional[str] = Field(None, description="직급")
    branch_id: Optional[int] = Field(None, description="지점 ID")
    contact_number: Optional[str] = Field(None, description="연락처")
    base_salary: Optional[int] = Field(None, description="기본급")
    incentive_pay: Optional[int] = Field(None, description="인센티브")
    avg_monthly_budget: Optional[int] = Field(None, description="월평균 예산")
    latest_evaluation: Optional[str] = Field(None, description="최근 평가")
    responsibilities: Optional[str] = Field(None, description="담당 업무")

class EmployeeInfoResponse(EmployeeInfoBase):
    """직원 인사정보 응답 스키마"""
    employee_info_id: int = Field(..., description="인사정보 ID")
    employee_id: Optional[int] = Field(None, description="직원 계정 ID")
    is_auto_created: bool = Field(False, description="자동 생성 여부")
    approval_status: str = Field("pending", description="승인 상태")
    approved_by: Optional[int] = Field(None, description="승인자 ID")
    approved_at: Optional[datetime] = Field(None, description="승인 일시")
    approval_notes: Optional[str] = Field(None, description="승인 메모")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    
    class Config:
        from_attributes = True

class EmployeeInfoWithBranch(EmployeeInfoResponse):
    """지점 정보 포함 직원 인사정보 스키마"""
    branch_name: Optional[str] = Field(None, description="지점명")
    headquarters: Optional[str] = Field(None, description="본부")
    department: Optional[str] = Field(None, description="부서")

class EmployeeInfoLegacy(EmployeeInfoBase):
    """레거시 호환용 스키마 (기존 branch 필드 포함)"""
    branch: Optional[str] = Field(None, description="지점명 (deprecated, use branch_id)")
    team: Optional[str] = Field(None, description="팀명 (deprecated)")
    business_unit: Optional[str] = Field(None, description="사업부 (deprecated)")
    
    class Config:
        from_attributes = True