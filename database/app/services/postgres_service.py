from app.models.documents import Document
from app.services.db import SessionLocal
from app.schemas.document import DocumentBase
from sqlalchemy.orm import Session
from typing import List, Optional

def save_document(doc_meta: DocumentBase) -> Document:
    db = SessionLocal()
    try:
        db_doc = Document(**doc_meta.dict())
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        return db_doc
    finally:
        db.close()

def get_documents() -> List[dict]:
    db = SessionLocal()
    try:
        # relationship을 사용해서 직원 정보와 함께 가져오기
        documents = db.query(Document).all()
        
        # 딕셔너리 형태로 변환
        return [
            {
                'doc_id': doc.doc_id,
                'doc_title': doc.doc_title,
                'doc_type': doc.doc_type,
                'file_path': doc.file_path,
                'version': doc.version,
                'created_at': doc.created_at,
                'uploader_id': doc.uploader_id,
                'uploader_name': doc.uploader.name if doc.uploader else None
            }
            for doc in documents
        ]
    finally:
        db.close()

def get_document_by_id(doc_id: int) -> Optional[dict]:
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        
        if doc:
            return {
                'doc_id': doc.doc_id,
                'doc_title': doc.doc_title,
                'doc_type': doc.doc_type,
                'file_path': doc.file_path,
                'version': doc.version,
                'created_at': doc.created_at,
                'uploader_id': doc.uploader_id,
                'uploader_name': doc.uploader.name if doc.uploader else None
            }
        return None
    finally:
        db.close()

def delete_document_from_postgres(doc_id: int) -> Optional[Document]:
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if doc:
            db.delete(doc)
            db.commit()
        return doc
    finally:
        db.close()
