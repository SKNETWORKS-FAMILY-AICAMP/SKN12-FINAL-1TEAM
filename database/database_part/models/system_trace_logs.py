from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, BigInteger
from sqlalchemy.dialects.postgresql import JSONB

class SystemTraceLog(Base):
    __tablename__ = "system_trace_logs"
    trace_id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, ForeignKey("chat_history.message_id"), nullable=False)
    event_type = Column(String)
    log_data = Column(JSONB)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=func.now()) 
