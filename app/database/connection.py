from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config.settings import settings


Path("data").mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

Base = declarative_base()

def init_db() -> None:
    Base.metadata.create_all(bind=engine)