from typing import List, Union
from fastapi import APIRouter, HTTPException, Path, status, Query
from typing import Optional

from models.course_models import Course, CartAddRequest, EnrollResponse, CaptchaRequiredResponse
from models.captcha_models import CaptchaVerifyRequest
from services.course_service import course_service
from services.captcha_service import captcha_service
from db.redis_client import increment_user_attempts, get_user_attempts, check_captcha_unlock, consume_captcha_unlock, grant_captcha_unlock

router = APIRouter(
    prefix="/api",
    tags=["Courses"],
)

# Rate limiting configuration
_attempt_window_secs = 3
_attempt_threshold = 5

def _rate_check_and_captcha(user_id: str):
    attempts = increment_user_attempts(user_id, ttl_seconds=_attempt_window_secs)
    if attempts >= _attempt_threshold:
        captcha_id, audio_path = captcha_service.create_captcha()
        return {"requireCaptcha": True, "captcha": {"captchaId": captcha_id, "audioPath": audio_path}}
    return None


@router.get("/courses", summary="강의 목록 조회")
async def get_courses(
    keyword: Optional[str] = Query(None, description="과목명 키워드(부분 일치)"),
    year: Optional[int] = Query(None, description="학년도"),
    semester: Optional[int] = Query(None, ge=1, le=2, description="학기: 1|2"),
    level: Optional[str] = Query(None, description="교과목 수준(학사|석사)"),
    category: Optional[str] = Query(None, description="이수구분(전필|전선|교양)"),
    department: Optional[str] = Query(None, description="개설전공/학과"),
    page: Optional[int] = Query(None, ge=1, description="페이지 번호(1-base)"),
    pageSize: Optional[int] = Query(None, ge=1, le=100, description="페이지 크기(최대 100)"),
    sort: Optional[str] = Query(None, pattern="^(recent|name|code)$", description="정렬 키: recent|name|code"),
    order: Optional[str] = Query(None, pattern="^(asc|desc)$", description="정렬 순서: asc|desc"),
):
    user_id = "12345678-1234-1234-1234-123456789012"  # demo-user UUID
    cap = _rate_check_and_captcha(user_id)
    if cap:
        return cap
    return course_service.list_courses(
        keyword=keyword,
        year=year,
        semester=semester,
        level=level,
        category=category,
        department=department,
        page=page,
        page_size=pageSize,
        sort=sort,
        order=order,
    )


@router.get("/cart", summary="장바구니 조회")
async def get_cart():
    # 데모에서는 고정 사용자 사용
    user_id = "12345678-1234-1234-1234-123456789012"  # demo-user UUID
    cap = _rate_check_and_captcha(user_id)
    if cap:
        return cap
    return course_service.get_cart(user_id)


@router.post("/cart", summary="장바구니 추가")
async def add_cart(body: CartAddRequest):
    user_id = "12345678-1234-1234-1234-123456789012"  # demo-user UUID
    cap = _rate_check_and_captcha(user_id)
    if cap:
        return cap
    try:
        course_service.add_to_cart(user_id, body.course_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True}


@router.delete("/cart/{courseId}", summary="장바구니 제거")
async def remove_cart(courseId: str = Path(..., description="강의 ID")):
    user_id = "12345678-1234-1234-1234-123456789012"  # demo-user UUID
    cap = _rate_check_and_captcha(user_id)
    if cap:
        return cap
    course_service.remove_from_cart(user_id, courseId)
    return {"success": True}


@router.post("/enroll", response_model=Union[EnrollResponse, CaptchaRequiredResponse], summary="수강신청")
async def enroll():
    user_id = "12345678-1234-1234-1234-123456789012"  # demo-user UUID

    # 캡차 통과 임시 허용이 있으면 1회 소진
    if check_captcha_unlock(user_id):
        consume_captcha_unlock(user_id)
    else:
        attempts = increment_user_attempts(user_id, ttl_seconds=_attempt_window_secs)
        if attempts >= _attempt_threshold:
            # 캡차 요구 응답
            captcha_id, audio_path = captcha_service.create_captcha()
            return CaptchaRequiredResponse(requireCaptcha=True, captcha={"captchaId": captcha_id, "audioPath": audio_path})

    results = course_service.enroll(user_id)
    return EnrollResponse(results=results)


@router.get("/my-courses", summary="신청 결과 조회")
async def my_courses():
    user_id = "12345678-1234-1234-1234-123456789012"  # demo-user UUID
    cap = _rate_check_and_captcha(user_id)
    if cap:
        return cap
    return course_service.my_courses(user_id)


@router.post("/enroll/unlock", summary="CAPTCHA 통과 후 일시적 신청 허용")
async def unlock_after_captcha(body: CaptchaVerifyRequest):
    """
    프론트에서 모달로 받은 captchaId/userInput을 제출하면 서버에서 검증 후
    해당 사용자에게 1회 신청을 허용합니다.
    """
    user_id = "12345678-1234-1234-1234-123456789012"  # demo-user UUID
    ok = captcha_service.verify_captcha(captcha_id=body.captcha_id, user_input=body.user_input)
    if not ok:
        return {"success": False, "message": "CAPTCHA 인증 실패"}
    grant_captcha_unlock(user_id, ttl_seconds=30)
    return {"success": True, "message": "CAPTCHA 인증 성공, 1회 신청 가능"}


@router.get("/departments", summary="개설전공/학과 목록")
async def list_departments(
    year: Optional[int] = Query(None, description="학년도"),
    semester: Optional[int] = Query(None, ge=1, le=2, description="학기: 1|2"),
):
    return course_service.list_departments(year=year, semester=semester)


@router.delete("/enroll/{courseId}", summary="수강취소")
async def cancel_enrollment(courseId: str = Path(..., description="강의 ID")):
    user_id = "12345678-1234-1234-1234-123456789012"  # demo-user UUID
    cap = _rate_check_and_captcha(user_id)
    if cap:
        return cap
    success = course_service.cancel_enrollment(user_id, courseId)
    if not success:
        raise HTTPException(status_code=404, detail="수강신청 내역을 찾을 수 없습니다.")
    return {"success": True, "message": "수강취소가 완료되었습니다."}

