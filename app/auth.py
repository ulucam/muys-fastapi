from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import Token, UserResponse
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-it")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz kimlik bilgileri",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.kullanici_adi == username).first()
    if user is None:
        raise credentials_exception
    if not user.aktif:
        raise HTTPException(status_code=403, detail="Hesabınız pasif durumda!")
    return user

from functools import wraps

def rol_gerekli(izinli_roller: list):
    """Belirtilen rollerden birine sahip değilse erişimi engelle"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # current_user'ı kwargs'dan veya args'dan bul
            current_user = kwargs.get('current_user')
            if not current_user:
                # Eğer current_user yoksa, onu bulmaya çalış
                from fastapi import Depends
                from app.auth import get_current_user
                # Bu durumda dependency injection ile çalışıyor
                # Normalde dekoratör doğru çalışır
                pass
            
            # Eğer current_user hala yoksa, args'dan al
            if not current_user and args:
                # İlk argüman genelde current_user'dır
                for arg in args:
                    if hasattr(arg, 'rol'):
                        current_user = arg
                        break
            
            if not current_user:
                from fastapi import HTTPException, status
                raise HTTPException(status_code=401, detail="Giriş yapın!")
            
            if current_user.rol not in izinli_roller:
                from fastapi import HTTPException, status
                raise HTTPException(status_code=403, detail="Bu sayfaya erişim yetkiniz yok!")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
