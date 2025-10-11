import json
import os
from typing import Dict, List, Optional
from models.course_models import Course, EnrollResult
from repositories.course_repository import course_repository


def _load_demo_courses() -> List[Course]:
    """Load demo courses from curated JSON if present, else fallback to default"""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "demo"))
    # Allow ENV override
    env_override = os.environ.get("CURATED_COURSES_JSON")
    candidate_paths = []
    if env_override:
        candidate_paths.append(env_override)
    candidate_paths.append(os.path.join(base_dir, "courses_curated.json"))
    candidate_paths.append(os.path.join(base_dir, "courses.json"))

    path_to_use = None
    for p in candidate_paths:
        try:
            if os.path.exists(p):
                path_to_use = p
                break
        except Exception:
            continue

    if not path_to_use:
        return []

    with open(path_to_use, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Course(**c) for c in data]


class CourseService:
    def __init__(self) -> None:
        # Demo data fallback for course info (title, professor, schedule)
        self.demo_courses: Dict[str, Course] = {c.course_id: c for c in _load_demo_courses()}
        # curated 전용 사용: demo_courses에 있는 코스만 노출
        self.curated_ids = set(self.demo_courses.keys())

    def list_courses(
        self,
        *,
        keyword: Optional[str] = None,
        year: Optional[int] = None,
        semester: Optional[int] = None,
        level: Optional[str] = None,
        category: Optional[str] = None,
        department: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
    ) -> List[Course]:
        """Get courses with optional filter/pagination, merge demo fields for display"""
        limit = None
        offset = None
        if page and page_size:
            page = max(1, page)
            page_size = min(max(1, page_size), 100)
            limit = page_size
            offset = (page - 1) * page_size

        db_courses = course_repository.get_courses_filtered(
            keyword=keyword,
            year=year,
            semester=semester,
            level=level,
            category=category,
            department=department,
            sort=sort,
            order=order,
            limit=limit,
            offset=offset,
        )
        
        # Merge with demo data for display
        result = []
        for db_course in db_courses:
            # curated에 없는 과목은 제외
            if db_course["id"] not in self.curated_ids:
                continue
            demo_course = self.demo_courses.get(db_course["id"])
            if demo_course:
                # Use DB data for capacity/enrolled, demo data for title/professor/schedule
                course_data = Course(
                    course_id=db_course["id"],
                    title=demo_course.title,
                    professor=getattr(demo_course, 'professor', 'Unknown'),
                    schedule=getattr(demo_course, 'schedule', 'TBA'),
                    capacity=db_course["capacity"],
                    enrolled=db_course["enrolled_count"],
                    theoryHours=db_course.get("theory_hours") or getattr(demo_course, 'theory_hours', None) or 3,
                    practiceHours=db_course.get("practice_hours") or getattr(demo_course, 'practice_hours', None) or 1,
                    department=db_course.get("department"),
                    year=db_course.get("year"),
                    semester=db_course.get("semester"),
                    level=db_course.get("level"),
                    category=db_course.get("category"),
                )
            else:
                # Fallback to DB-only data if demo not available
                course_data = Course(
                    course_id=db_course["id"],
                    title=db_course.get("title", "Untitled"),
                    professor='Unknown',
                    schedule='TBA',
                    capacity=db_course["capacity"],
                    enrolled=db_course["enrolled_count"],
                    theoryHours=db_course.get("theory_hours") or 3,
                    practiceHours=db_course.get("practice_hours") or 1,
                    department=db_course.get("department"),
                    year=db_course.get("year"),
                    semester=db_course.get("semester"),
                    level=db_course.get("level"),
                    category=db_course.get("category"),
                )
            result.append(course_data)
        
        return result

    def get_cart(self, user_id: str) -> List[Course]:
        """Get user's cart items"""
        db_courses = course_repository.get_user_cart(user_id)
        
        result = []
        for db_course in db_courses:
            demo_course = self.demo_courses.get(db_course["id"])
            if demo_course:
                course_data = Course(
                    course_id=db_course["id"],
                    title=demo_course.title,
                    professor=getattr(demo_course, 'professor', 'Unknown'),
                    schedule=getattr(demo_course, 'schedule', 'TBA'),
                    capacity=db_course["capacity"],
                    enrolled=db_course["enrolled_count"]
                )
                result.append(course_data)
        
        return result

    def add_to_cart(self, user_id: str, course_id: str) -> None:
        """Add course to user's cart"""
        course_repository.add_to_cart(user_id, course_id)

    def remove_from_cart(self, user_id: str, course_id: str) -> None:
        """Remove course from user's cart"""
        course_repository.remove_from_cart(user_id, course_id)

    def enroll(self, user_id: str) -> List[EnrollResult]:
        """Enroll user in all cart courses"""
        results_data = course_repository.enroll_user(user_id)
        
        # Convert to EnrollResult objects
        results = []
        for result_data in results_data:
            success = result_data["status"] == "SUCCESS"
            reason = result_data["message"] if not success else None
            
            results.append(EnrollResult(
                courseId=result_data["courseId"],
                success=success,
                reason=reason
            ))
        
        return results

    def my_courses(self, user_id: str) -> List[Course]:
        """Get user's enrolled courses"""
        db_courses = course_repository.get_user_enrollments(user_id)
        
        result = []
        for db_course in db_courses:
            demo_course = self.demo_courses.get(db_course["id"])
            if demo_course:
                course_data = Course(
                    course_id=db_course["id"],
                    title=demo_course.title,
                    professor=getattr(demo_course, 'professor', 'Unknown'),
                    schedule=getattr(demo_course, 'schedule', 'TBA'),
                    capacity=db_course["capacity"],
                    enrolled=db_course["enrolled_count"]
                )
                result.append(course_data)
        
        return result


    def list_departments(self, *, year: Optional[int] = None, semester: Optional[int] = None) -> List[str]:
        # curated 데이터 기반으로 전공 목록 산출
        deps: List[str] = []
        for c in self.demo_courses.values():
            if year is not None and getattr(c, 'year', None) != year:
                continue
            if semester is not None and getattr(c, 'semester', None) != semester:
                continue
            if getattr(c, 'department', None):
                deps.append(c.department)  # type: ignore[attr-defined]
        return sorted(sorted(set(deps)))

course_service = CourseService()
