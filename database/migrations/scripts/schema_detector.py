#!/usr/bin/env python3
"""
스키마 변경 감지 스크립트
현재 데이터베이스 스키마와 모델 정의를 비교하여 변경사항을 감지합니다.
"""

import os
import sys
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker
import logging

# Docker 환경 설정
sys.path.append('/app')
from app.models import Base
from app.config.settings import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaDetector:
    def __init__(self):
        self.engine = None
        self.inspector = None
        self.setup_database_connection()
    
    def setup_database_connection(self):
        """데이터베이스 연결 설정"""
        try:
            database_url = settings.get_database_url()
            self.engine = sa.create_engine(database_url)
            self.inspector = inspect(self.engine)
            logger.info("✅ 데이터베이스 연결 성공")
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    def get_current_tables(self):
        """현재 데이터베이스의 테이블 목록 조회"""
        try:
            tables = self.inspector.get_table_names()
            logger.info(f"현재 DB 테이블: {tables}")
            return set(tables)
        except Exception as e:
            logger.error(f"❌ 테이블 목록 조회 실패: {e}")
            return set()
    
    def get_model_tables(self):
        """모델에서 정의된 테이블 목록 조회"""
        try:
            model_tables = set(Base.metadata.tables.keys())
            logger.info(f"모델 테이블: {model_tables}")
            return model_tables
        except Exception as e:
            logger.error(f"❌ 모델 테이블 조회 실패: {e}")
            return set()
    
    def compare_schemas(self):
        """스키마 비교 및 변경사항 감지"""
        current_tables = self.get_current_tables()
        model_tables = self.get_model_tables()
        
        # 새로 추가된 테이블
        new_tables = model_tables - current_tables
        # 삭제된 테이블
        removed_tables = current_tables - model_tables
        
        # 컬럼 변경사항도 감지
        column_changes = self.check_column_changes()
        
        changes = {
            'new_tables': list(new_tables),
            'removed_tables': list(removed_tables),
            'column_changes': column_changes,
            'has_changes': len(new_tables) > 0 or len(removed_tables) > 0 or len(column_changes) > 0
        }
        
        if changes['has_changes']:
            logger.info("📝 스키마 변경사항 감지됨!")
            if new_tables:
                logger.info(f"➕ 새 테이블: {new_tables}")
            if removed_tables:
                logger.info(f"➖ 삭제된 테이블: {removed_tables}")
            if column_changes:
                logger.info(f"🔄 컬럼 변경: {column_changes}")
        else:
            logger.info("✅ 스키마 변경사항 없음")
        
        return changes
    
    def check_column_changes(self):
        """컬럼 변경사항 감지 (고급 기능)"""
        changes = []
        current_tables = self.get_current_tables()
        
        for table_name in current_tables:
            if table_name in Base.metadata.tables:
                # 현재 DB의 컬럼 정보
                db_columns = {col['name']: col for col in self.inspector.get_columns(table_name)}
                
                # 모델의 컬럼 정보
                model_table = Base.metadata.tables[table_name]
                model_columns = {col.name: col for col in model_table.columns}
                
                # 새 컬럼 감지
                new_columns = set(model_columns.keys()) - set(db_columns.keys())
                if new_columns:
                    changes.append({
                        'table': table_name,
                        'type': 'new_columns',
                        'columns': list(new_columns)
                    })
        
        return changes

def main():
    """메인 실행 함수"""
    try:
        detector = SchemaDetector()
        schema_changes = detector.compare_schemas()
        column_changes = detector.check_column_changes()
        
        # 결과 출력
        print("\n" + "="*50)
        print("🔍 스키마 변경 감지 결과")
        print("="*50)
        
        if schema_changes['has_changes']:
            print("📝 스키마 변경사항이 감지되었습니다!")
            if schema_changes['new_tables']:
                print(f"➕ 새 테이블: {schema_changes['new_tables']}")
            if schema_changes['removed_tables']:
                print(f"➖ 삭제된 테이블: {schema_changes['removed_tables']}")
        else:
            print("✅ 스키마 변경사항이 없습니다.")
        
        if column_changes:
            print("\n📊 컬럼 변경사항:")
            for change in column_changes:
                print(f"  테이블 '{change['table']}': {change['columns']}")
        
        # 종료 코드 설정 (변경사항이 있으면 1, 없으면 0)
        exit_code = 1 if schema_changes['has_changes'] or column_changes else 0
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"❌ 스키마 감지 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 