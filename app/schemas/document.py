from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    doc_title: str
    doc_type: Optional[str] = None
    file_path: str
    uploader_id: int
    version: Optional[str] = None
    summary: Optional[str] = None
    created_at: Optional[datetime] = None

class DocumentInfo(DocumentBase):
    doc_id: int
    processing_status: Optional[str] = None
    processed_at: Optional[datetime] = None
    processing_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True 