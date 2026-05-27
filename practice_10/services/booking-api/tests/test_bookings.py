import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Room, Booking

# Тестовая БД
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
                       "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)

    # Создаем тестовую комнату
    db = TestingSessionLocal()
    room = Room(name="Test Room", capacity=10, equipment="TV")
    db.add(room)
    db.commit()
    db.refresh(room)
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def get_test_room_id():
    db = TestingSessionLocal()
    room = db.query(Room).first()
    room_id = room.id if room else 1
    db.close()
    return room_id


def test_create_booking_success():
    """Тест успешного создания бронирования"""
    room_id = get_test_room_id()
    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)

    response = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "user_email": "test@example.com",
            "user_telegram_id": "123456789",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "purpose": "Team meeting"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["room_id"] == room_id
    assert data["user_email"] == "test@example.com"
    assert data["status"] == "active"


def test_create_booking_conflict():
    """Тест создания бронирования с конфликтом"""
    room_id = get_test_room_id()
    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)

    # Первое бронирование
    client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "user_email": "user1@example.com",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    # Второе бронирование (конфликт)
    response = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "user_email": "user2@example.com",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    assert response.status_code == 409
    assert "already booked" in response.json()["detail"]


def test_cancel_booking():
    """Тест отмены бронирования"""
    room_id = get_test_room_id()
    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)

    # Создание бронирования
    create_response = client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "user_email": "test@example.com",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )
    booking_id = create_response.json()["id"]

    # Отмена
    response = client.delete(f"/bookings/{booking_id}")
    assert response.status_code == 204


def test_check_conflict_endpoint():
    """Тест эндпоинта проверки конфликта"""
    room_id = get_test_room_id()
    start_time = datetime.utcnow() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)

    # Создание бронирования
    client.post(
        "/bookings/",
        json={
            "room_id": room_id,
            "user_email": "test@example.com",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    # Проверка конфликта
    response = client.get(
        f"/bookings/check-conflict/",
        params={
            "room_id": room_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    )

    assert response.status_code == 200
    assert response.json()["has_conflict"] is True
