from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# Room schemas
class RoomBase(BaseModel):
    name: str = Field(..., max_length=100)
    capacity: int = Field(..., ge=1, le=100)
    equipment: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class RoomResponse(RoomBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


# Booking schemas
class BookingBase(BaseModel):
    room_id: int
    user_email: EmailStr
    user_telegram_id: Optional[str] = None
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None


class BookingCreate(BookingBase):
    pass


class BookingResponse(BookingBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Conflict check response
class ConflictCheckResponse(BaseModel):
    has_conflict: bool
    message: str


# Health check
class HealthResponse(BaseModel):
    status: str
    services: dict
