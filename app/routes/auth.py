from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.kullanici_adi == user_data.kullanici_adi).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kullanılıyor!")
    
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Bu email zaten kullanılıyor!")
    
    new_user = User(
        kullanici_adi=user_data.kullanici_adi,
        email=user_data.email,
        sifre_hash=get_password_hash(user_data.sifre),
        adi=user_data.adi,
        soyadi=user_data.soyadi,
        rol=user_data.rol
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.kullanici_adi == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.sifre_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı kullanıcı adı veya şifre!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.aktif:
        raise HTTPException(status_code=403, detail="Hesabınız pasif durumda!")
    
    access_token = create_access_token(data={"sub": user.kullanici_adi})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
