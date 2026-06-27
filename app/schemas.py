from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=6, description="Минимум 6 символов")


class UserResponse(BaseModel):
    id: int
    email: str  
    full_name: str
    is_admin: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class RoomCreate(BaseModel):
    name: str
    capacity: int = Field(..., gt=0, description="Вместимость должна быть больше 0")
    description: Optional[str] = None


class RoomResponse(BaseModel):
    id: int
    name: str
    capacity: int
    description: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    room_id: int
    date: str
    time_slot: str
    participants_count: int = Field(..., gt=0, description="Количество участников")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
        """Проверяем формат даты ГГГГ-ММ-ДД"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Неверный формат даты. Используйте ГГГГ-ММ-ДД')
        return v

    @field_validator('time_slot')
    @classmethod
    def validate_time_slot_format(cls, v):
        try:
            start, end = v.split("-")
            datetime.strptime(start.strip(), "%H:%M")
            datetime.strptime(end.strip(), "%H:%M")
        except (ValueError, AttributeError):
            raise ValueError('Неверный формат времени. Используйте ЧЧ:ММ-ЧЧ:ММ')
        return v


class BookingResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    date: str
    time_slot: str
    participants_count: int 
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)