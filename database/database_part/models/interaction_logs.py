from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

class InteractionLog(Base):
    __tablename__ = "interaction_logs"
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False)
    interaction_type = Column(String)
    summary = Column(String)
    sentiment = Column(String)
    compliance_risk = Column(String)
    interacted_at = Column(DateTime) 
