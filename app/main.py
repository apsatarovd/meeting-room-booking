from fastapi import FastAPI
from app.models import User, Room, Booking
from app.database import engine, SessionLocal, Base
from app.auth import hash_password
import os
from dotenv import load_dotenv

from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router
from app.routers.room_router import router as room_router
from app.routers.booking_router import router as booking_router

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Room Booking Service")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(room_router)
app.include_router(booking_router)


@app.get("/")
def home():
    return {"message": "Это сервис бронирования переговорных комнат"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def create_admin():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_email or not admin_password:
        return
    
    db = SessionLocal()
    if not db.query(User).filter(User.email == admin_email).first():
        db.add(User(
            email=admin_email,
            full_name=os.getenv("ADMIN_NAME", "Админ"),
            hashed_password=hash_password(admin_password),
            is_admin=1
        ))
        db.commit()
    db.close()