from typing import List

from fastapi import APIRouter, HTTPException, Path, status

from models.course_models import Course, CartAddRequest, EnrollResponse
from services.course_service import course_service

router = APIRouter(
    prefix="/api",
    tags=["Courses"],
)


@router.get("/courses", response_model=List[Course], summary="강의 목록 조회")
async def get_courses():
    return course_service.list_courses()


@router.get("/cart", response_model=List[Course], summary="장바구니 조회")
async def get_cart():
    # 데모에서는 고정 사용자 사용
    user_id = "demo-user"
    return course_service.get_cart(user_id)


@router.post("/cart", status_code=status.HTTP_204_NO_CONTENT, summary="장바구니 추가")
async def add_cart(body: CartAddRequest):
    user_id = "demo-user"
    try:
        course_service.add_to_cart(user_id, body.course_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cart/{courseId}", status_code=status.HTTP_204_NO_CONTENT, summary="장바구니 제거")
async def remove_cart(courseId: str = Path(..., description="강의 ID")):
    user_id = "demo-user"
    course_service.remove_from_cart(user_id, courseId)


@router.post("/enroll", response_model=EnrollResponse, summary="수강신청")
async def enroll():
    user_id = "demo-user"
    results = course_service.enroll(user_id)
    return EnrollResponse(results=results)


@router.get("/my-courses", response_model=List[Course], summary="신청 결과 조회")
async def my_courses():
    user_id = "demo-user"
    return course_service.my_courses(user_id)


