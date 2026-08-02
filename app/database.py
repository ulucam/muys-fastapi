from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import Config


# ==========================
# DATABASE ENGINE
# ==========================

DATABASE_URL = Config.DATABASE_URL

# Render postgres URL düzeltme
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )

elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )



if "sqlite" in DATABASE_URL:

    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False
        }
    )

else:

    engine = create_engine(
        DATABASE_URL
    )



# ==========================
# SESSION
# ==========================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)



# ==========================
# MODEL BASE
# ==========================

Base = declarative_base()



# ==========================
# DATABASE CONNECTION
# ==========================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()