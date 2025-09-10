from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from utils.responses import UTF8JSONResponse
from models.captcha_models import CaptchaGenerateResponse, CaptchaVerifyRequest, CaptchaVerifyResponse
from services.captcha_service import captcha_service
from db.captcha_repository import captcha_repository

router = APIRouter(
    prefix="/api/captcha",
    tags=["CAPTCHA"],
)

@router.get(
    "/generate",
    response_model=CaptchaGenerateResponse,
    summary="CAPTCHA 생성",
    description="새로운 오디오 CAPTCHA를 생성하고 ID와 오디오 파일 경로를 반환합니다.",
)
async def generate_captcha():
    """
    새로운 CAPTCHA를 생성합니다.
    - 고유한 CAPTCHA ID 생성
    - 랜덤 오디오 파일 선택
    - 정답을 서버에 저장 (일정 시간 후 만료)
    """
    try:
        captcha_id, audio_path = captcha_service.create_captcha()
        # 명시적 UTF-8 설정 및 ensure_ascii=False 적용
        payload = CaptchaGenerateResponse(captchaId=captcha_id, audioPath=audio_path).model_dump(by_alias=True)
        return UTF8JSONResponse(content=payload)
    except Exception as e:
        print(f"Error generating CAPTCHA: {e}")
        raise HTTPException(status_code=500, detail="CAPTCHA 생성에 실패했습니다.")

@router.post(
    "/verify",
    response_model=CaptchaVerifyResponse,
    summary="CAPTCHA 검증",
    description="사용자가 제출한 CAPTCHA 정답을 검증합니다.",
)
async def verify_captcha(request: CaptchaVerifyRequest):
    """
    CAPTCHA 정답을 검증합니다.
    - 제출된 CAPTCHA ID와 사용자 입력을 확인
    - 정답이 일치하면 성공, 그렇지 않으면 실패
    - 검증 후 해당 CAPTCHA는 무효화됨 (일회용)
    """
    try:
        is_valid = captcha_service.verify_captcha(request.captcha_id, request.user_input)
        if is_valid:
            payload = CaptchaVerifyResponse(success=True, message="CAPTCHA 인증에 성공했습니다.").model_dump()
            return UTF8JSONResponse(content=payload)
        else:
            payload = CaptchaVerifyResponse(success=False, message="CAPTCHA 인증에 실패했습니다.").model_dump()
            return UTF8JSONResponse(content=payload)
    except Exception as e:
        print(f"Error verifying CAPTCHA: {e}")
        raise HTTPException(status_code=500, detail="CAPTCHA 검증에 실패했습니다.")

@router.get(
    "/audio/{captcha_file_id}",
    summary="CAPTCHA 오디오 파일 제공",
    description="CAPTCHA 오디오 파일을 DB에서 읽어 반환합니다.",
)
async def get_captcha_audio(captcha_file_id: str):
    """
    CAPTCHA 오디오 파일을 반환합니다.
    """
    try:
        audio_data = captcha_repository.get_captcha_audio(captcha_file_id)
        if not audio_data:
            raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")
        
        audio_bytes, content_type = audio_data
        return Response(
            content=audio_bytes,
            media_type=content_type,
            headers={"Content-Disposition": f"inline; filename={captcha_file_id}.wav"}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving CAPTCHA audio: {e}")
        raise HTTPException(status_code=500, detail="오디오 파일 제공에 실패했습니다.")