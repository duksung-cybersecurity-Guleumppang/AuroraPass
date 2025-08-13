from typing import List, Optional
from pydantic import BaseModel, Field
try:
    # pydantic v2
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    ConfigDict = dict  # type: ignore


class Course(BaseModel):
    """
    강의 정보 응답 모델
    """
    course_id: str = Field(..., alias="courseId")
    title: str
    professor: str
    schedule: str
    capacity: int
    enrolled: int

    try:
        model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)  # type: ignore
    except Exception:  # pydantic v1 fallback
        class Config:  # type: ignore
            allow_population_by_field_name = True
            fields = {}


class CartAddRequest(BaseModel):
    """
    장바구니 추가 요청
    """
    course_id: str = Field(..., alias="courseId")


class EnrollResult(BaseModel):
    course_id: str = Field(..., alias="courseId")
    success: bool
    reason: Optional[str] = None


class EnrollResponse(BaseModel):
    """
    수강신청 결과
    """
    results: List[EnrollResult]


class CaptchaInfo(BaseModel):
    captcha_id: str = Field(..., alias="captchaId")
    audio_path: str = Field(..., alias="audioPath")
    try:
        model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)  # type: ignore
    except Exception:  # pydantic v1 fallback
        class Config:  # type: ignore
            allow_population_by_field_name = True
            fields = {}


class CaptchaRequiredResponse(BaseModel):
    require_captcha: bool = Field(..., alias="requireCaptcha")
    captcha: CaptchaInfo
    try:
        model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)  # type: ignore
    except Exception:  # pydantic v1 fallback
        class Config:  # type: ignore
            allow_population_by_field_name = True
            fields = {}

