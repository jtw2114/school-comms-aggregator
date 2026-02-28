"""Date extraction service for populating event_date on checklist items."""

import logging
from datetime import date

from src.utils.date_parser import extract_date_from_text

logger = logging.getLogger(__name__)


def extract_event_date(item_text: str, reference_date: date | None = None) -> date | None:
    """Extract an event date from checklist item text.

    Step 1: Use regex-based extraction from date_parser.
    Step 2: If regex fails and Claude API key is available, use Claude.
    """
    ref_year = reference_date.year if reference_date else None
    result = extract_date_from_text(item_text, reference_year=ref_year)
    if result:
        return result

    # Step 2: Try Claude API for harder-to-parse dates
    try:
        from src.services.credential_manager import get_claude_api_key
        api_key = get_claude_api_key()
        if not api_key:
            return None

        import anthropic
        from src.config.settings import CLAUDE_MODEL

        client = anthropic.Anthropic(api_key=api_key)
        today = reference_date or date.today()
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": (
                    f"Today is {today.isoformat()}. "
                    f"Extract the event date from this text and return ONLY an ISO date (YYYY-MM-DD) or 'none':\n"
                    f"{item_text}"
                ),
            }],
        )
        text = response.content[0].text.strip()
        if text and text != "none":
            return date.fromisoformat(text)
    except Exception:
        logger.debug("Claude date extraction failed for: %s", item_text, exc_info=True)

    return None


def backfill_event_dates():
    """Backfill event_date for all checklist items where it is NULL."""
    from src.models.base import get_session
    from src.models.communication import ChecklistItem

    session = get_session()
    try:
        items = (
            session.query(ChecklistItem)
            .filter(ChecklistItem.event_date.is_(None))
            .all()
        )
        if not items:
            return

        updated = 0
        for item in items:
            event_date = extract_event_date(item.item_text)
            if event_date:
                item.event_date = event_date
                updated += 1

        if updated:
            session.commit()
            logger.info(f"Backfilled event_date for {updated} checklist item(s)")
    except Exception:
        session.rollback()
        logger.warning("Failed to backfill event dates", exc_info=True)
    finally:
        session.close()
