from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api import captcha_api, user_api, courses_api

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
