import json
import os
from typing import Dict, List

from models.course_models import Course, EnrollResult


def _load_demo_courses() -> List[Course]:
    demo_path = os.path.join(os.path.dirname(__file__), "..", "static", "demo", "courses.json")
    demo_path = os.path.abspath(demo_path)
    with open(demo_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Course(**c) for c in data]


class CourseService:
    def __init__(self) -> None:
        # 데모 데이터 로드 (메모리에 유지)
        self.courses: Dict[str, Course] = {c.course_id: c for c in _load_demo_courses()}
        # 간단 장바구니/신청 상태(인메모리)
        self.user_cart: Dict[str, List[str]] = {}
        self.user_enrolled: Dict[str, List[str]] = {}

    def list_courses(self) -> List[Course]:
        return list(self.courses.values())

    def get_cart(self, user_id: str) -> List[Course]:
        course_ids = self.user_cart.get(user_id, [])
        return [self.courses[cid] for cid in course_ids if cid in self.courses]

    def add_to_cart(self, user_id: str, course_id: str) -> None:
        if course_id not in self.courses:
            raise ValueError("존재하지 않는 강의입니다.")
        cart = self.user_cart.setdefault(user_id, [])
        if course_id not in cart:
            cart.append(course_id)

    def remove_from_cart(self, user_id: str, course_id: str) -> None:
        cart = self.user_cart.setdefault(user_id, [])
        if course_id in cart:
            cart.remove(course_id)

    def enroll(self, user_id: str) -> List[EnrollResult]:
        results: List[EnrollResult] = []
        cart = self.user_cart.get(user_id, [])
        enrolled_list = self.user_enrolled.setdefault(user_id, [])
        for cid in cart:
            course = self.courses.get(cid)
            if not course:
                results.append(EnrollResult(courseId=cid, success=False, reason="강의 없음"))
                continue
            if course.enrolled >= course.capacity:
                results.append(EnrollResult(courseId=cid, success=False, reason="정원 초과"))
                continue
            if cid in enrolled_list:
                results.append(EnrollResult(courseId=cid, success=False, reason="이미 신청됨"))
                continue
            # 간단 신청 처리
            course.enrolled += 1
            enrolled_list.append(cid)
            results.append(EnrollResult(courseId=cid, success=True))

        # 신청 후 장바구니 비우기
        self.user_cart[user_id] = []
        return results

    def my_courses(self, user_id: str) -> List[Course]:
        enrolled_ids = self.user_enrolled.get(user_id, [])
        return [self.courses[cid] for cid in enrolled_ids if cid in self.courses]


course_service = CourseService()

