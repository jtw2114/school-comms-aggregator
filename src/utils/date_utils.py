"""Date utility functions."""

from datetime import date, datetime, timedelta

from src.config.settings import SUMMARY_ROLLING_DAYS


def get_rolling_date_range(days: int = SUMMARY_ROLLING_DAYS) -> list[date]:
    """Return a list of dates for the rolling window, most recent first."""
    today = date.today()
    return [today - timedelta(days=i) for i in range(days)]


def date_label(d: date) -> str:
    """Human-readable label for a date relative to today."""
    today = date.today()
    diff = (today - d).days
    if diff == 0:
        return "Today"
    elif diff == 1:
        return "Yesterday"
    else:
        return d.strftime("%b %d")


def parse_timestamp(ts: str | int | float | datetime) -> datetime:
    """Normalize various timestamp formats to datetime."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, (int, float)):
        # Unix timestamp (seconds or milliseconds)
        if ts > 1e12:
            ts = ts / 1000
        return datetime.fromtimestamp(ts)
    if isinstance(ts, str):
        # Try ISO format first
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(ts, fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse timestamp: {ts}")
    raise TypeError(f"Unexpected timestamp type: {type(ts)}")
