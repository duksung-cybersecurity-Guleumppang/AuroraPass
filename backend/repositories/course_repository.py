from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
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
    
    def get_user_cart(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's cart items as course dicts"""
        with get_db_session() as session:
            cart = session.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                return []
            
            courses = session.query(Course).join(CartItem).filter(
                CartItem.cart_id == cart.id
            ).all()
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
    
    def get_user_enrollments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's enrolled courses as dicts"""
        # Convert user_id to UUID if it's a string
        if isinstance(user_id, str):
            user_id = UUID(user_id)
            
        with get_db_session() as session:
            courses = session.query(Course).join(Enrollment).filter(
                Enrollment.user_id == user_id
            ).all()
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


course_repository = CourseRepository()
