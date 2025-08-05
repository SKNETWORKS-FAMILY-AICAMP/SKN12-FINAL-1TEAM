from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.config import settings

# 중앙화된 설정에서 데이터베이스 URL 가져오기
SQLALCHEMY_DATABASE_URL = settings.get_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_with_transaction():
    """트랜잭션 관리가 포함된 데이터베이스 세션"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def create_db_session():
    """새로운 데이터베이스 세션 생성 (컨텍스트 매니저용)"""
    return SessionLocal() 