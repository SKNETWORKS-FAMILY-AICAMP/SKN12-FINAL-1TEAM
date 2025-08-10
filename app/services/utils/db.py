from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models import Base
from app.config import settings

# 중앙화된 설정에서 데이터베이스 URL 가져오기
SQLALCHEMY_DATABASE_URL = settings.get_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 비동기 엔진과 세션 팩토리 추가
async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'))
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)

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

async def create_async_db_session():
    """새로운 비동기 데이터베이스 세션 생성 (비동기 컨텍스트 매니저용)"""
    return AsyncSessionLocal() 