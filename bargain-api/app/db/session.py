from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Synchronous engine (psycopg2 driver). The config normalizes DATABASE_URL to
# postgresql+psycopg2:// for Render Postgres, and falls back to sqlite for
# local development.
#
# SQL echo is controlled by SQL_ECHO env var (default False). Setting it to
# True floods logs with every SQL query (~500/sec in production), which causes
# Render's log rate limit to drop important scheduler/error messages.
engine = create_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO)
SessionLocal = sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
