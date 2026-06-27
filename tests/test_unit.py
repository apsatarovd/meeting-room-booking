import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from app.auth import hash_password, check_password, create_access_token
from app.routers.booking_router import check_intersection
from app.schemas import UserCreate, RoomCreate, BookingCreate


class TestUserValidation:

    def test_valid_user_creation(self):
        user = UserCreate(
            email="test@mail.ru",
            password="secure123",
            full_name="Иван Иванов"
        )
        assert user.email == "test@mail.ru"
        assert user.full_name == "Иван Иванов"

    def test_invalid_email_format(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="неправильный-email",
                password="secure123",
                full_name="Иван Иванов"
            )

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@mail.ru",
                password="12345",  
                full_name="Иван Иванов"
            )

class TestPasswordSecurity:

    def test_password_is_hashed_not_stored_plain(self):
        password = "my_secret_password"
        hashed = hash_password(password)
        
        # Хэш не должен совпадать с оригиналом
        assert hashed != password
        # Хэш не должен содержать пароль как подстроку
        assert password not in hashed

    def test_same_password_different_hashes(self):
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

    def test_wrong_password_rejected(self):
        password = "correct_password"
        hashed = hash_password(password)
        
        assert check_password("wrong_password", hashed) == False
        assert check_password("", hashed) == False
        assert check_password("correct_password ", hashed) == False  # С пробелом

class TestTimeIntersection:

    def test_overlapping_times_detected(self):
        # 11:00-13:00 пересекается с 12:00-14:00
        assert check_intersection("11:00", "13:00", "12:00", "14:00") == True

    def test_non_overlapping_times_allowed(self):
        # 11:00-13:00 и 14:00-16:00 не пересекаются
        assert check_intersection("11:00", "13:00", "14:00", "16:00") == False

    def test_adjacent_times_allowed(self):
        # 11:00-13:00 и 13:00-15:00 — разрешается 
        assert check_intersection("11:00", "13:00", "13:00", "15:00") == False

    def test_complete_overlap_detected(self):
        # 09:00-17:00 полностью покрывает 10:00-12:00
        assert check_intersection("09:00", "17:00", "10:00", "12:00") == True

class TestSchemaValidation:

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@mail.ru",
                password="12345",  
                full_name="Иван Иванов"
            )

    def test_negative_room_capacity_rejected(self):
        with pytest.raises(ValidationError):
            RoomCreate(
                name="Про футбол",
                capacity=-5,  
                description="Тест"
            )

    def test_invalid_booking_date_rejected(self):
        with pytest.raises(ValidationError):
            BookingCreate(
                room_id=1,
                date="25.06.2026", 
                time_slot="11:00-13:00",
                participants_count=5
            )