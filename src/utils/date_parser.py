"""Date extraction utility for parsing dates from checklist item text."""

import re
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.communication import ChecklistItem

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

# ISO format at start of text: "2026-02-14: ..." or "~2026-02-14: ..."
ISO_PREFIX_PATTERN = re.compile(r'^~?(\d{4})-(\d{2})-(\d{2})\b')

# Full ISO date anywhere: "2026-02-14"
ISO_PATTERN = re.compile(r'(\d{4})-(\d{2})-(\d{2})\b')

# Named month: "Feb 14", "March 5th", "Mar. 1", "January 23rd", etc.
NAMED_MONTH_PATTERN = re.compile(
    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+(\d{1,2})(?:st|nd|rd|th)?',
    re.IGNORECASE
)

# Numeric with year: "02/14/2026" or "2/14/2026"
NUMERIC_WITH_YEAR_PATTERN = re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b')

# Numeric without year: "2/14" or "02/14"
NUMERIC_SHORT_PATTERN = re.compile(r'\b(\d{1,2})/(\d{1,2})\b')


def _infer_year(month: int, day: int, reference_year: int | None) -> date | None:
    """Build a date, inferring year if needed. Returns None on invalid dates."""
    today = date.today()
    year = reference_year or today.year
    try:
        result = date(year, month, day)
        # If date is more than 2 months in the past, assume next year
        if (today - result).days > 60:
            result = date(year + 1, month, day)
        return result
    except ValueError:
        return None


def extract_date_from_text(text: str, reference_year: int | None = None) -> date | None:
    """Extract the first date mention from item text.

    Tries patterns in order of specificity:
    1. ISO prefix at start of line ("2026-02-14: ..." or "~2026-02-14: ...")
    2. Full ISO date anywhere ("2026-02-14")
    3. Numeric with year ("02/14/2026")
    4. Named month ("Feb 14", "March 5th", "January 23rd")
    5. Numeric without year ("2/14")

    Returns None if no date found.
    """
    # 1. ISO prefix at start (from structured prompt output)
    m = ISO_PREFIX_PATTERN.search(text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # 2. Full ISO date anywhere
    m = ISO_PATTERN.search(text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # 3. Numeric with explicit year: "02/14/2026"
    m = NUMERIC_WITH_YEAR_PATTERN.search(text)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    # 4. Named month: "Feb 14", "March 5th"
    m = NAMED_MONTH_PATTERN.search(text)
    if m:
        month_str = m.group(1).lower()[:3]
        day = int(m.group(2))
        month = MONTH_MAP.get(month_str)
        if month and 1 <= day <= 31:
            result = _infer_year(month, day, reference_year)
            if result:
                return result

    # 5. Numeric without year: "2/14"
    m = NUMERIC_SHORT_PATTERN.search(text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return _infer_year(month, day, reference_year)

    return None


def sort_items_by_date(items: list["ChecklistItem"]) -> list["ChecklistItem"]:
    """Sort ChecklistItem objects by extracted date, then created_at.

    Items with extractable dates come first (sorted by date),
    followed by items without dates (sorted by created_at).
    """
    def sort_key(item):
        extracted = extract_date_from_text(item.item_text)
        if extracted:
            return (0, extracted)  # Dated items first, sorted by date
        # Fallback to created_at for items without parseable dates
        fallback = item.created_at.date() if item.created_at else date.max
        return (1, fallback)

    return sorted(items, key=sort_key)


def sort_items_alphabetically(items: list["ChecklistItem"]) -> list["ChecklistItem"]:
    """Sort ChecklistItem objects alphabetically by item_text (case-insensitive)."""
    return sorted(items, key=lambda item: item.item_text.lower())


def sort_strings_by_date(strings: list[str]) -> list[str]:
    """Sort a list of strings by extracted date chronologically.

    Strings with extractable dates come first (sorted by date),
    followed by strings without dates (in original order).
    """
    def sort_key(text: str):
        extracted = extract_date_from_text(text)
        if extracted:
            return (0, extracted)  # Dated items first, sorted by date
        return (1, date.max)  # Undated items last

    return sorted(strings, key=sort_key)
