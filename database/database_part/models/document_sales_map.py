from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint

class DocumentSalesMap(Base):
    __tablename__ = "document_sales_map"
    link_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.doc_id"), nullable=False)
    sales_record_id = Column(Integer, ForeignKey("sales_records.record_id"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('doc_id', 'sales_record_id', name='uq_doc_sales_doc_sales'),
    ) 
