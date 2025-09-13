import os
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import time
import threading

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from utils.responses import UTF8JSONResponse
from utils.logging import configure_logging, get_logger
from api import captcha_api, user_api, courses_api
from db.redis_client import ping_redis
from db.session import dispose_engine
from db.leader_lock import acquire_leader_lock, release_leader_lock, get_leader_status
from services.topup_scheduler import start_topup_scheduler, stop_topup_scheduler, join_topup_scheduler, get_topup_status
try:
    import psycopg2  # For readiness-only direct checks to avoid SQLAlchemy pre_ping/pool waits
except Exception:  # pragma: no cover
    psycopg2 = None

# Configure structured logging
configure_logging()
logger = get_logger("main")

# 환경 변수
DATABASE_URL = os.getenv("DATABASE_URL")
TOPUP_ENABLED = os.getenv("TOPUP_ENABLED", "0").lower() in ("1", "true", "yes", "on")
TOPUP_JOIN_TIMEOUT_SEC = int(os.getenv("TOPUP_JOIN_TIMEOUT_SEC", "25"))

# DB 엔진 (헬스체크용)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # readiness에서 연결/풀 대기 상한 적용
    connect_args={"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT_SEC", "1"))} if DATABASE_URL else {},
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT_SEC", "2")) if DATABASE_URL else None,
) if DATABASE_URL else None

# Readiness probe cache and thread
_readiness_cache: Dict[str, Any] = {"db": False, "redis": False, "updated_at": None}
_readiness_stop = threading.Event()
_readiness_thread: Optional[threading.Thread] = None

def _probe_db() -> bool:
    if not (DATABASE_URL and psycopg2):
        return False
    try:
        dsn = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
        # psycopg2/libpq는 정수 초를 기대하므로, 환경값이 "1.0"이어도 int로 변환
        conn_timeout = int(float(os.getenv("DB_CONNECT_TIMEOUT_SEC", "1")))
        conn = psycopg2.connect(dsn, connect_timeout=conn_timeout)
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute("SET statement_timeout=750")
                except Exception:
                    pass
                cur.execute("SELECT 1")
                row = cur.fetchone()
                return bool(row and row[0] == 1)
        finally:
            conn.close()
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False

def _probe_redis() -> bool:
    try:
        return ping_redis()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return False

def _readiness_loop(interval_sec: float = 1.0):
    logger.info("Readiness probe thread started")
    while not _readiness_stop.is_set():
        try:
            db_ok = _probe_db()
            redis_ok = _probe_redis()
            _readiness_cache["db"] = db_ok
            _readiness_cache["redis"] = redis_ok
            _readiness_cache["updated_at"] = time.time()
        except Exception as e:
            logger.error("Readiness probe loop error", error=str(e))
        # Sleep with stop check
        _readiness_stop.wait(interval_sec)
    logger.info("Readiness probe thread stopped")


def _parse_topup_enabled() -> bool:
    """TOPUP_ENABLED 환경변수 엄격 파싱"""
    raw_value = os.getenv("TOPUP_ENABLED", "0")
    enabled = raw_value.lower() in ("1", "true", "yes", "on")
    
    logger.info("Top-up scheduler environment gate", 
               raw_value=raw_value, 
               enabled=enabled)
    
    return enabled


def _check_required_schema() -> bool:
    """필수 스키마 점검 (captcha_files.used 컬럼/인덱스)"""
    if not engine:
        logger.warning("Database engine not available for schema check")
        return False
    
    try:
        with engine.connect() as conn:
            # captcha_files 테이블 존재 확인
            table_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'captcha_files'
                )
            """)).scalar()
            
            if not table_exists:
                logger.warning("Required table 'captcha_files' does not exist")
                return False
            
            # used 컬럼 존재 확인
            used_column_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'captcha_files' 
                    AND column_name = 'used'
                )
            """)).scalar()
            
            if not used_column_exists:
                logger.warning("Required column 'captcha_files.used' does not exist")
                return False
            
            # expires_at 컬럼 존재 확인
            expires_column_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'captcha_files' 
                    AND column_name = 'expires_at'
                )
            """)).scalar()
            
            if not expires_column_exists:
                logger.warning("Required column 'captcha_files.expires_at' does not exist")
                return False
            
            logger.info("Required schema validation passed")
            return True
            
    except Exception as e:
        logger.error("Schema validation failed", error=str(e))
        return False


def _ensure_captcha_data():
    """CAPTCHA 테이블 및 데이터 보장"""
    if not engine:
        return
    
    try:
        with engine.begin() as conn:
            # 테이블 존재 여부 확인 후 생성 (기본 컬럼만)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS captcha_files (
                  id varchar(40) PRIMARY KEY,
                  filename varchar(255) UNIQUE NOT NULL,
                  answer varchar(100) NOT NULL,
                  audio_data bytea NOT NULL,
                  content_type varchar(50) NOT NULL DEFAULT 'audio/wav',
                  created_at timestamptz NOT NULL DEFAULT now()
                )
            """))

            # 데이터 존재 여부 확인
            count = conn.execute(text("SELECT COUNT(*) FROM captcha_files")).scalar()
            if count and count > 0:
                logger.info("CAPTCHA data already exists", count=count)
                return

            # 파일 시스템에서 로드
            audio_dir = Path(__file__).parent / "static" / "audio"
            answers_path = audio_dir / "captcha_answers.json"
            
            if answers_path.exists():
                answers = json.loads(answers_path.read_text(encoding="utf-8"))
                loaded_count = 0
                
                for filename, answer in answers.items():
                    file_path = audio_dir / filename
                    if not file_path.exists():
                        continue
                    
                    audio_data = file_path.read_bytes()
                    conn.execute(text("""
                        INSERT INTO captcha_files (id, filename, answer, audio_data, content_type)
                        VALUES (:id, :filename, :answer, :audio_data, 'audio/wav')
                        ON CONFLICT (filename) DO NOTHING
                    """), {
                        "id": filename.replace(".wav", ""),
                        "filename": filename,
                        "answer": answer,
                        "audio_data": audio_data,
                    })
                    loaded_count += 1
                
                logger.info("CAPTCHA data loaded from filesystem", count=loaded_count)
            else:
                logger.warning("CAPTCHA answers file not found", path=str(answers_path))
            
            # 데모 사용자 생성 (없을 경우)
            demo_user_id = "12345678-1234-1234-1234-123456789012"
            user_count = conn.execute(text("SELECT COUNT(*) FROM users WHERE id = :id"), 
                                    {"id": demo_user_id}).scalar()
            if not user_count:
                conn.execute(text("""
                    INSERT INTO users (id, username, email, password_hash)
                    VALUES (:id, :username, :email, :password_hash)
                    ON CONFLICT (id) DO NOTHING
                """), {
                    "id": demo_user_id,
                    "username": "demo_user",
                    "email": "demo@example.com",
                    "password_hash": "demo_hash"
                })
                logger.info("Demo user created")
                
    except Exception as e:
        logger.error("Failed to ensure CAPTCHA data", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan: 시작/종료 단일 책임"""
    
    # === STARTUP ===
    logger.info("Application startup initiated")
    
    try:
        # 1. 기본 데이터 보장
        _ensure_captcha_data()
        
        # 2. 환경 게이트: TOPUP_ENABLED 파싱
        topup_enabled = _parse_topup_enabled()
        
        if not topup_enabled:
            logger.info("Top-up scheduler disabled by environment variable")
        else:
            # 3. 필수 스키마 확인
            schema_ok = _check_required_schema()
            
            if not schema_ok:
                logger.warning("Schema validation failed, scheduler will not start")
            else:
                # 4. 리더락 획득 시도
                leader_acquired = acquire_leader_lock()
                
                if leader_acquired:
                    logger.info("Leader lock acquired, starting scheduler")
                    
                    # 5. 스케줄러 시작
                    scheduler_started = start_topup_scheduler()
                    
                    if scheduler_started:
                        logger.info("Top-up scheduler started successfully")
                    else:
                        logger.error("Failed to start top-up scheduler")
                else:
                    logger.info("Failed to acquire leader lock, running as follower")
        
        logger.info("Application startup completed")
        # Start readiness probe background thread
        global _readiness_thread
        _readiness_stop.clear()
        _readiness_thread = threading.Thread(target=_readiness_loop, name="ReadinessProbe", daemon=True)
        _readiness_thread.start()
        
        # 애플리케이션 실행 중
        yield
        
    except Exception as e:
        logger.error("Application startup failed", error=str(e))
        yield  # 에러가 있어도 애플리케이션은 시작
    
    # === SHUTDOWN ===
    logger.info("Application shutdown initiated")
    
    try:
        # Stop readiness probe
        _readiness_stop.set()
        if _readiness_thread:
            _readiness_thread.join(timeout=2.0)
        # 1. 스케줄러 정지
        logger.info("Stopping top-up scheduler")
        stop_topup_scheduler()
        
        # 2. 스케줄러 종료 대기 (유한 시간)
        success = join_topup_scheduler(timeout=TOPUP_JOIN_TIMEOUT_SEC)
        
        if success:
            logger.info("Top-up scheduler stopped successfully")
        else:
            logger.warning("Top-up scheduler did not stop within timeout")
        
        # 3. 리더락 해제
        logger.info("Releasing leader lock")
        release_leader_lock()
        
        # 4. DB 엔진/풀 dispose
        logger.info("Disposing database engine")
        dispose_engine()
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error("Application shutdown failed", error=str(e))


# FastAPI 애플리케이션 생성 (lifespan 적용)
app = FastAPI(
    title="Rainbowwings Course Registration API",
    description="캡차가 적용된 수강신청 시스템의 API 명세서",
    version="1.0.0",
    default_response_class=UTF8JSONResponse,
    lifespan=lifespan
)

# API 라우터 등록
app.include_router(captcha_api.router)
app.include_router(user_api.router)
app.include_router(courses_api.router)

# 정적 파일 마운트 (CAPTCHA 오디오 파일 제공)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["Root"])
async def read_root():
    """루트 엔드포인트. API 서버가 실행 중인지 확인합니다."""
    return {"message": "Welcome to Rainbowwings Course Registration API"}


@app.get("/healthz", tags=["Health"]) 
async def healthz():
    """간단한 헬스체크 (항상 성공)"""
    return {"ok": True}


@app.get("/readyz", tags=["Health"]) 
def readyz() -> Dict[str, Any]:
    """상세 준비성 체크 (DB/Redis + 스케줄러/리더 상태 포함)"""
    logger.info("/readyz called")
    # Use cached probe results to avoid blocking readiness path
    db_ok = bool(_readiness_cache.get("db", False))
    redis_ok = bool(_readiness_cache.get("redis", False))
    
    # 최소 필드만 반환하여 레디니스 경로에서 어떤 잠재적 락도 피함
    overall_ok = db_ok and redis_ok
    payload = {
        "ok": overall_ok,
        "db": db_ok,
        "redis": redis_ok,
        "config": {
            "topup_enabled": TOPUP_ENABLED,
            "topup_join_timeout_sec": TOPUP_JOIN_TIMEOUT_SEC
        }
    }
    logger.info("/readyz responding", ok=overall_ok, db=db_ok, redis=redis_ok)
    return payload