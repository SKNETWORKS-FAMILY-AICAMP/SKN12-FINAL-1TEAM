from . import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, UniqueConstraint

class DocumentRelation(Base):
    __tablename__ = "document_relations"
    relation_id = Column(Integer, primary_key=True, autoincrement=True)
    source_doc_id = Column(Integer, ForeignKey("documents.doc_id"), nullable=False)
    related_doc_id = Column(Integer, ForeignKey("documents.doc_id"), nullable=False)
    relation_type = Column(String, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('source_doc_id', 'related_doc_id', name='uq_doc_relation_source_related'),
    ) 
