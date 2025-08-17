from . import Base
from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
import enum

class ScheduleType(enum.Enum):
    """일정 유형 열거형"""
    VISIT = "방문"  # 거래처 방문
    MEETING = "회의"  # 회의
    EDUCATION = "교육"  # 교육/세미나
    OTHER = "기타"  # 기타

class ScheduleStatus(enum.Enum):
    """일정 상태 열거형"""
    SCHEDULED = "예정"  # 예정된 일정
    IN_PROGRESS = "진행중"  # 진행중인 일정
    COMPLETED = "완료"  # 완료된 일정
    CANCELLED = "취소"  # 취소된 일정

class Schedule(Base):
    """직원 일정을 관리하는 테이블"""
    __tablename__ = "schedules"
    
    # 기본 식별 정보
    schedule_id = Column(Integer, primary_key=True, autoincrement=True)  # 일정 고유 ID
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)  # 직원 ID
    
    # 일정 정보
    title = Column(String(200), nullable=False)  # 일정 제목
    location = Column(String(200), nullable=False)  # 거래처/위치
    contact_person = Column(String(100), nullable=False)  # 담당자
    
    # 일정 시간 정보
    schedule_date = Column(Date, nullable=False)  # 일정 날짜
    schedule_time = Column(Time, nullable=False)  # 일정 시간
    duration = Column(String(50))  # 소요 시간 (예: "1시간", "30분", "2시간")
    
    # 일정 분류 및 상태
    schedule_type = Column(
        Enum(ScheduleType, values_callable=lambda obj: [e.value for e in obj]), 
        nullable=False,
        default=ScheduleType.VISIT
    )  # 일정 유형
    status = Column(
        Enum(ScheduleStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ScheduleStatus.SCHEDULED
    )  # 일정 상태
    
    # 추가 정보
    memo = Column(Text)  # 메모
    
    # 시스템 정보
    created_at = Column(DateTime(timezone=True), default=func.now())  # 생성 일시
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 수정 일시
    
    # 관계 설정
    employee = relationship("Employee", backref="schedules")