from . import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

class Employee(Base):
    __tablename__ = "employees"
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    team = Column(String)
    position = Column(String)
    business_unit = Column(String)
    branch = Column(String)
    contact_number = Column(String)
    responsibilities = Column(String)
    base_salary = Column(Integer)
    incentive_pay = Column(Integer)
    avg_monthly_budget = Column(Integer)
    latest_evaluation = Column(String)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
