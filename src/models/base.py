"""SQLAlchemy engine and session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config.settings import DB_PATH, ensure_dirs


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        ensure_dirs()
        _engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def init_db():
    """Create all tables."""
    from src.models.communication import (  # noqa: F401
        Attachment,
        CommunicationItem,
        DailySummary,
        SyncState,
    )

    Base.metadata.create_all(get_engine())


def get_session():
    """Get a new database session."""
    factory = get_session_factory()
    return factory()
