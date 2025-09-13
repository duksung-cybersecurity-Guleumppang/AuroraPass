import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Optional
from utils.logging import get_logger

logger = get_logger("db.session")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set; please provide it via .env or environment variables."
    )

# 환경변수로 풀 파라미터 설정
POOL_SIZE = int(os.getenv("POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW", "10"))
POOL_RECYCLE_SEC = int(os.getenv("POOL_RECYCLE_SEC", "1800"))  # 30분
POOL_PRE_PING = os.getenv("POOL_PRE_PING", "1").lower() in ("1", "true", "yes", "on")

# DB 쿼리 타임아웃 (밀리초)
DB_STATEMENT_TIMEOUT_MS = int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "2000"))

# 엔진 생성 (풀 파라미터 적용)
engine = create_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_recycle=POOL_RECYCLE_SEC,
    pool_pre_ping=POOL_PRE_PING,
    echo=False  # SQL 로깅은 필요시 환경변수로 제어 가능
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger.info("Database engine configured", 
           pool_size=POOL_SIZE, 
           max_overflow=MAX_OVERFLOW, 
           pool_recycle=POOL_RECYCLE_SEC,
           pool_pre_ping=POOL_PRE_PING,
           statement_timeout_ms=DB_STATEMENT_TIMEOUT_MS)


@contextmanager
def get_db_session():
    """Database session context manager with statement timeout"""
    session = SessionLocal()
    try:
        # 세션 진입 시 statement timeout 설정
        session.execute(text(f"SET LOCAL statement_timeout = '{DB_STATEMENT_TIMEOUT_MS}ms'"))
        
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager 
def get_db_session_with_timeout(timeout_ms: Optional[int] = None):
    """Database session context manager with custom timeout"""
    session = SessionLocal()
    effective_timeout = timeout_ms or DB_STATEMENT_TIMEOUT_MS
    
    try:
        # 커스텀 타임아웃 설정
        session.execute(text(f"SET LOCAL statement_timeout = '{effective_timeout}ms'"))
        
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """FastAPI dependency for database session"""
    with get_db_session() as session:
        yield session


def create_dedicated_connection(database_url: Optional[str] = None):
    """전용 커넥션 생성 (풀 미사용, 리더락 등에 사용)"""
    url = database_url or DATABASE_URL
    return create_engine(url, poolclass=None).connect()


def dispose_engine():
    """엔진 및 커넥션 풀 정리 (lifespan shutdown에서 호출)"""
    try:
        engine.dispose()
        logger.info("Database engine disposed successfully")
    except Exception as e:
        logger.error("Failed to dispose database engine", error=str(e))
