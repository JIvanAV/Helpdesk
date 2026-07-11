"""Database configuration for Ivan Helpdesk."""

from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Database file lives in ../data/helpdesk.db relative to this file
DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "helpdesk.db"

# SQLite engine with thread-safety for FastAPI
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    echo=False,  # Set True for SQL debugging
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Call on startup."""
    Base.metadata.create_all(bind=engine)

    # Pequena migração para bancos locais já criados antes deste campo existir.
    with engine.begin() as conn:
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info(tickets)"))]
        if "feedback" not in columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN feedback INTEGER"))
        if "origin" not in columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN origin VARCHAR(50) NOT NULL DEFAULT 'portal'"))
        if "internal_comments" not in columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN internal_comments TEXT"))
