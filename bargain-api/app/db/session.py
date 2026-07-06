from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Synchronous engine (psycopg2 driver). The config normalizes DATABASE_URL to
# postgresql+psycopg2:// for Railway/Render Postgres, and falls back to sqlite
# for local development.
engine = create_engine(settings.DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
