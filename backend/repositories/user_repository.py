from typing import Optional
from sqlalchemy.orm import Session
from db.models import User, Cart
from db.session import get_db_session
import uuid
import hashlib


class UserRepository:
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """Create a new user with cart"""
        password_hash = f"hashed_{password}"  # TODO: Use proper hashing like bcrypt
        
        with get_db_session() as session:
            # Check duplicates
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    raise ValueError("이미 사용 중인 아이디입니다.")
                else:
                    raise ValueError("이미 사용 중인 이메일입니다.")
            
            # Create user
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash
            )
            session.add(new_user)
            session.flush()  # Get the ID
            
            # Create cart
            cart = Cart(user_id=new_user.id)
            session.add(cart)
            
            return new_user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        with get_db_session() as session:
            return session.query(User).filter(User.username == username).first()
    
    def verify_password(self, user: User, password: str) -> bool:
        """Verify user password (simplified)"""
        expected_hash = f"hashed_{password}"
        return user.password_hash == expected_hash


user_repository = UserRepository()
