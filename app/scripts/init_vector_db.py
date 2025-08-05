#!/usr/bin/env python3
"""
벡터 데이터베이스 초기화 스크립트
컨테이너 내부에서 직접 실행할 수 있습니다.

사용법:
    docker exec -it fastapi-app python /app/app/scripts/init_vector_db.py
"""

import asyncio
import sys
import os
import logging

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, '/app')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

async def init_vector_database():
    """벡터 데이터베이스 초기화"""
    try:
        from app.services.core.vector_similarity_service import vector_similarity_service
        from app.services.utils.db import SessionLocal
        
        logger.info("🔧 벡터 데이터베이스 초기화 시작...")
        
        # 데이터베이스 세션 생성
        session = SessionLocal()
        
        try:
            # 벡터 데이터베이스 초기화
            await vector_similarity_service.initialize_table_descriptions(session)
            logger.info("✅ 벡터 데이터베이스 초기화 완료")
            return True
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ 벡터 데이터베이스 초기화 실패: {e}")
        return False

def main():
    """메인 함수"""
    logger.info("🚀 벡터 데이터베이스 초기화 스크립트 시작")
    
    try:
        # 비동기 함수 실행
        success = asyncio.run(init_vector_database())
        
        if success:
            logger.info("🎉 벡터 데이터베이스 초기화 성공!")
            sys.exit(0)
        else:
            logger.error("💥 벡터 데이터베이스 초기화 실패!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ 사용자에 의해 중단됨")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 