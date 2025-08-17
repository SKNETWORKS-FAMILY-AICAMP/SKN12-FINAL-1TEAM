from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time, datetime
from enum import Enum

class ScheduleTypeEnum(str, Enum):
    """일정 유형 Enum"""
    VISIT = "방문"
    MEETING = "회의"
    EDUCATION = "교육"
    OTHER = "기타"

class ScheduleStatusEnum(str, Enum):
    """일정 상태 Enum"""
    SCHEDULED = "예정"
    IN_PROGRESS = "진행중"
    COMPLETED = "완료"
    CANCELLED = "취소"

class ScheduleBase(BaseModel):
    """일정 기본 스키마"""
    title: str = Field(..., description="일정 제목", max_length=200)
    location: str = Field(..., description="거래처/위치", max_length=200)
    contact_person: str = Field(..., description="담당자", max_length=100)
    schedule_date: date = Field(..., description="일정 날짜")
    schedule_time: time = Field(..., description="일정 시간")
    duration: Optional[str] = Field(None, description="소요 시간", max_length=50)
    schedule_type: ScheduleTypeEnum = Field(ScheduleTypeEnum.VISIT, description="일정 유형")
    status: ScheduleStatusEnum = Field(ScheduleStatusEnum.SCHEDULED, description="일정 상태")
    memo: Optional[str] = Field(None, description="메모")

class ScheduleCreate(ScheduleBase):
    """일정 생성 스키마"""
    pass

class ScheduleUpdate(BaseModel):
    """일정 수정 스키마"""
    title: Optional[str] = Field(None, description="일정 제목", max_length=200)
    location: Optional[str] = Field(None, description="거래처/위치", max_length=200)
    contact_person: Optional[str] = Field(None, description="담당자", max_length=100)
    schedule_date: Optional[date] = Field(None, description="일정 날짜")
    schedule_time: Optional[time] = Field(None, description="일정 시간")
    duration: Optional[str] = Field(None, description="소요 시간", max_length=50)
    schedule_type: Optional[ScheduleTypeEnum] = Field(None, description="일정 유형")
    status: Optional[ScheduleStatusEnum] = Field(None, description="일정 상태")
    memo: Optional[str] = Field(None, description="메모")

class ScheduleStatusUpdate(BaseModel):
    """일정 상태 변경 스키마"""
    status: ScheduleStatusEnum = Field(..., description="변경할 상태")

class ScheduleResponse(ScheduleBase):
    """일정 응답 스키마"""
    schedule_id: int = Field(..., description="일정 ID")
    employee_id: int = Field(..., description="직원 ID")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: Optional[datetime] = Field(None, description="수정 일시")
    
    class Config:
        from_attributes = True

class ScheduleWithEmployee(ScheduleResponse):
    """직원 정보를 포함한 일정 응답 스키마"""
    employee_name: Optional[str] = Field(None, description="직원 이름")
    employee_email: Optional[str] = Field(None, description="직원 이메일")
    
    class Config:
        from_attributes = True

class ScheduleBulkCreate(BaseModel):
    """일정 대량 생성 스키마"""
    schedules: list[ScheduleCreate] = Field(..., description="생성할 일정 목록")

class ScheduleSummary(BaseModel):
    """일정 요약 스키마"""
    total_count: int = Field(..., description="전체 일정 수")
    scheduled_count: int = Field(..., description="예정된 일정 수")
    in_progress_count: int = Field(..., description="진행중인 일정 수")
    completed_count: int = Field(..., description="완료된 일정 수")
    cancelled_count: int = Field(..., description="취소된 일정 수")