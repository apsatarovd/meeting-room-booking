from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
from typing import List, Optional


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
    time_slots: Optional[List[str]] = [
        "09:00-11:00",
        "11:00-13:00",
        "14:00-16:00",
        "16:00-18:00"
    ]



class RoomResponse(BaseModel):
    id: int
    name: str
    capacity: int
    description: Optional[str]
    time_slots: List[str] 
    
    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    room_id: int
    date: str
    time_slot: str
    participants_count: int = Field(..., gt=0, description="Количество участников")

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
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
            start = start.strip()
            end = end.strip()
            
            start_time = datetime.strptime(start, "%H:%M")
            end_time = datetime.strptime(end, "%H:%M")
            
            if start_time >= end_time:
                raise ValueError(
                    f'Время начала ({start}) должно быть раньше времени конца ({end})'
                )
        except ValueError as e:
            if "должно быть раньше" in str(e):
                raise ValueError(str(e))
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

class BookingInfo(BaseModel):
    id: int
    time_slot: str
    participants_count: int
    user_name: str

    class Config:
        from_attributes = True

class RoomAvailability(BaseModel):
    room_id: int
    room_name: str
    capacity: int
    description: Optional[str] = None
    date: str
    bookings: List[BookingInfo] = []

    class Config:
        from_attributes = True