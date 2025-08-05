from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional, Union, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.document import DocumentBase, DocumentInfo
from app.services.external.s3_service import upload_file, delete_file_from_s3
from app.services.external.postgres_service import save_document, get_documents, get_document_by_id, delete_document_from_postgres
from app.models.documents import Document
from app.services.external.opensearch_service import index_document_chunks, delete_document_chunks_from_opensearch, DOCUMENT_INDEX_NAME
from app.services.core.document_relation_analyzer import document_relation_analyzer

from app.services.core.document_analyzer import document_analyzer
from app.services.core.text2sql_classifier import text2sql_classifier
from app.routers.user_router import get_current_user, get_current_admin_user
from pydantic import BaseModel
import logging

# 파일 처리 관련 라이브러리들
try:
    import pandas as pd
    import io
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)

class TableUploadResult(BaseModel):
    doc_title: str
    doc_type: str
    uploader_id: int
    version: Optional[str]
    created_at: datetime
    message: str
    analysis: Optional[Dict] = None

class BatchUploadResult(BaseModel):
    total_files: int
    successful_uploads: int
    failed_uploads: int
    results: List[Union[DocumentInfo, TableUploadResult]]
    errors: List[Dict[str, str]]

def _extract_csv_data(file_bytes: bytes) -> tuple[str, list]:
    """CSV 파일에서 데이터 추출"""
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas 라이브러리가 설치되지 않았습니다.")
    df = pd.read_csv(io.BytesIO(file_bytes))
    return "", df.to_dict('records')

def _extract_excel_data(file_bytes: bytes) -> tuple[str, list]:
    """Excel 파일에서 데이터 추출"""
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas 라이브러리가 설치되지 않았습니다.")
    df = pd.read_excel(io.BytesIO(file_bytes))
    return "", df.to_dict('records')

def _extract_text_data(file_bytes: bytes) -> tuple[str, list]:
    """TXT 파일에서 텍스트 추출"""
    text = file_bytes.decode("utf-8", errors="ignore")
    return text, []

def _extract_docx_data(file_bytes: bytes) -> tuple[str, list]:
    """DOCX 파일에서 텍스트 추출"""
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx 라이브러리가 설치되지 않았습니다.")
    try:
        doc = DocxDocument(io.BytesIO(file_bytes))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text, []
    except Exception as e:
        logger.error(f"DOCX 파일 텍스트 추출 실패: {e}")
        return "", []

def _extract_pdf_data(file_bytes: bytes) -> tuple[str, list]:
    """PDF 파일에서 텍스트 추출"""
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 라이브러리가 설치되지 않았습니다.")
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text, []
    except Exception as e:
        logger.error(f"PDF 파일 텍스트 추출 실패: {e}")
        return "", []

# 파일 처리 관련 상수 (함수 정의 후에 배치)
FILE_PROCESSORS = {
    '.csv': _extract_csv_data,
    '.xlsx': _extract_excel_data,
    '.xls': _extract_excel_data,
    '.txt': _extract_text_data,
    '.docx': _extract_docx_data,
    '.pdf': _extract_pdf_data,
}

def extract_text_and_table(file_bytes: bytes, filename: str):
    """
    파일 확장자에 따라 텍스트/테이블 데이터를 추출한다.
    
    Args:
        file_bytes: 파일 바이트 데이터
        filename: 파일명
        
    Returns:
        tuple: (text, table_data, is_table_file)
        
    Raises:
        HTTPException: 지원하지 않는 파일 형식 또는 처리 오류
    """
    file_extension = document_analyzer._get_file_extension(filename)
    is_table_file = file_extension in document_analyzer.supported_extensions["table"]
    
    text = ""
    table_data = []
    
    try:
        processor = FILE_PROCESSORS.get(file_extension.lower())
        if processor:
            text, table_data = processor(file_bytes)
        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {file_extension}")
            
    except ImportError as e:
        logger.warning(f"필요한 라이브러리가 설치되지 않았습니다: {e}")
        raise HTTPException(status_code=500, detail="파일 처리를 위한 라이브러리가 필요합니다.")
    except Exception as e:
        logger.error(f"파일 텍스트 추출 실패: {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")
    
    return text, table_data, is_table_file

async def process_single_document(file: UploadFile, uploader_id: int, version: str = None) -> Union[DocumentInfo, TableUploadResult]:
    """
    단일 문서를 처리하는 공통 함수
    
    Args:
        file: 업로드할 파일
        uploader_id: 업로더 ID
        version: 문서 버전 (선택사항)
        
    Returns:
        DocumentInfo 또는 TableUploadResult: 처리 결과
        
    Raises:
        HTTPException: 파일 크기 초과, 지원하지 않는 형식, 처리 오류 등
    """
    # 파일 크기 검증 (10MB 제한)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="파일 크기가 너무 큽니다. 최대 10MB까지 업로드 가능합니다.")
    
    file_bytes = file.file.read()
    file_extension = document_analyzer._get_file_extension(file.filename)
    text, table_data, is_table_file = extract_text_and_table(file_bytes, file.filename)
    
    # 문서 제목이 없으면 파일명 사용 (확장자 제외)
    doc_title = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
    
    # 테이블 문서 처리 - Text2SQL 분류기 사용
    if is_table_file and table_data:
        logger.info(f"테이블 문서 Text2SQL 처리 시작: {file.filename}")
        
        # 1. 원본 파일을 S3에 저장
        file_path = upload_file(file_bytes, file.filename, file.content_type)
        
        # 2. 문서 메타데이터를 documents 테이블에 저장 (먼저 저장)
        meta = DocumentBase(
            doc_title=doc_title,
            doc_type="text2sql_pending",  # 임시 타입
            file_path=file_path,
            uploader_id=uploader_id,
            version=version,
            created_at=datetime.now(timezone.utc)
        )
        doc = save_document(meta)
        
        # 3. Text2SQL 분류기로 처리 (document_id와 uploader_id 전달)
        try:
            result = await text2sql_classifier.classify_table_with_text2sql(
                table_data=table_data,
                table_description=doc_title,
                document_id=doc.doc_id,
                uploader_id=uploader_id
            )
            
            if result['success']:
                logger.info(f"Text2SQL 분류 완료: {result['message']}")
                logger.info(f"분류 결과: {file.filename} -> {result['target_table']} (신뢰도: {result['confidence']:.2f})")
                
                # 4. 문서 타입 업데이트
                doc.doc_type = f"text2sql_{result['target_table']}"
                # 여기서 문서 업데이트 로직이 필요하지만, 현재 save_document는 새로 생성만 함
                # 실제로는 별도의 업데이트 함수가 필요할 수 있음
                
                logger.info(f"테이블 문서 업로드 완료: {doc.doc_id} (타입: {result['target_table']})")
                
                return TableUploadResult(
                    doc_title=doc_title,
                    doc_type=f"text2sql_{result['target_table']}",
                    uploader_id=uploader_id,
                    version=version,
                    created_at=datetime.now(timezone.utc),
                    message=f"{result['message']} (문서 ID: {doc.doc_id})",
                    analysis={
                        'target_table': result['target_table'],
                        'confidence': result['confidence'],
                        'reasoning': result.get('reasoning', ''),
                        'column_mapping': result.get('column_mapping', {}),
                        'doc_id': doc.doc_id
                    }
                )
            else:
                logger.error(f"Text2SQL 분류 실패: {result['message']}")
                raise HTTPException(status_code=500, detail=f"문서 분류 중 오류가 발생했습니다: {result['message']}")
                
        except Exception as e:
            logger.error(f"Text2SQL 분류기 실행 실패: {e}")
            raise HTTPException(status_code=500, detail=f"문서 처리 중 오류가 발생했습니다: {str(e)}")
    
    # 텍스트 문서 처리
    else:
        logger.info(f"텍스트 문서 처리 시작: {file.filename}")
        
        # 문서 타입 분석 (텍스트 문서용)
        analyzed_doc_type = document_analyzer.analyze_document(text, file.filename)
        logger.info(f"문서 분석 결과: {file.filename} -> {analyzed_doc_type}")
        
        # S3 업로드
        file_path = upload_file(file_bytes, file.filename, file.content_type)
        
        # 문서 메타데이터 저장
        meta = DocumentBase(
            doc_title=doc_title,
            doc_type=analyzed_doc_type,
            file_path=file_path,
            uploader_id=uploader_id,
            version=version,
            created_at=datetime.now(timezone.utc)
        )
        doc = save_document(meta)
        
        # OpenSearch 인덱싱 (텍스트 문서만)
        if file_extension in document_analyzer.supported_extensions["text"]:
            chunking_type = document_analyzer.get_chunking_type(analyzed_doc_type)
            index_document_chunks(
                doc_id=doc.doc_id,
                doc_title=doc_title,
                file_name=file.filename,
                text=text,
                document_type=chunking_type
            )
            logger.info(f"텍스트 문서 업로드 완료: {doc.doc_id} (타입: {analyzed_doc_type}, 청킹: {chunking_type})")
        else:
            logger.info(f"문서 업로드 완료: {doc.doc_id} (타입: {analyzed_doc_type})")
        
        return DocumentInfo.model_validate(doc)


@router.post("/documents/upload", response_model=Union[DocumentInfo, TableUploadResult])
async def upload_document(file: UploadFile = File(...), doc_title: str = Form(None), uploader_id: int = Form(...), version: str = Form(None), user=Depends(get_current_user)):
    """
    문서를 업로드하고 자동으로 타입을 분석하여 저장합니다.
    
    Args:
        file: 업로드할 파일
        doc_title: 문서 제목 (선택사항, 없으면 파일명 사용)
        uploader_id: 업로더 ID
        version: 문서 버전 (선택사항)
        user: 현재 인증된 사용자
        
    Returns:
        DocumentInfo 또는 TableUploadResult: 업로드 결과
        
    Raises:
        HTTPException: 파일 크기 초과, 지원하지 않는 형식, 처리 오류 등
    """
    try:
        return await process_single_document(file, uploader_id, version)
    except Exception as e:
        logger.error(f"문서 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"문서 업로드 중 오류가 발생했습니다: {str(e)}")

@router.post("/documents/upload/batch", response_model=BatchUploadResult)
async def upload_documents_batch(files: List[UploadFile] = File(...), uploader_id: int = Form(...), version: str = Form(None), user=Depends(get_current_user)):
    """
    여러 문서를 한 번에 업로드합니다.
    
    Args:
        files: 업로드할 파일들
        uploader_id: 업로더 ID
        version: 문서 버전 (선택사항)
        user: 현재 인증된 사용자
        
    Returns:
        BatchUploadResult: 배치 업로드 결과
    """
    total_files = len(files)
    successful_uploads = 0
    failed_uploads = 0
    results = []
    errors = []
    
    # 배치 업로드 시작 로그
    logger.info(f"배치 업로드 시작: {total_files}개 파일")
    
    # 각 파일을 개별 트랜잭션으로 처리하여 격리 보장
    for i, file in enumerate(files, 1):
        try:
            logger.info(f"배치 업로드 진행 중: {i}/{total_files} - {file.filename}")
            
            # 개별 파일 처리를 위한 트랜잭션 격리
            from app.services.utils.db import create_db_session
            with create_db_session() as session:
                try:
                    # 트랜잭션 격리 레벨 설정
                    session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
                    
                    # 파일 처리 (세션 전달)
                    result = await process_single_document_with_session(file, uploader_id, version, session)
                    results.append(result)
                    successful_uploads += 1
                    logger.info(f"배치 업로드 성공: {file.filename}")
                    
                    session.commit()
                    
                except Exception as e:
                    session.rollback()
                    raise e
                    
        except Exception as e:
            error_msg = f"문서 업로드 실패: {str(e)}"
            errors.append({"filename": file.filename, "error": error_msg})
            failed_uploads += 1
            logger.error(f"배치 업로드 중 오류 ({file.filename}): {e}")
            
            # 개별 파일 실패 시에도 계속 진행
            continue
    
    logger.info(f"배치 업로드 완료: 성공 {successful_uploads}/{total_files}, 실패 {failed_uploads}")
    
    return BatchUploadResult(
        total_files=total_files,
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        results=results,
        errors=errors
    )

async def process_single_document_with_session(file: UploadFile, uploader_id: int, version: str = None, session: Session = None) -> Union[DocumentInfo, TableUploadResult]:
    """
    세션을 받아서 단일 문서를 처리하는 함수 (트랜잭션 격리용)
    """
    # 기존 process_single_document 로직을 세션 기반으로 수정
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="파일 크기가 너무 큽니다. 최대 10MB까지 업로드 가능합니다.")
    
    file_bytes = file.file.read()
    file_extension = document_analyzer._get_file_extension(file.filename)
    text, table_data, is_table_file = extract_text_and_table(file_bytes, file.filename)
    
    doc_title = file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename
    
    # 테이블 문서 처리
    if is_table_file and table_data:
        logger.info(f"테이블 문서 Text2SQL 처리 시작: {file.filename}")
        
        # S3 업로드
        file_path = upload_file(file_bytes, file.filename, file.content_type)
        
        # 문서 메타데이터 저장 (세션 사용)
        meta = DocumentBase(
            doc_title=doc_title,
            doc_type="text2sql_pending",
            file_path=file_path,
            uploader_id=uploader_id,
            version=version,
            created_at=datetime.now(timezone.utc)
        )
        
        # 세션을 사용하여 문서 저장
        db_doc = Document(**meta.dict())
        session.add(db_doc)
        session.flush()  # ID 생성을 위해 flush
        
        # Text2SQL 분류기로 처리 (세션 전달)
        try:
            result = await text2sql_classifier.classify_table_with_text2sql(
                table_data=table_data,
                table_description=doc_title,
                document_id=db_doc.doc_id,
                uploader_id=uploader_id
            )
            
            if result['success']:
                logger.info(f"Text2SQL 분류 완료: {result['message']}")
                
                # 문서 타입 업데이트
                db_doc.doc_type = f"text2sql_{result['target_table']}"
                session.flush()
                
                return TableUploadResult(
                    doc_title=doc_title,
                    doc_type=f"text2sql_{result['target_table']}",
                    uploader_id=uploader_id,
                    version=version,
                    created_at=datetime.now(timezone.utc),
                    message=f"{result['message']} (문서 ID: {db_doc.doc_id})",
                    analysis={
                        'target_table': result['target_table'],
                        'confidence': result['confidence'],
                        'reasoning': result.get('reasoning', ''),
                        'column_mapping': result.get('column_mapping', {}),
                        'doc_id': db_doc.doc_id
                    }
                )
            else:
                raise HTTPException(status_code=500, detail=f"문서 분류 중 오류가 발생했습니다: {result['message']}")
                
        except Exception as e:
            logger.error(f"Text2SQL 분류기 실행 실패: {e}")
            raise HTTPException(status_code=500, detail=f"문서 처리 중 오류가 발생했습니다: {str(e)}")
    
    # 텍스트 문서 처리
    else:
        logger.info(f"텍스트 문서 처리 시작: {file.filename}")
        
        analyzed_doc_type = document_analyzer.analyze_document(text, file.filename)
        logger.info(f"문서 분석 결과: {file.filename} -> {analyzed_doc_type}")
        
        file_path = upload_file(file_bytes, file.filename, file.content_type)
        
        meta = DocumentBase(
            doc_title=doc_title,
            doc_type=analyzed_doc_type,
            file_path=file_path,
            uploader_id=uploader_id,
            version=version,
            created_at=datetime.now(timezone.utc)
        )
        
        # 세션을 사용하여 문서 저장
        db_doc = Document(**meta.dict())
        session.add(db_doc)
        session.flush()
        
        # OpenSearch 인덱싱 (텍스트 문서만)
        if file_extension in document_analyzer.supported_extensions["text"]:
            chunking_type = document_analyzer.get_chunking_type(analyzed_doc_type)
            index_document_chunks(
                doc_id=db_doc.doc_id,
                doc_title=doc_title,
                file_name=file.filename,
                text=text,
                document_type=chunking_type
            )
            logger.info(f"텍스트 문서 업로드 완료: {db_doc.doc_id} (타입: {analyzed_doc_type}, 청킹: {chunking_type})")
        else:
            logger.info(f"문서 업로드 완료: {db_doc.doc_id} (타입: {analyzed_doc_type})")
        
        return DocumentInfo.model_validate(db_doc)

@router.get("/documents/", response_model=List[DocumentInfo])
def list_documents(user=Depends(get_current_user)):
    """
    모든 문서 목록을 조회합니다.
    
    Args:
        user: 현재 인증된 사용자
        
    Returns:
        List[DocumentInfo]: 문서 목록
    """
    docs = get_documents()
    return [DocumentInfo.model_validate(doc) for doc in docs]

@router.get("/documents/{doc_id}", response_model=DocumentInfo)
def get_document(doc_id: int, user=Depends(get_current_user)):
    """
    특정 문서를 조회합니다.
    
    Args:
        doc_id: 문서 ID
        user: 현재 인증된 사용자
        
    Returns:
        DocumentInfo: 문서 정보
        
    Raises:
        HTTPException: 문서를 찾을 수 없는 경우
    """
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentInfo.model_validate(doc)

@router.delete("/documents/{doc_id}", response_model=DocumentInfo)
def delete_document(doc_id: int, admin=Depends(get_current_admin_user)):
    """
    문서를 삭제합니다. (관리자만 가능)
    
    Args:
        doc_id: 삭제할 문서 ID
        admin: 현재 인증된 관리자
        
    Returns:
        DocumentInfo: 삭제된 문서 정보
        
    Raises:
        HTTPException: 문서를 찾을 수 없거나 삭제 실패 시
    """
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # 1. S3에서 원본 파일 삭제
        file_name = doc.file_path.split("/")[-1]
        delete_file_from_s3(file_name)
        logger.info(f"S3 파일 삭제 완료: {file_name}")
        
        # 2. OpenSearch에서 문서 청크 삭제 (텍스트 문서용)
        delete_document_chunks_from_opensearch(DOCUMENT_INDEX_NAME, doc_id)
        logger.info(f"OpenSearch 문서 청크 삭제 완료: doc_id={doc_id}")
        

        
        # 4. 문서 관계 삭제
        try:
            relation_delete_result = document_relation_analyzer.delete_document_relations(doc_id)
            if relation_delete_result['success']:
                logger.info(f"문서 관계 삭제 완료: {relation_delete_result['deleted_count']}개")
            else:
                logger.warning(f"문서 관계 삭제 실패: {relation_delete_result['message']}")
        except Exception as e:
            logger.error(f"문서 관계 삭제 중 오류: {e}")
        
        # 5. PostgreSQL에서 문서 메타데이터 삭제
        deleted_doc = delete_document_from_postgres(doc_id)
        if not deleted_doc:
            raise HTTPException(status_code=500, detail="Failed to delete document from DB")
        
        logger.info(f"문서 완전 삭제 완료: doc_id={doc_id}, title={doc.doc_title}")
        return DocumentInfo.model_validate(deleted_doc)
        
    except Exception as e:
        logger.error(f"문서 삭제 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문서 삭제 중 오류가 발생했습니다: {str(e)}") 