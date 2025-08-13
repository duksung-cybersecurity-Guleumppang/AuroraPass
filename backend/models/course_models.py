from typing import List, Optional
from pydantic import BaseModel, Field


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

    class Config:
        populate_by_name = True


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

