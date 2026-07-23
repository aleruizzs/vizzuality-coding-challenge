from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from src.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Connected to PostgreSQL database")
    except Exception as error:
        print(f"❌ Database connection error: {error}")
