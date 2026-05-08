from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from src.infrastructure.config import Settings


settings = Settings()

if not settings.database_url:
    raise ValueError(
        "DATABASE_URL environment variable is not set. Set it to a SQLAlchemy "
        "database connection string, for example "
        "postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DATABASE."
    )

database_url = make_url(settings.database_url)
if database_url.drivername in {"http", "https"}:
    raise ValueError(
        "DATABASE_URL is an HTTP URL, but SQLAlchemy needs a database connection "
        "string. For Supabase, use the PostgreSQL direct or pooler connection "
        "URI from Project Settings > Database, not the project API URL."
    )

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
