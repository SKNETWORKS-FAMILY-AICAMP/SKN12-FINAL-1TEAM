from pydantic import BaseModel

class DocumentRelationBase(BaseModel):
    doc_id: str
    related_doc_id: str
    relation_type: str  # 'reference', 'similar', etc.

class DocumentRelationInfo(DocumentRelationBase):
    class Config:
        from_attributes = True 