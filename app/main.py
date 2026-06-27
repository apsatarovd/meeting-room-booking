from fastapi import FastAPI
from app.database import engine, Base
from app.models import User, Room, Booking

from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router
from app.routers.room_router import router as room_router
from app.routers.booking_router import router as booking_router

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