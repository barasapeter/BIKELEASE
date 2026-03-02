from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import config

SETTINGS = config.GlobalSettings()

engine = create_engine(
    SETTINGS.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
