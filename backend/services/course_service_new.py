import json
import os
from typing import Dict, List
from models.course_models import Course, EnrollResult
from repositories.course_repository import course_repository


def _load_demo_courses() -> List[Course]:
    """Load demo courses from JSON file"""
    demo_path = os.path.join(os.path.dirname(__file__), "..", "static", "demo", "courses.json")
    demo_path = os.path.abspath(demo_path)
    with open(demo_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Course(**c) for c in data]


class CourseService:
    def __init__(self) -> None:
        # Demo data fallback for course info (title, professor, schedule)
        self.demo_courses: Dict[str, Course] = {c.course_id: c for c in _load_demo_courses()}

    def list_courses(self) -> List[Course]:
        """Get all courses from DB, fallback to demo data for display info"""
        db_courses = course_repository.get_all_courses()
        
        # Merge with demo data for display
        result = []
        for db_course in db_courses:
            demo_course = self.demo_courses.get(db_course.id)
            if demo_course:
                # Use DB data for capacity/enrolled, demo data for title/professor/schedule
                course_data = Course(
                    course_id=db_course.id,
                    title=demo_course.title,
                    professor=getattr(demo_course, 'professor', 'Unknown'),
                    schedule=getattr(demo_course, 'schedule', 'TBA'),
                    capacity=db_course.capacity,
                    enrolled=db_course.enrolled_count
                )
                result.append(course_data)
        
        return result

    def get_cart(self, user_id: str) -> List[Course]:
        """Get user's cart items"""
        db_courses = course_repository.get_user_cart(user_id)
        
        result = []
        for db_course in db_courses:
            demo_course = self.demo_courses.get(db_course.id)
            if demo_course:
                course_data = Course(
                    course_id=db_course.id,
                    title=demo_course.title,
                    professor=getattr(demo_course, 'professor', 'Unknown'),
                    schedule=getattr(demo_course, 'schedule', 'TBA'),
                    capacity=db_course.capacity,
                    enrolled=db_course.enrolled_count
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
            demo_course = self.demo_courses.get(db_course.id)
            if demo_course:
                course_data = Course(
                    course_id=db_course.id,
                    title=demo_course.title,
                    professor=getattr(demo_course, 'professor', 'Unknown'),
                    schedule=getattr(demo_course, 'schedule', 'TBA'),
                    capacity=db_course.capacity,
                    enrolled=db_course.enrolled_count
                )
                result.append(course_data)
        
        return result


course_service = CourseService()
