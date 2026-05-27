import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Room

# Тестовая БД (SQLite in-memory)
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
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_room_success():
    """Тест создания комнаты (админ)"""
    response = client.post(
        "/rooms/",
        headers={"X-User-Role": "admin"},
        json={
            "name": "Test Room",
            "capacity": 10,
            "equipment": "TV, Whiteboard"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Room"
    assert data["capacity"] == 10


def test_create_room_forbidden():
    """Тест создания комнаты без прав админа"""
    response = client.post(
        "/rooms/",
        json={
            "name": "Test Room",
            "capacity": 10
        }
    )
    assert response.status_code == 403
    assert "Only administrators" in response.json()["detail"]


def test_get_rooms():
    """Тест получения списка комнат"""
    # Сначала создаем комнату
    client.post("/rooms/", headers={"X-User-Role": "admin"},
                json={"name": "Room 1", "capacity": 5})
    client.post("/rooms/", headers={"X-User-Role": "admin"},
                json={"name": "Room 2", "capacity": 10})

    response = client.get("/rooms/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_room_by_id():
    """Тест получения комнаты по ID"""
    create_response = client.post(
        "/rooms/",
        headers={"X-User-Role": "admin"},
        json={"name": "Specific Room", "capacity": 8}
    )
    room_id = create_response.json()["id"]

    response = client.get(f"/rooms/{room_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Specific Room"


def test_get_room_not_found():
    """Тест получения несуществующей комнаты"""
    response = client.get("/rooms/999")
    assert response.status_code == 404
    assert "Room not found" in response.json()["detail"]
