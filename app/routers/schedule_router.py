"""
직원 일정 관리 라우터
일정 생성, 조회, 수정, 삭제 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, cast, Date
from datetime import date, datetime, timedelta
from pydantic import BaseModel

from app.services.utils.db import get_db
from app.routers.user_router import get_current_user
from app.models.schedules import Schedule, ScheduleType, ScheduleStatus
from app.models.employees import Employee
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleWithEmployee,
    ScheduleStatusUpdate,
    ScheduleSummary
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=List[ScheduleWithEmployee])
def get_schedules(
    employee_id: Optional[int] = Query(None, description="직원 ID로 필터링"),
    schedule_date: Optional[date] = Query(None, description="특정 날짜의 일정"),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    schedule_type: Optional[str] = Query(None, description="일정 유형"),
    status: Optional[str] = Query(None, description="일정 상태"),
    skip: int = Query(0, description="페이지네이션 오프셋"),
    limit: int = Query(100, description="페이지 크기"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> List[ScheduleWithEmployee]:
    """
    일정 목록 조회
    
    Args:
        employee_id: 특정 직원의 일정만 조회
        schedule_date: 특정 날짜의 일정만 조회
        start_date: 검색 시작 날짜
        end_date: 검색 종료 날짜
        schedule_type: 일정 유형 필터
        status: 일정 상태 필터
        
    Returns:
        일정 목록
    """
    try:
        query = db.query(Schedule).join(Employee, Schedule.employee_id == Employee.employee_id)
        
        # 필터 적용
        if employee_id:
            query = query.filter(Schedule.employee_id == employee_id)
        
        if schedule_date:
            query = query.filter(Schedule.schedule_date == schedule_date)
        elif start_date and end_date:
            query = query.filter(
                and_(
                    Schedule.schedule_date >= start_date,
                    Schedule.schedule_date <= end_date
                )
            )
        elif start_date:
            query = query.filter(Schedule.schedule_date >= start_date)
        elif end_date:
            query = query.filter(Schedule.schedule_date <= end_date)
        
        if schedule_type:
            query = query.filter(Schedule.schedule_type == schedule_type)
        
        if status:
            query = query.filter(Schedule.status == status)
        
        # 날짜와 시간 순으로 정렬
        schedules = query.order_by(
            Schedule.schedule_date,
            Schedule.schedule_time
        ).offset(skip).limit(limit).all()
        
        # 직원 정보 포함한 응답 생성
        result = []
        for schedule in schedules:
            schedule_dict = {
                "schedule_id": schedule.schedule_id,
                "employee_id": schedule.employee_id,
                "title": schedule.title,
                "location": schedule.location,
                "contact_person": schedule.contact_person,
                "schedule_date": schedule.schedule_date,
                "schedule_time": schedule.schedule_time,
                "duration": schedule.duration,
                "schedule_type": schedule.schedule_type.value if hasattr(schedule.schedule_type, 'value') else schedule.schedule_type,
                "status": schedule.status.value if hasattr(schedule.status, 'value') else schedule.status,
                "memo": schedule.memo,
                "created_at": schedule.created_at,
                "updated_at": schedule.updated_at,
                "employee_name": schedule.employee.name if schedule.employee else None,
                "employee_email": schedule.employee.email if schedule.employee else None
            }
            result.append(ScheduleWithEmployee(**schedule_dict))
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/my", response_model=List[ScheduleResponse])
def get_my_schedules(
    schedule_date: Optional[date] = Query(None, description="특정 날짜의 일정"),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    status: Optional[str] = Query(None, description="일정 상태"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> List[ScheduleResponse]:
    """
    내 일정 조회
    
    Returns:
        로그인한 사용자의 일정 목록
    """
    try:
        query = db.query(Schedule).filter(Schedule.employee_id == current_user.employee_id)
        
        # 날짜 필터
        if schedule_date:
            query = query.filter(Schedule.schedule_date == schedule_date)
        elif start_date and end_date:
            query = query.filter(
                and_(
                    Schedule.schedule_date >= start_date,
                    Schedule.schedule_date <= end_date
                )
            )
        
        if status:
            query = query.filter(Schedule.status == status)
        
        schedules = query.order_by(
            Schedule.schedule_date.desc(),
            Schedule.schedule_time
        ).all()
        
        return [ScheduleResponse.model_validate(schedule) for schedule in schedules]
    
    except Exception as e:
        logger.error(f"Error fetching my schedules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"내 일정 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/today", response_model=List[ScheduleWithEmployee])
def get_today_schedules(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> List[ScheduleWithEmployee]:
    """
    오늘의 일정 조회
    
    Returns:
        오늘 날짜의 모든 일정
    """
    today = date.today()
    return get_schedules(
        schedule_date=today,
        db=db,
        current_user=current_user
    )

@router.get("/week", response_model=List[ScheduleWithEmployee])
def get_week_schedules(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> List[ScheduleWithEmployee]:
    """
    이번 주 일정 조회
    
    Returns:
        이번 주의 모든 일정
    """
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    return get_schedules(
        start_date=start_of_week,
        end_date=end_of_week,
        db=db,
        current_user=current_user
    )

@router.get("/summary", response_model=ScheduleSummary)
def get_schedule_summary(
    employee_id: Optional[int] = Query(None, description="직원 ID"),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> ScheduleSummary:
    """
    일정 요약 통계 조회
    
    Returns:
        일정 상태별 개수 통계
    """
    try:
        query = db.query(Schedule)
        
        if employee_id:
            query = query.filter(Schedule.employee_id == employee_id)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    Schedule.schedule_date >= start_date,
                    Schedule.schedule_date <= end_date
                )
            )
        
        schedules = query.all()
        
        summary = ScheduleSummary(
            total_count=len(schedules),
            scheduled_count=sum(1 for s in schedules if s.status == ScheduleStatus.SCHEDULED),
            in_progress_count=sum(1 for s in schedules if s.status == ScheduleStatus.IN_PROGRESS),
            completed_count=sum(1 for s in schedules if s.status == ScheduleStatus.COMPLETED),
            cancelled_count=sum(1 for s in schedules if s.status == ScheduleStatus.CANCELLED)
        )
        
        return summary
    
    except Exception as e:
        logger.error(f"Error getting schedule summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 요약 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: int = Path(..., description="일정 ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> ScheduleResponse:
    """
    특정 일정 상세 조회
    
    Args:
        schedule_id: 일정 ID
        
    Returns:
        일정 상세 정보
    """
    schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
    
    return ScheduleResponse.model_validate(schedule)

@router.post("", response_model=ScheduleResponse)
def create_schedule(
    schedule_data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> ScheduleResponse:
    """
    일정 생성
    
    Args:
        schedule_data: 생성할 일정 정보
        
    Returns:
        생성된 일정 정보
    """
    try:
        # 일정 충돌 검사 (선택사항)
        existing = db.query(Schedule).filter(
            and_(
                Schedule.employee_id == current_user.employee_id,
                Schedule.schedule_date == schedule_data.schedule_date,
                Schedule.schedule_time == schedule_data.schedule_time,
                Schedule.status != ScheduleStatus.CANCELLED
            )
        ).first()
        
        if existing:
            logger.warning(f"Schedule conflict for employee {current_user.employee_id} at {schedule_data.schedule_date} {schedule_data.schedule_time}")
            # 경고만 하고 생성은 허용 (필요시 에러 발생 가능)
        
        # 일정 생성
        new_schedule = Schedule(
            employee_id=current_user.employee_id,
            **schedule_data.model_dump()
        )
        
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)
        
        logger.info(f"Schedule created: {new_schedule.schedule_id} for employee {current_user.employee_id}")
        return ScheduleResponse.model_validate(new_schedule)
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 생성 중 오류가 발생했습니다: {str(e)}")

@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int = Path(..., description="일정 ID"),
    schedule_data: ScheduleUpdate = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> ScheduleResponse:
    """
    일정 수정
    
    Args:
        schedule_id: 수정할 일정 ID
        schedule_data: 수정할 일정 정보
        
    Returns:
        수정된 일정 정보
    """
    try:
        schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
        
        # 본인 일정만 수정 가능
        if schedule.employee_id != current_user.employee_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="본인의 일정만 수정할 수 있습니다")
        
        # 업데이트
        update_data = schedule_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        schedule.updated_at = func.now()
        
        db.commit()
        db.refresh(schedule)
        
        logger.info(f"Schedule updated: {schedule_id}")
        return ScheduleResponse.model_validate(schedule)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 수정 중 오류가 발생했습니다: {str(e)}")

@router.patch("/{schedule_id}/status", response_model=ScheduleResponse)
def update_schedule_status(
    schedule_id: int = Path(..., description="일정 ID"),
    status_data: ScheduleStatusUpdate = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> ScheduleResponse:
    """
    일정 상태 변경
    
    Args:
        schedule_id: 일정 ID
        status_data: 변경할 상태
        
    Returns:
        수정된 일정 정보
    """
    try:
        schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
        
        # 본인 일정만 수정 가능
        if schedule.employee_id != current_user.employee_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="본인의 일정만 수정할 수 있습니다")
        
        # 상태 업데이트
        schedule.status = status_data.status
        schedule.updated_at = func.now()
        
        db.commit()
        db.refresh(schedule)
        
        logger.info(f"Schedule {schedule_id} status updated to {status_data.status}")
        return ScheduleResponse.model_validate(schedule)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating schedule status {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 상태 변경 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int = Path(..., description="일정 ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    일정 삭제
    
    Args:
        schedule_id: 삭제할 일정 ID
        
    Returns:
        삭제 성공 메시지
    """
    try:
        schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")
        
        # 본인 일정만 삭제 가능
        if schedule.employee_id != current_user.employee_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="본인의 일정만 삭제할 수 있습니다")
        
        db.delete(schedule)
        db.commit()
        
        logger.info(f"Schedule deleted: {schedule_id}")
        return {"message": f"일정 {schedule_id}이(가) 삭제되었습니다"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 삭제 중 오류가 발생했습니다: {str(e)}")