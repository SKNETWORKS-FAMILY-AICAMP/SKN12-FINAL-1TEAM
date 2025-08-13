from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Time, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    
    employee_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with schedules
    schedules = relationship("Schedule", back_populates="employee")

class Schedule(Base):
    __tablename__ = "schedules"
    
    schedule_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    
    # 기본 일정 정보
    schedule_type = Column(String, nullable=False)  # 'visit', 'meeting', 'training', 'report', 'other'
    title = Column(String, nullable=False)  # 일정 제목
    description = Column(Text)  # 상세 설명
    
    # 날짜 및 시간 정보
    schedule_date = Column(Date, nullable=False)  # 일정 날짜
    start_time = Column(Time)  # 시작 시간
    end_time = Column(Time)  # 종료 시간
    
    # 방문/회의 관련 정보
    location = Column(String)  # 위치/장소
    client_name = Column(String)  # 고객사/거래처명
    client_contact = Column(String)  # 담당자 연락처
    purpose = Column(Text)  # 방문 목적/회의 안건
    
    # 상태 및 우선순위
    status = Column(String, default='scheduled')  # 'scheduled', 'in_progress', 'completed', 'cancelled'
    priority = Column(String, default='medium')  # 'high', 'medium', 'low'
    
    # 결과 및 후속 조치
    result = Column(Text)  # 방문/회의 결과
    follow_up = Column(Text)  # 후속 조치 사항
    
    # 알림 설정
    reminder = Column(Boolean, default=False)  # 알림 설정 여부
    reminder_time = Column(DateTime)  # 알림 시간
    
    # 메타 정보
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    # Relationship
    employee = relationship("Employee", back_populates="schedules")