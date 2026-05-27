from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Room
from ..schemas import RoomCreate, RoomResponse
from ..metrics import rooms_created_total

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    # Заглушка для проверки роли администратора
    x_user_role: str = None
):
    """Создание новой переговорной комнаты (только администратор)"""
    # Простая проверка роли (заглушка)
    if x_user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create rooms"
        )

    db_room = Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    rooms_created_total.inc()

    return db_room


@router.get("/", response_model=list[RoomResponse])
async def get_rooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получение списка всех комнат"""
    rooms = db.query(Room).filter(Room.is_active ==
                                  True).offset(skip).limit(limit).all()
    return rooms


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    db: Session = Depends(get_db)
):
    """Получение информации о комнате по ID"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    return room
