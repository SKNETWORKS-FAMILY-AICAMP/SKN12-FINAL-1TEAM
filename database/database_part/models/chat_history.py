from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, BigInteger, Text

class ChatHistory(Base):
    __tablename__ = "chat_history"
    message_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    user_query = Column(Text)
    system_response = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now()) 
