"""SQLAlchemy engine and session factory."""

import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config.settings import DB_PATH, ensure_dirs

logger = logging.getLogger(__name__)


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
        ChecklistItem,
        CommunicationItem,
        DailySummary,
        SyncState,
    )

    Base.metadata.create_all(get_engine())
    _migrate_attachment_extracted_text()


def _migrate_attachment_extracted_text():
    """Add extracted_text column to attachments table if missing (safe migration)."""
    engine = get_engine()
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("attachments")]
    if "extracted_text" not in columns:
        logger.info("Migrating: adding extracted_text column to attachments table")
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE attachments ADD COLUMN extracted_text TEXT"))


def get_session():
    """Get a new database session."""
    factory = get_session_factory()
    return factory()
