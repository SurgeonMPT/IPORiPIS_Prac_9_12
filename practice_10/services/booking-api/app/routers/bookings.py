from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models import Room, Booking, check_conflict
from ..schemas import BookingCreate, BookingResponse, ConflictCheckResponse
from ..rabbit import get_rabbit
from ..metrics import bookings_created_total

router = APIRouter(prefix="/bookings", tags=["bookings"])


async def send_notification_background(
    booking_id: int,
    user_email: str,
    user_telegram_id: str,
    room_name: str,
    start_time: datetime,
    end_time: datetime,
    action: str = "created"
):
    """Фоновая отправка уведомления через RabbitMQ"""
    rabbit = await get_rabbit()
    if rabbit:
        await rabbit.publish_notification({
            "booking_id": booking_id,
            "user_email": user_email,
            "user_telegram_id": user_telegram_id,
            "room_name": room_name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "action": action
        })


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking: BookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Создание нового бронирования"""
    # Проверяем существование комнаты
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # Проверяем корректность времени
    if booking.start_time >= booking.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time"
        )

    if booking.start_time < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book in the past"
        )

    # Проверяем конфликт
    if check_conflict(db, booking.room_id, booking.start_time, booking.end_time):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room is already booked for this time period"
        )

    # Создаем бронирование
    db_booking = Booking(**booking.model_dump())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    bookings_created_total.inc()

    # Отправляем уведомление в фоне
    background_tasks.add_task(
        send_notification_background,
        db_booking.id,
        booking.user_email,
        booking.user_telegram_id,
        room.name,
        booking.start_time,
        booking.end_time,
        "created"
    )

    return db_booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Отмена бронирования"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking already cancelled"
        )

    # Получаем информацию о комнате до удаления
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    room_name = room.name if room else "Unknown"

    # Отменяем бронирование
    booking.status = "cancelled"
    db.commit()

    # Отправляем уведомление об отмене
    background_tasks.add_task(
        send_notification_background,
        booking.id,
        booking.user_email,
        booking.user_telegram_id,
        room_name,
        booking.start_time,
        booking.end_time,
        "cancelled"
    )

    return None


@router.get("/", response_model=list[BookingResponse])
async def get_bookings(
    skip: int = 0,
    limit: int = 100,
    room_id: int = None,
    user_email: str = None,
    db: Session = Depends(get_db)
):
    """Получение списка бронирований с фильтрацией"""
    query = db.query(Booking).filter(Booking.status == "active")

    if room_id:
        query = query.filter(Booking.room_id == room_id)
    if user_email:
        query = query.filter(Booking.user_email == user_email)

    bookings = query.order_by(Booking.start_time).offset(
        skip).limit(limit).all()
    return bookings


@router.get("/check-conflict/", response_model=ConflictCheckResponse)
async def check_booking_conflict(
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db)
):
    """Проверка конфликта бронирования без создания"""
    has_conflict = check_conflict(db, room_id, start_time, end_time)

    return ConflictCheckResponse(
        has_conflict=has_conflict,
        message="Room is available" if not has_conflict else "Room is already booked for this time"
    )
