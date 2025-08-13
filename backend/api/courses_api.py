from typing import List, Union
import time
from collections import deque, defaultdict

from fastapi import APIRouter, HTTPException, Path, status

from models.course_models import Course, CartAddRequest, EnrollResponse, CaptchaRequiredResponse
from models.captcha_models import CaptchaVerifyRequest
from services.course_service import course_service
from services.captcha_service import captcha_service

router = APIRouter(
    prefix="/api",
    tags=["Courses"],
)

# 비정상 접근 탐지 (간단한 슬라이딩 윈도우)
_attempt_window_secs = 3.0
_attempt_threshold = 5
_user_attempts = defaultdict(lambda: deque(maxlen=50))
_captcha_unlock_once = set()

def _rate_check_and_captcha(user_id: str):
    now = time.time()
    dq = _user_attempts[user_id]
    while dq and now - dq[0] > _attempt_window_secs:
        dq.popleft()
    dq.append(now)
    if len(dq) >= _attempt_threshold:
        captcha_id, audio_path = captcha_service.create_captcha()
        return {"requireCaptcha": True, "captcha": {"captchaId": captcha_id, "audioPath": audio_path}}
    return None


@router.get("/courses", summary="강의 목록 조회")
async def get_courses():
    user_id = "demo-user"
    cap = _rate_check_and_captcha(user_id)
    if cap:
        return cap
    return course_service.list_courses()


@router.get("/cart", summary="장바구니 조회")
async def get_cart():
    # 데모에서는 고정 사용자 사용
    user_id = "demo-user"
    cap = _rate_check_and_captcha(user_id)
    if cap:
        return cap
    return course_service.get_cart(user_id)


@router.post("/cart", summary="장바구니 추가")
async def add_cart(body: CartAddRequest):
    user_id = "demo-user"
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
    user_id = "demo-user"
    cap = _rate_check_and_captcha(user_id)
    if cap:
        return cap
    course_service.remove_from_cart(user_id, courseId)
    return {"success": True}


@router.post("/enroll", response_model=Union[EnrollResponse, CaptchaRequiredResponse], summary="수강신청")
async def enroll():
    user_id = "demo-user"

    # 캡차 통과 임시 허용이 있으면 1회 소진
    if user_id in _captcha_unlock_once:
        _captcha_unlock_once.discard(user_id)
    else:
        now = time.time()
        dq = _user_attempts[user_id]
        # 최근 윈도우 내 시도만 유지
        while dq and now - dq[0] > _attempt_window_secs:
            dq.popleft()
        dq.append(now)
        if len(dq) >= _attempt_threshold:
            # 캡차 요구 응답
            captcha_id, audio_path = captcha_service.create_captcha()
            return CaptchaRequiredResponse(requireCaptcha=True, captcha={"captchaId": captcha_id, "audioPath": audio_path})

    results = course_service.enroll(user_id)
    return EnrollResponse(results=results)


@router.get("/my-courses", summary="신청 결과 조회")
async def my_courses():
    user_id = "demo-user"
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
    user_id = "demo-user"
    ok = captcha_service.verify_captcha(captcha_id=body.captcha_id, user_input=body.user_input)
    if not ok:
        return {"success": False, "message": "CAPTCHA 인증 실패"}
    _captcha_unlock_once.add(user_id)
    return {"success": True, "message": "CAPTCHA 인증 성공, 1회 신청 가능"}


