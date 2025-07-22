from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint

class DocumentInteractionMap(Base):
    __tablename__ = "document_interaction_map"
    link_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.doc_id"), nullable=False)
    interaction_id = Column(Integer, ForeignKey("interaction_logs.log_id"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('doc_id', 'interaction_id', name='uq_doc_interaction_doc_interaction'),
    ) 
