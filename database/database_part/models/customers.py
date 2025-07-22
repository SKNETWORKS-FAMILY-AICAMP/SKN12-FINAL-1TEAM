from . import Base
from sqlalchemy import Column, Integer, String, DateTime, func

class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String, nullable=False)
    customer_type = Column(String)
    address = Column(String)
    doctor_name = Column(String)
    total_patients = Column(Integer)
    customer_grade = Column(String)
    notes = Column(String)
    created_at = Column(DateTime, default=func.now()) 
