from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List
from datetime import datetime
from schemas.document import DocumentBase, DocumentInfo
from services.s3_service import upload_file, delete_file_from_s3
from services.postgres_service import save_document, get_documents, get_document_by_id, delete_document_from_postgres
from services.opensearch_service import index_document_chunks, delete_document_chunks_from_opensearch, DOCUMENT_INDEX_NAME

from services.document_analyzer import document_analyzer
from routers.user_router import get_current_user, get_current_admin_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/documents/upload", response_model=DocumentInfo)
def upload_document(file: UploadFile = File(...), doc_title: str = Form(...), uploader_id: int = Form(...), doc_type: str = Form(None), version: str = Form(None), user=Depends(get_current_user)):
    """
    문서를 업로드하고 자동으로 타입을 분석하여 저장합니다.
    
    Args:
        file: 업로드할 파일 (.txt, .docx, .pdf, .csv, .xlsx, .xls)
        doc_title: 문서 제목
        uploader_id: 업로더 ID
        doc_type: 문서 타입 (선택사항, 자동 분석 시 무시됨)
        version: 문서 버전
        user: 현재 사용자
        
    Returns:
        업로드된 문서 정보
    """
    try:
        # 파일 형식 검증
        if not document_analyzer.is_supported_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: .txt, .docx, .pdf, .csv, .xlsx, .xls"
            )
        
        # 파일 읽기
        file_bytes = file.file.read()
        content_type = file.content_type
        
        # 파일을 S3에 업로드
        file_path = upload_file(file_bytes, file.filename, content_type)
        
        # 문서 내용 추출 (파일 형식별 적절한 방법 사용)
        text = ""
        if file.filename.lower().endswith('.txt'):
            # 텍스트 파일은 UTF-8로 디코딩
            text = file_bytes.decode("utf-8", errors="ignore")
        elif file.filename.lower().endswith('.docx'):
            # DOCX 파일은 python-docx 라이브러리 사용
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(file_bytes))
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            except ImportError:
                logger.warning("python-docx 라이브러리가 설치되지 않았습니다. DOCX 파일 내용을 추출할 수 없습니다.")
                text = ""
            except Exception as e:
                logger.error(f"DOCX 파일 텍스트 추출 실패: {e}")
                text = ""
        elif file.filename.lower().endswith('.pdf'):
            # PDF 파일은 PyPDF2 또는 pdfplumber 라이브러리 사용
            try:
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            except ImportError:
                logger.warning("PyPDF2 라이브러리가 설치되지 않았습니다. PDF 파일 내용을 추출할 수 없습니다.")
                text = ""
            except Exception as e:
                logger.error(f"PDF 파일 텍스트 추출 실패: {e}")
                text = ""
        
        # 자동 문서 타입 분석
        analyzed_doc_type = document_analyzer.analyze_document(text, file.filename)
        
        # 분석 결과 로깅
        logger.info(f"문서 분석 결과: {file.filename} -> {analyzed_doc_type}")
        
        # 문서 메타데이터 생성
        meta = DocumentBase(
            doc_title=doc_title,
            doc_type=analyzed_doc_type,  # 자동 분석된 타입 사용
            file_path=file_path,
            uploader_id=uploader_id,
            version=version,
            created_at=datetime.utcnow()
        )
        
        # PostgreSQL에 문서 저장
        doc = save_document(meta)
        
        # 텍스트 문서인 경우에만 청킹/임베딩 수행
        if file.filename.lower().endswith(('.txt', '.docx', '.pdf')):
            # 청킹 타입 결정
            chunking_type = document_analyzer.get_chunking_type(analyzed_doc_type)
            
            # 문서 청킹/임베딩/OpenSearch 저장
            index_document_chunks(
                doc_id=doc.doc_id,
                doc_title=doc_title,
                file_name=file.filename,
                text=text,
                document_type=chunking_type
            )
            
            logger.info(f"문서 업로드 완료: {doc.doc_id} (타입: {analyzed_doc_type}, 청킹: {chunking_type})")
        else:
            logger.info(f"테이블 문서 업로드 완료: {doc.doc_id} (타입: {analyzed_doc_type})")
        
        return DocumentInfo.model_validate(doc)
        
    except Exception as e:
        logger.error(f"문서 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"문서 업로드 중 오류가 발생했습니다: {str(e)}")

@router.get("/documents/", response_model=List[DocumentInfo])
def list_documents(user=Depends(get_current_user)):
    docs = get_documents()
    return [DocumentInfo.model_validate(doc) for doc in docs]

@router.get("/documents/{doc_id}", response_model=DocumentInfo)
def get_document(doc_id: int, user=Depends(get_current_user)):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentInfo.model_validate(doc)

@router.delete("/documents/{doc_id}", response_model=DocumentInfo)
def delete_document(doc_id: int, admin=Depends(get_current_admin_user)):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    file_name = doc.file_path.split("/")[-1]
    delete_file_from_s3(file_name)
    delete_document_chunks_from_opensearch(DOCUMENT_INDEX_NAME, doc_id)
    deleted_doc = delete_document_from_postgres(doc_id)
    if not deleted_doc:
        raise HTTPException(status_code=500, detail="Failed to delete document from DB")
    return DocumentInfo.model_validate(deleted_doc) 