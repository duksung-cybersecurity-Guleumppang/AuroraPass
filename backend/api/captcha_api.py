from fastapi import APIRouter, HTTPException, status
from models.captcha_models import (
    CaptchaGenerateResponse,
    CaptchaVerifyRequest,
    CaptchaVerifyResponse,
)
from services.captcha_service import captcha_service

router = APIRouter(
    prefix="/api/captcha",
    tags=["Captcha"],
)

@router.get(
    "/generate",
    response_model=CaptchaGenerateResponse,
    summary="오디오 CAPTCHA 생성",
    description="새로운 오디오 CAPTCHA와 고유 ID를 요청합니다.",
)
async def generate_captcha():
    """
    새로운 오디오 CAPTCHA를 생성하고, 고유 ID와 오디오 파일 경로를 반환합니다.
    """
    try:
        captcha_id, audio_path = captcha_service.create_captcha()
        return CaptchaGenerateResponse(captchaId=captcha_id, audioPath=audio_path)
    except Exception as e:
        # 실제 운영 환경에서는 로깅을 통해 에러를 기록해야 합니다.
        print(f"Error generating CAPTCHA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CAPTCHA 생성에 실패했습니다.",
        )

@router.post(
    "/verify",
    response_model=CaptchaVerifyResponse,
    summary="CAPTCHA 검증",
    description="사용자가 입력한 단어가 오디오 CAPTCHA의 정답과 일치하는지 검증합니다.",
)
async def verify_captcha(request: CaptchaVerifyRequest):
    """
    사용자가 제출한 CAPTCHA 정보를 검증합니다.
    """
    is_correct = captcha_service.verify_captcha(
        captcha_id=request.captcha_id, user_input=request.user_input
    )

    if is_correct:
        return CaptchaVerifyResponse(
            success=True, message="CAPTCHA 인증에 성공했습니다."
        )
    else:
        # 실패 응답 시에도 200 OK를 반환하고, 본문에 실패 정보를 담아 전달합니다.
        # 이는 API 명세에 따른 것입니다.
        return CaptchaVerifyResponse(
            success=False, message="입력한 내용이 올바르지 않거나 세션이 만료되었습니다."
        )
