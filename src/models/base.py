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
    _migrate_fix_pdf_mimetypes()


def _migrate_attachment_extracted_text():
    """Add extracted_text column to attachments table if missing (safe migration)."""
    engine = get_engine()
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("attachments")]
    if "extracted_text" not in columns:
        logger.info("Migrating: adding extracted_text column to attachments table")
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE attachments ADD COLUMN extracted_text TEXT"))


def _migrate_fix_pdf_mimetypes():
    """Fix attachments that have PDF URLs but wrong mime_type (one-time fixup)."""
    from urllib.parse import unquote, urlparse

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        from src.models.communication import Attachment

        # Find attachments where the URL path ends in .pdf but mime_type is wrong
        candidates = (
            session.query(Attachment)
            .filter(
                Attachment.remote_url.like("%.pdf%"),
                Attachment.mime_type != "application/pdf",
            )
            .all()
        )

        fixed = 0
        for att in candidates:
            try:
                path = urlparse(att.remote_url).path
                if path.lower().endswith(".pdf"):
                    att.mime_type = "application/pdf"
                    # Fix garbled filename too
                    clean_name = unquote(path.rsplit("/", 1)[-1])
                    if clean_name:
                        att.filename = clean_name
                    fixed += 1
            except Exception:
                continue

        if fixed:
            session.commit()
            logger.info(f"Fixed mime_type for {fixed} PDF attachment(s)")
    except Exception:
        session.rollback()
        logger.warning("Failed to fix PDF mime types", exc_info=True)
    finally:
        session.close()


def get_session():
    """Get a new database session."""
    factory = get_session_factory()
    return factory()
