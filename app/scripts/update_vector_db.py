#!/usr/bin/env python3
"""
벡터 데이터베이스 업데이트 스크립트
기존 테이블 설명을 수정하거나 새로 추가할 수 있습니다.

사용법:
    # 모든 테이블 설명 강제 업데이트
    docker exec -it fastapi-app python /app/app/scripts/update_vector_db.py --refresh-all
    
    # 특정 테이블만 업데이트
    docker exec -it fastapi-app python /app/app/scripts/update_vector_db.py --table employees
    
    # 특정 테이블 삭제
    docker exec -it fastapi-app python /app/app/scripts/update_vector_db.py --delete employees
"""

import asyncio
import sys
import argparse
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

async def refresh_all_descriptions():
    """모든 테이블 설명을 강제 업데이트"""
    try:
        from app.services.core.vector_similarity_service import vector_similarity_service
        from app.services.utils.db import AsyncSessionLocal
        from app.config.table_descriptions_loader import load_table_descriptions
        
        logger.info("🔄 모든 테이블 설명 새로 고침 시작...")
        
        # JSON에서 테이블 설명 로드
        table_descriptions = load_table_descriptions()
        
        # 비동기 데이터베이스 세션 생성
        async with AsyncSessionLocal() as session:
            # 모든 테이블 설명 새로 고침
            success = await vector_similarity_service.refresh_all_table_descriptions(
                session, table_descriptions
            )
            
            if success:
                logger.info("✅ 모든 테이블 설명 새로 고침 완료")
                return True
            else:
                logger.error("❌ 일부 테이블 설명 새로 고침 실패")
                return False
            
    except Exception as e:
        logger.error(f"❌ 테이블 설명 새로 고침 실패: {e}")
        return False

async def update_single_table(table_name: str):
    """특정 테이블 설명만 업데이트"""
    try:
        from app.services.core.vector_similarity_service import vector_similarity_service
        from app.services.utils.db import AsyncSessionLocal
        from app.config.table_descriptions_loader import load_table_descriptions
        
        logger.info(f"🔄 테이블 '{table_name}' 설명 업데이트 시작...")
        
        # JSON에서 테이블 설명 로드
        table_descriptions = load_table_descriptions()
        
        if table_name not in table_descriptions:
            logger.error(f"❌ 테이블 '{table_name}'을 JSON 파일에서 찾을 수 없음")
            return False
        
        # 비동기 데이터베이스 세션 생성
        async with AsyncSessionLocal() as session:
            info = table_descriptions[table_name]
            success = await vector_similarity_service.update_table_description(
                session, 
                table_name,
                info['description'],
                info['columns'],
                info['sample_data']
            )
            
            if success:
                logger.info(f"✅ 테이블 '{table_name}' 설명 업데이트 완료")
                return True
            else:
                logger.error(f"❌ 테이블 '{table_name}' 설명 업데이트 실패")
                return False
            
    except Exception as e:
        logger.error(f"❌ 테이블 '{table_name}' 설명 업데이트 실패: {e}")
        return False

async def delete_table_description(table_name: str):
    """특정 테이블 설명을 삭제"""
    try:
        from app.services.core.vector_similarity_service import vector_similarity_service
        from app.services.utils.db import AsyncSessionLocal
        
        logger.info(f"🗑️ 테이블 '{table_name}' 설명 삭제 시작...")
        
        # 비동기 데이터베이스 세션 생성
        async with AsyncSessionLocal() as session:
            success = await vector_similarity_service.delete_table_description(
                session, table_name
            )
            
            if success:
                logger.info(f"✅ 테이블 '{table_name}' 설명 삭제 완료")
                return True
            else:
                logger.error(f"❌ 테이블 '{table_name}' 설명 삭제 실패")
                return False
            
    except Exception as e:
        logger.error(f"❌ 테이블 '{table_name}' 설명 삭제 실패: {e}")
        return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='벡터 데이터베이스 업데이트 스크립트')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--refresh-all', action='store_true', help='모든 테이블 설명 강제 업데이트')
    group.add_argument('--table', type=str, help='특정 테이블만 업데이트')
    group.add_argument('--delete', type=str, help='특정 테이블 설명 삭제')
    
    args = parser.parse_args()
    
    logger.info("🚀 벡터 데이터베이스 업데이트 스크립트 시작")
    
    try:
        success = False
        
        if args.refresh_all:
            success = asyncio.run(refresh_all_descriptions())
        elif args.table:
            success = asyncio.run(update_single_table(args.table))
        elif args.delete:
            success = asyncio.run(delete_table_description(args.delete))
        
        if success:
            logger.info("🎉 벡터 데이터베이스 업데이트 성공!")
            sys.exit(0)
        else:
            logger.error("💥 벡터 데이터베이스 업데이트 실패!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ 사용자에 의해 중단됨")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()