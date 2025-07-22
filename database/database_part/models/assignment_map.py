from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint

class AssignmentMap(Base):
    __tablename__ = "assignment_map"
    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('employee_id', 'customer_id', name='uq_assignment_employee_customer'),
    ) 
