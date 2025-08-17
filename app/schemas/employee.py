from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class EmployeeBase(BaseModel):
    """
    email: unique, required
    password: required (only for creation)
    name: required
    role: required
    is_active: default True
    created_at: optional
    """
    email: EmailStr
    password: Optional[constr(min_length=8)] = None
    name: str
    role: str  # 'admin', 'manager', 'user'
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None

class EmployeeCreate(EmployeeBase):
    password: constr(min_length=8)

class EmployeeLogin(BaseModel):
    email: EmailStr
    password: str

class EmployeeInfo(EmployeeBase):
    employee_id: int

    class Config:
        from_attributes = True

class EmployeeRegisterRequest(BaseModel):
    """직원 계정 등록 요청 스키마"""
    name: str  # 직원 이름
    employee_number: str  # 사번
    email: EmailStr  # 이메일
    password: constr(min_length=8)  # 패스워드
    role: str = "user"  # 기본 역할 (user, manager, admin) 