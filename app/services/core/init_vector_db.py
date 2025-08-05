"""
벡터 DB 초기화 스크립트
테이블 설명을 pgvector에 저장합니다.
"""

import asyncio
import logging
from sqlalchemy.orm import Session

from app.services.utils.db import SessionLocal
from app.services.core.vector_similarity_service import vector_similarity_service

logger = logging.getLogger(__name__)

async def init_vector_database():
    """벡터 데이터베이스 초기화"""
    try:
        session = SessionLocal()
        
        # 테이블 설명 벡터 초기화
        await vector_similarity_service.initialize_table_descriptions(session)
        
        logger.info("벡터 데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"벡터 데이터베이스 초기화 실패: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 비동기 실행
    asyncio.run(init_vector_database()) 