import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid

from app.main import app
from app.database import get_db, Base
from app.models import User

TEST_DB_NAME = "meeting_room_db_test"
admin_engine = create_engine(
    "postgresql://postgres:postgres@localhost:5433/postgres",
    isolation_level="AUTOCOMMIT"
)
test_engine = create_engine(
    f"postgresql://postgres:postgres@localhost:5433/{TEST_DB_NAME}"
)
Session = sessionmaker(bind=test_engine)


def override_get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Генерирует уникальное имя для комнаты, чтобы тесты не конфликтовали
def unique_name(prefix: str = "Room") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    Base.metadata.create_all(bind=test_engine)
    yield
    test_engine.dispose()
    admin_engine.dispose()

    with admin_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    client.post("/api/auth/register", json={
        "email": "admin@test.com",
        "password": "pass1234",
        "full_name": "Admin"
    })
    db = Session()
    db.query(User).filter_by(email="admin@test.com").first().is_admin = True
    db.commit()
    db.close()
    return client.post("/api/auth/login", data={
        "username": "admin@test.com",
        "password": "pass1234"
    }).json()["access_token"]


@pytest.fixture
def user_token(client):
    client.post("/api/auth/register", json={
        "email": "user@test.com",
        "password": "pass1234",
        "full_name": "User"
    })
    return client.post("/api/auth/login", data={
        "username": "user@test.com",
        "password": "pass1234"
    }).json()["access_token"]


# админ создаёт комнату и бронирование в ней.
def test_create_room_and_booking(client, admin_token):
    room = client.post(
        "/api/rooms",
        json={"name": "Переговорка", "capacity": 5, "description": "1 этаж"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert room.status_code in (200, 201)

    booking = client.post(
        "/api/bookings",
        json={
            "room_id": room.json()["id"],
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "time_slot": "09:00-11:00",
            "participants_count": 3
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert booking.status_code in (200, 201)

# обычный пользователь не может создавать комнаты
def test_user_cannot_create_room(client, user_token):
    response = client.post(
        "/api/rooms",
        json={"name": "R", "capacity": 5, "description": "t"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403

# нельзя забронировать одну комнату на одно и то же время дважды
def test_booking_overlap_forbidden(client, admin_token):
    room = client.post(
        "/api/rooms",
        json={"name": "R", "capacity": 5, "description": "t"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    room_id = room.json()["id"]
    future = (date.today() + timedelta(days=1)).isoformat()

    first = client.post(
        "/api/bookings",
        json={"room_id": room_id, "date": future, "time_slot": "09:00-11:00", "participants_count": 2},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert first.status_code in (200, 201)  

    second = client.post(
        "/api/bookings",
        json={"room_id": room_id, "date": future, "time_slot": "09:00-11:00", "participants_count": 2},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert second.status_code == 400

# Проверка ограничения вместимости
def test_capacity_exceeded(client, admin_token):
    room = client.post(
        "/api/rooms",
        json={"name": "Маленькая", "capacity": 3, "description": "small"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    booking = client.post(
        "/api/bookings",
        json={
            "room_id": room.json()["id"],
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "time_slot": "14:00-16:00",
            "participants_count": 10
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert booking.status_code == 400

# Проверка защиты от неавторизованного доступа
def test_unauthorized_access(client):
    response = client.post(
        "/api/bookings",
        json={
            "room_id": 1,
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "time_slot": "10:00-11:00",
            "participants_count": 2
        }
    )
    assert response.status_code == 401

# пользователь не может отменить бронирование, созданное другим пользователем
def test_user_cannot_cancel_others_booking(client, admin_token, user_token):

    room = client.post(
        "/api/rooms",
        json={"name": "Room", "capacity": 5, "description": "test"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    room_id = room.json()["id"]    

    future = (date.today() + timedelta(days=1)).isoformat()
    booking = client.post(
        "/api/bookings",
        json={
            "room_id": room_id,
            "date": future,
            "time_slot": "09:00-11:00",
            "participants_count": 2
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    booking_id = booking.json()["id"]

    response = client.delete(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403

# время начала должно быть раньше времени окончания
def test_invalid_time_interval_forbidden(client, admin_token):
    room = client.post(
        "/api/rooms",
        json={"name": unique_name(), "capacity": 5, "description": "test"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    room_id = room.json()["id"]
    future = (date.today() + timedelta(days=1)).isoformat()
    
    response = client.post(
        "/api/bookings",
        json={
            "room_id": room_id,
            "date": future,
            "time_slot": "13:00-11:00",  
            "participants_count": 2
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code in (400, 422)

# Проверка эндпоинта доступности комнат
def test_room_availability_by_date(client, admin_token):
    room = client.post(
        "/api/rooms",
        json={"name": unique_name(), "capacity": 5, "description": "test"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    room_id = room.json()["id"]
    
    future = (date.today() + timedelta(days=1)).isoformat()
    
    # Создаём бронирование
    client.post(
        "/api/bookings",
        json={
            "room_id": room_id,
            "date": future,
            "time_slot": "09:00-11:00",
            "participants_count": 2
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.get(
        f"/api/rooms/availability?date={future}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# нельзя забронировать комнату на слот, которого нет в списке доступных слотов этой комнаты.
def test_invalid_slot_forbidden(client, admin_token):
    room = client.post(
        "/api/rooms",
        json={
    "name": unique_name(),
    "capacity": 5,
    "description": "test",
    "time_slots": ["09:00-11:00", "11:00-13:00"]
    },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    room_id = room.json()["id"]
    future = (date.today() + timedelta(days=1)).isoformat()
    
    response = client.post(
        "/api/bookings",
        json={
            "room_id": room_id,
            "date": future,
            "time_slot": "16:00-18:00",  
            "participants_count": 2
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400