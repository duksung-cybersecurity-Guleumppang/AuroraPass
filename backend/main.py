from fastapi import FastAPI
from utils.responses import UTF8JSONResponse
from fastapi.staticfiles import StaticFiles
from api import captcha_api, user_api, courses_api
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from pathlib import Path
from db.redis_client import ping_redis
from utils.logging import configure_logging, get_logger
from services.topup_scheduler import start_topup_scheduler

# Configure structured logging
configure_logging()
logger = get_logger("main")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Rainbowwings Course Registration API",
    description="캡차가 적용된 수강신청 시스템의 API 명세서",
    version="1.0.0",
    default_response_class=UTF8JSONResponse,
)

# API 라우터 등록
app.include_router(captcha_api.router)
app.include_router(user_api.router)
app.include_router(courses_api.router)

# 정적 파일 마운트 (CAPTCHA 오디오 파일 제공)
# /static 경로로 오는 요청을 static 폴더에서 찾도록 설정합니다.
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", tags=["Root"])
async def read_root():
    """
    루트 엔드포인트. API 서버가 실행 중인지 확인합니다.
    """
    return {"message": "Welcome to Rainbowwings Course Registration API"}


# Health/Ready endpoints
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None


@app.get("/healthz", tags=["Health"]) 
async def healthz():
    return {"ok": True}


@app.get("/readyz", tags=["Health"]) 
async def readyz():
    db_ok = False
    redis_ok = False
    
    # Check database
    if engine is not None:
        try:
            with engine.connect() as conn:
                db_ok = conn.execute(text("select 1")).scalar() == 1
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
    
    # Check Redis
    try:
        redis_ok = ping_redis()
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
    
    overall_ok = db_ok and redis_ok
    
    return {
        "db": db_ok,
        "redis": redis_ok,
        "ok": overall_ok
    }


@app.on_event("startup")
def ensure_captcha_table_and_seed():
    """
    컨테이너가 초기화된 상태(볼륨 비어있음)에서 시작할 때
    - captcha_files 테이블이 없으면 생성
    - 비어 있으면 static/audio 의 파일과 정답을 DB에 로드
    """
    if engine is None:
        return
    try:
        with engine.begin() as conn:
            # 테이블 존재 여부 확인 후 생성
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS captcha_files (
                  id varchar(40) PRIMARY KEY,
                  filename varchar(255) UNIQUE NOT NULL,
                  answer varchar(100) NOT NULL,
                  audio_data bytea NOT NULL,
                  content_type varchar(50) NOT NULL DEFAULT 'audio/wav',
                  created_at timestamptz NOT NULL DEFAULT now()
                )
                """
            ))

            # 데이터 존재 여부 확인
            count = conn.execute(text("SELECT COUNT(*) FROM captcha_files")).scalar()
            if count and count > 0:
                return

            # 파일 시스템에서 로드
            audio_dir = Path(__file__).parent / "static" / "audio"
            answers_path = audio_dir / "captcha_answers.json"
            import json
            if answers_path.exists():
                answers = json.loads(answers_path.read_text(encoding="utf-8"))
                for filename, answer in answers.items():
                    file_path = audio_dir / filename
                    if not file_path.exists():
                        continue
                    audio_data = file_path.read_bytes()
                    conn.execute(text(
                        """
                        INSERT INTO captcha_files (id, filename, answer, audio_data, content_type)
                        VALUES (:id, :filename, :answer, :audio_data, 'audio/wav')
                        ON CONFLICT (filename) DO NOTHING
                        """
                    ), {
                        "id": filename.replace(".wav", ""),
                        "filename": filename,
                        "answer": answer,
                        "audio_data": audio_data,
                    })
            logger.info("captcha_files ensured and seeded if empty")
            
            # 데모 사용자 생성 (없을 경우)
            demo_user_id = "12345678-1234-1234-1234-123456789012"
            user_count = conn.execute(text("SELECT COUNT(*) FROM users WHERE id = :id"), {"id": demo_user_id}).scalar()
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
        logger.error("Failed to ensure/seed captcha_files and demo user", error=str(e))


@app.on_event("startup")
def start_background_topup_scheduler():
    """API 프로세스에서 Top-up 스케줄러를 시작한다(부팅 스크립트 종료 후에도 지속)."""
    try:
        start_topup_scheduler()
        logger.info("Background Top-up scheduler started from API process")
    except Exception as e:
        logger.error("Failed to start Top-up scheduler from API process", error=str(e))
