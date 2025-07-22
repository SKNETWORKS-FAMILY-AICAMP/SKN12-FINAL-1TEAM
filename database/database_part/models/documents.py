from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

class Document(Base):
    __tablename__ = "documents"
    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    uploader_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    doc_title = Column(String, nullable=False)
    doc_type = Column(String)
    file_path = Column(String, nullable=False)
    version = Column(String)
    created_at = Column(DateTime, default=func.now()) 
