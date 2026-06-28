from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date
from app.database import get_db
from app.models import Booking, Room, User
from app.schemas import BookingCreate, BookingResponse
from app.routers.user_router import get_current_user

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


def check_intersection(new_start: str, new_end: str, 
                       existing_start: str, existing_end: str) -> bool:
    
    fmt = "%H:%M"
    n_start = datetime.strptime(new_start, fmt)
    n_end = datetime.strptime(new_end, fmt)
    e_start = datetime.strptime(existing_start, fmt)
    e_end = datetime.strptime(existing_end, fmt)

    if n_start < e_end and n_end > e_start:
        return True  
    
    return False  

@router.post("", response_model=BookingResponse, status_code=201)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
): 
    room = db.query(Room).filter(Room.id == booking_data.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    
    if booking_data.participants_count > room.capacity:
        raise HTTPException(
        status_code=400,
        detail=f"Количество участников ({booking_data.participants_count}) превышает вместимость комнаты ({room.capacity})"

    )
    if booking_data.time_slot not in room.time_slots:
        raise HTTPException(
            status_code=400,
            detail=f"Временной слот '{booking_data.time_slot}' недоступен для этой комнаты. Доступные слоты: {', '.join(room.time_slots)}"
        )
    try:
        booking_date = datetime.strptime(booking_data.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Неправильный формат даты. Используйте YYYY-MM-DD"
        )
    
    if booking_date < date.today():
        raise HTTPException(
        status_code=400,
        detail="Нельзя бронировать прошлые даты"
    )
    new_start, new_end = booking_data.time_slot.split("-")
    new_start = new_start.strip()
    new_end = new_end.strip()

    existing_bookings = db.query(Booking).filter(
        Booking.room_id == booking_data.room_id,
        Booking.date == booking_data.date
    ).all()

    for booking in existing_bookings:
        existing_start, existing_end = booking.time_slot.split("-")
        existing_start = existing_start.strip()
        existing_end = existing_end.strip()
        
        if check_intersection(new_start, new_end, existing_start, existing_end):
            raise HTTPException(
                status_code=400, 
                detail=f"Время пересекается с бронированием #{booking.id} ({booking.time_slot})"
            )

    new_booking = Booking(
        room_id=booking_data.room_id,
        user_id=user.id,
        date=booking_data.date,
        time_slot=booking_data.time_slot,
         participants_count=booking_data.participants_count  
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking


@router.get("/my", response_model=List[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(Booking).filter(Booking.user_id == user.id).all()


@router.get("", response_model=List[BookingResponse])
def get_all_bookings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Только для админов")
    return db.query(Booking).all()


@router.delete("/{booking_id}", status_code=204)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    if booking.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Нельзя отменить чужое бронирование")

    db.delete(booking)
    db.commit()
    return None
