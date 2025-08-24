from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api import captcha_api, user_api, courses_api
import os
from sqlalchemy import create_engine, text
from db.redis_client import ping_redis
from utils.logging import configure_logging, get_logger

# Configure structured logging
configure_logging()
logger = get_logger("main")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Rainbowwings Course Registration API",
    description="캡차가 적용된 수강신청 시스템의 API 명세서",
    version="1.0.0",
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
