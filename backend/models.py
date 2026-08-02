from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=True)
    password_hash = Column(String(300), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    bookings = relationship("Booking", back_populates="user")

class Tour(Base):
    __tablename__ = "tours"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    short_description = Column(String(400), nullable=False)
    full_description = Column(Text, nullable=False)
    itinerary = Column(Text, nullable=False)
    included = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    duration = Column(String(120), nullable=False, default="1 day")
    image_urls = Column(Text, nullable=False)
    video_urls = Column(Text, nullable=True)
    front_media_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    bookings = relationship("Booking", back_populates="tour")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tour_id = Column(Integer, ForeignKey("tours.id"), nullable=False)
    name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    age = Column(Integer, nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(64), nullable=False)
    date_of_booking = Column(String(80), nullable=False)
    status = Column(String(80), default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="bookings")
    tour = relationship("Tour", back_populates="bookings")

class OTPToken(Base):
    __tablename__ = "otp_tokens"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), nullable=False, index=True)
    otp_hash = Column(String(300), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
