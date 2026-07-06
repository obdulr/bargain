from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Use synchronous engine for local SQLite development
engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""), echo=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
