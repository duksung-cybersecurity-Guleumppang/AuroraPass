from pydantic import BaseModel, Field
from typing import Optional
import uuid

class CaptchaGenerateResponse(BaseModel):
    """
    CAPTCHA 생성 요청에 대한 응답 모델
    """
    captcha_id: str = Field(..., alias="captchaId", description="생성된 CAPTCHA의 고유 식별자")
    audio_path: str = Field(..., alias="audioPath", description="재생할 오디오 파일의 경로")

class CaptchaVerifyRequest(BaseModel):
    """
    CAPTCHA 검증 요청 모델
    """
    captcha_id: str = Field(..., alias="captchaId", description="발급받은 CAPTCHA의 고유 식별자")
    user_input: str = Field(..., alias="userInput", description="사용자가 오디오를 듣고 입력한 단어")

class CaptchaVerifyResponse(BaseModel):
    """
    CAPTCHA 검증 요청에 대한 응답 모델
    """
    success: bool
    message: str
