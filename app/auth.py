from passlib.context import CryptContext          
from jose import jwt                              
from datetime import datetime, timedelta, timezone
from typing import Optional    
from app.database import settings 

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def check_password(plain_password: str, hashed_password: str) -> bool:
     return pwd_context.verify(plain_password, hashed_password)



def create_access_token(data: dict, delta: Optional[timedelta] = None) -> str:

    to_encode = data.copy()
    
    if delta:
        expire = datetime.now(timezone.utc) + delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

