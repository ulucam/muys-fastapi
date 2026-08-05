import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Varsayılan değer mevcut kurulumların session çerezlerini geçersiz kılmamak
    # için önceki SessionMiddleware anahtarıyla aynıdır.
    SECRET_KEY = os.getenv("SECRET_KEY", "muys-secret-key-2026")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./muys.db")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10080))
