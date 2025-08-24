from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cart = relationship("Cart", back_populates="user", uselist=False)
    enrollments = relationship("Enrollment", back_populates="user")


class Course(Base):
    __tablename__ = 'courses'
    
    id = Column(String(40), primary_key=True)
    title = Column(Text, nullable=False)
    capacity = Column(Integer, nullable=False)
    enrolled_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint('capacity >= 0', name='check_capacity_positive'),
        CheckConstraint('enrolled_count >= 0', name='check_enrolled_count_positive'),
    )
    
    # Relationships
    cart_items = relationship("CartItem", back_populates="course")
    enrollments = relationship("Enrollment", back_populates="course")


class Cart(Base):
    __tablename__ = 'carts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = 'cart_items'
    
    cart_id = Column(UUID(as_uuid=True), ForeignKey('carts.id', ondelete='CASCADE'), primary_key=True)
    course_id = Column(String(40), ForeignKey('courses.id'), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    course = relationship("Course", back_populates="cart_items")


class Enrollment(Base):
    __tablename__ = 'enrollments'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    course_id = Column(String(40), ForeignKey('courses.id'), primary_key=True)
    status = Column(String(20), nullable=False, default='ENROLLED')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
