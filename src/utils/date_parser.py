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

# Pattern matches: "Feb 14", "March 5th", "Mar. 1", "January 23rd", etc.
DATE_PATTERN = re.compile(
    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+(\d{1,2})(?:st|nd|rd|th)?',
    re.IGNORECASE
)


def extract_date_from_text(text: str, reference_year: int | None = None) -> date | None:
    """Extract the first date mention from item text.

    Returns None if no date found.
    Infers year: if the date is more than 2 months in the past, assume next year.
    """
    match = DATE_PATTERN.search(text)
    if not match:
        return None

    month_str = match.group(1).lower()[:3]
    day = int(match.group(2))
    month = MONTH_MAP.get(month_str)

    if not month or day < 1 or day > 31:
        return None

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
