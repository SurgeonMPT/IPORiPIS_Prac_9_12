from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    equipment = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    bookings = relationship("Booking", back_populates="room")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_email = Column(String(200), nullable=False)
    user_telegram_id = Column(String(100), nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    purpose = Column(Text, nullable=True)
    status = Column(String(20), default="active")  # active, cancelled, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="bookings")


def check_conflict(db, room_id: int, start_time: datetime, end_time: datetime, exclude_id: int = None) -> bool:
    """
    Проверяет, есть ли пересечение бронирований для комнаты.
    Возвращает True если конфликт есть.
    """
    from sqlalchemy import and_
    
    query = db.query(Booking).filter(
        and_(
            Booking.room_id == room_id,
            Booking.status == "active",
            Booking.start_time < end_time,
            Booking.end_time > start_time
        )
    )
    
    if exclude_id:
        query = query.filter(Booking.id != exclude_id)
    
    return query.first() is not None