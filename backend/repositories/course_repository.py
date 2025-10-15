from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from uuid import UUID
from db.models import Course, Cart, CartItem, Enrollment, User
from db.session import get_db_session


class CourseRepository:
    
    def get_all_courses(self) -> List[Dict[str, Any]]:
        """Get all courses as dicts"""
        with get_db_session() as session:
            courses = session.query(Course).all()
            return [
                {
                    "id": course.id,
                    "title": course.title,
                    "capacity": course.capacity,
                    "enrolled_count": course.enrolled_count,
                    "updated_at": course.updated_at
                }
                for course in courses
            ]
    
    def get_course_by_id(self, course_id: str) -> Optional[Course]:
        """Get course by ID"""
        with get_db_session() as session:
            return session.query(Course).filter(Course.id == course_id).first()

    def get_courses_filtered(
        self,
        *,
        keyword: Optional[str] = None,
        year: Optional[int] = None,
        semester: Optional[int] = None,
        level: Optional[str] = None,
        category: Optional[str] = None,
        department: Optional[str] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get courses with optional keyword filter and pagination/sorting"""
        with get_db_session() as session:
            query = session.query(Course).filter(Course.is_active.is_(True))

            if keyword:
                # case-insensitive search on title
                kw = f"%{keyword.lower()}%"
                query = query.filter(func.lower(Course.title).like(kw))

            if year is not None:
                query = query.filter(Course.year == year)
            if semester is not None:
                query = query.filter(Course.semester == semester)
            if level:
                query = query.filter(Course.level == level)
            if category:
                query = query.filter(Course.category == category)
            if department:
                query = query.filter(Course.department == department)

            # sorting
            sort_key = (sort or "recent").lower()
            is_desc = (order or "desc").lower() == "desc"

            if sort_key == "name" or sort_key == "title":
                query = query.order_by(Course.title.desc() if is_desc else Course.title.asc())
            elif sort_key == "code" or sort_key == "id":
                query = query.order_by(Course.id.desc() if is_desc else Course.id.asc())
            else:  # recent by updated_at
                query = query.order_by(Course.updated_at.desc() if is_desc else Course.updated_at.asc())

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            courses = query.all()
            return [
                {
                    "id": course.id,
                    "title": course.title,
                    "capacity": course.capacity,
                    "enrolled_count": course.enrolled_count,
                    "theory_hours": getattr(course, 'theory_hours', None),
                    "practice_hours": getattr(course, 'practice_hours', None),
                    "year": course.year,
                    "semester": course.semester,
                    "level": course.level,
                    "category": course.category,
                    "department": course.department,
                    "updated_at": course.updated_at,
                }
                for course in courses
            ]
    
    def get_user_cart(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's cart items as course dicts"""
        with get_db_session() as session:
            cart = session.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                return []
            
            courses = session.query(Course).join(CartItem).filter(
                CartItem.cart_id == cart.id
            ).filter(Course.is_active.is_(True)).all()
            return [
                {
                    "id": course.id,
                    "title": course.title,
                    "capacity": course.capacity,
                    "enrolled_count": course.enrolled_count,
                    "updated_at": course.updated_at
                }
                for course in courses
            ]
    
    def add_to_cart(self, user_id: str, course_id: str) -> None:
        """Add course to user's cart"""
        with get_db_session() as session:
            # Get or create cart
            cart = session.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                cart = Cart(user_id=user_id)
                session.add(cart)
                session.flush()
            
            # Check if course exists
            course = session.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise ValueError("강의를 찾을 수 없습니다.")
            
            # Check if already in cart
            existing = session.query(CartItem).filter(
                and_(CartItem.cart_id == cart.id, CartItem.course_id == course_id)
            ).first()
            if existing:
                raise ValueError("이미 장바구니에 있는 강의입니다.")
            
            # Add to cart
            cart_item = CartItem(cart_id=cart.id, course_id=course_id)
            session.add(cart_item)
    
    def remove_from_cart(self, user_id: str, course_id: str) -> None:
        """Remove course from user's cart"""
        with get_db_session() as session:
            cart = session.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                return
            
            cart_item = session.query(CartItem).filter(
                and_(CartItem.cart_id == cart.id, CartItem.course_id == course_id)
            ).first()
            if cart_item:
                session.delete(cart_item)
    
    def enroll_user(self, user_id: str) -> List[dict]:
        """Enroll user in all cart courses"""
        results = []
        
        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        with get_db_session() as session:
            cart = session.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                return results
            
            cart_items = session.query(CartItem).filter(CartItem.cart_id == cart.id).all()
            
            for item in cart_items:
                course = session.query(Course).filter(Course.id == item.course_id).first()
                if not course:
                    continue
                
                # Check capacity with row-level lock
                course_locked = session.query(Course).filter(Course.id == course.id).with_for_update().first()
                
                if course_locked.enrolled_count >= course_locked.capacity:
                    results.append({
                        "courseId": course.id,
                        "title": course.title,
                        "status": "FAILED",
                        "message": "정원 초과"
                    })
                    continue
                
                # Check if already enrolled
                existing_enrollment = session.query(Enrollment).filter(
                    and_(Enrollment.user_id == user_id, Enrollment.course_id == course.id)
                ).first()
                
                if existing_enrollment:
                    results.append({
                        "courseId": course.id,
                        "title": course.title,
                        "status": "FAILED",
                        "message": "이미 신청한 강의"
                    })
                    continue
                
                # Enroll
                enrollment = Enrollment(user_id=user_id, course_id=course.id)
                session.add(enrollment)
                
                # Update count
                course_locked.enrolled_count += 1
                
                results.append({
                    "courseId": course.id,
                    "title": course.title,
                    "status": "SUCCESS",
                    "message": "신청 완료"
                })
            
            # Clear cart after enrollment attempt
            for item in cart_items:
                session.delete(item)
        
        return results
    
    def get_departments(self, *, year: Optional[int] = None, semester: Optional[int] = None) -> List[str]:
        """Get distinct departments from courses, optionally filtered by year/semester"""
        with get_db_session() as session:
            query = session.query(Course.department).filter(Course.department.isnot(None))
            if year is not None:
                query = query.filter(Course.year == year)
            if semester is not None:
                query = query.filter(Course.semester == semester)
            rows = query.distinct().order_by(Course.department).all()
            return [r[0] for r in rows if r and r[0]]

    def get_user_enrollments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's enrolled courses as dicts"""
        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        with get_db_session() as session:
            courses = session.query(Course).join(Enrollment).filter(
                Enrollment.user_id == user_id
            ).filter(Course.is_active.is_(True)).all()
            return [
                {
                    "id": course.id,
                    "title": course.title,
                    "capacity": course.capacity,
                    "enrolled_count": course.enrolled_count,
                    "updated_at": course.updated_at
                }
                for course in courses
            ]

    def cancel_enrollment(self, user_id: str, course_id: str) -> bool:
        """Cancel user's enrollment for a course"""
        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        with get_db_session() as session:
            # Find enrollment
            enrollment = session.query(Enrollment).filter(
                and_(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
            ).first()

            if not enrollment:
                return False

            # Lock the course row and decrement enrolled_count
            course = session.query(Course).filter(Course.id == course_id).with_for_update().first()
            if course and course.enrolled_count > 0:
                course.enrolled_count -= 1

            # Delete enrollment
            session.delete(enrollment)

            return True


course_repository = CourseRepository()
