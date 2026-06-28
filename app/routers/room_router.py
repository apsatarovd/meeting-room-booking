from fastapi import APIRouter, Depends, HTTPException, status,  Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database import get_db
from app.models import Room, User, Booking
from app.schemas import RoomCreate, RoomResponse, RoomAvailability, BookingInfo
from app.routers.user_router import get_current_user

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])


def check_admin(user: User):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Только для админов")


def get_room_or_404(db: Session, room_id: int) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    return room


@router.get("/availability", response_model=List[RoomAvailability])
def get_rooms_availability(
    date: date = Query(..., description="Дата должна быть написана в формате YYYY-MM-DD"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    rooms = db.query(Room).all()
    
    result = []
    for room in rooms:
        bookings = db.query(Booking).filter(
            Booking.room_id == room.id,
            Booking.date == date.isoformat()
)       .all()
        
        result.append(RoomAvailability(
            room_id=room.id,
            room_name=room.name,
            capacity=room.capacity,
            description=room.description,
            date=date.isoformat(),
            bookings=[
                BookingInfo(
                    id=b.id,
                    time_slot=b.time_slot,
                    participants_count=b.participants_count,
                    user_name=b.user.full_name
                )
                for b in bookings
            ]
        ))
    
    return result


@router.get("", response_model=List[RoomResponse])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    return get_room_or_404(db, room_id)


@router.post("", response_model=RoomResponse, status_code=201)
def create_room(
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    check_admin(user)
    
    if db.query(Room).filter(Room.name == room_data.name).first():
        raise HTTPException(status_code=400, detail="Комната с таким названием уже существует")
    
    new_room = Room(**room_data.dict())
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return new_room


@router.put("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    check_admin(user)
    
    room = get_room_or_404(db, room_id)
    
    if room_data.name != room.name:
        if db.query(Room).filter(Room.name == room_data.name, Room.id != room_id).first():
            raise HTTPException(status_code=400, detail="Такое название уже занято")

    for key, value in room_data.dict().items():
        setattr(room, key, value)
    
    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}", status_code=204)
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    check_admin(user)
    
    room = get_room_or_404(db, room_id)
    
    if room.bookings:
        raise HTTPException(status_code=400, detail="Есть активные бронирования")
    
    db.delete(room)
    db.commit()
    return None