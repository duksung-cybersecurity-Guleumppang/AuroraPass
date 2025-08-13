from pydantic import BaseModel, Field, EmailStr

class UserRegisterRequest(BaseModel):
    """
    사용자 가입 요청 모델
    """
    username: str = Field(..., description="사용할 아이디")
    password: str = Field(..., description="사용할 비밀번호")
    email: EmailStr = Field(..., description="사용자 이메일")
    captcha_id: str = Field(..., alias="captchaId", description="발급받은 CAPTCHA의 고유 식별자")
    user_input: str = Field(..., alias="userInput", description="사용자가 CAPTCHA 오디오를 듣고 입력한 정답")

class UserRegisterResponse(BaseModel):
    """
    사용자 가입 성공 응답 모델
    """
    user_id: str = Field(..., alias="userId", description="생성된 사용자의 고유 ID")
    username: str
    message: str
