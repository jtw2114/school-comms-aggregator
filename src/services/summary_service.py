"""Claude API integration for generating daily summaries from communications."""

import json
import logging
from datetime import date, datetime, timedelta

import anthropic

from src.config.settings import CLAUDE_MODEL, SUMMARY_ROLLING_DAYS
from src.models.base import get_session
from src.models.communication import CommunicationItem, DailySummary
from src.services.credential_manager import get_claude_api_key
from src.utils.html_utils import strip_html

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """\
You are a helpful assistant that analyzes school communications for a parent.
You will be given a set of emails and activity feed items from a single day.
Extract and categorize the information into exactly four categories plus a structured overview.

Context: The parent has two children at BISC (school):
- Nia Whyte is in the Lovable Lambs room
- Zoe Whyte is in the Hedgehogs room

Respond with valid JSON matching this schema:
{
  "key_dates": ["string describing each upcoming date/event mentioned"],
  "deadlines": ["string describing each deadline or due date mentioned"],
  "curriculum_updates": ["string describing each curriculum/learning update"],
  "action_items": ["string describing each thing requiring parent action"],
  "overview": {
    "nia_whyte_lovable_lambs": "2-3 sentence summary of Nia's day, activities, and any updates specific to her or the Lovable Lambs room",
    "zoe_whyte_hedgehogs": "2-3 sentence summary of Zoe's day, activities, and any updates specific to her or the Hedgehogs room",
    "general_bisc": "2-3 sentence summary of school-wide updates, announcements, or items not specific to either child"
  }
}

Rules:
- Each array item should be a concise, actionable string (e.g., "Feb 14 - Valentine's Day party, bring cards for 14 students")
- Include specific dates when mentioned
- If a category has no items, return an empty array
- For action_items, start with the action verb (e.g., "Sign permission slip for...", "Send $15 for...")
- For overview sections, if there is no information for a particular child or general updates, use an empty string
- Only include information actually present in the communications, do not invent items
- Return ONLY valid JSON, no markdown formatting
"""


class SummaryService:
    """Generates daily summaries using Claude API."""

    def __init__(self):
        api_key = get_claude_api_key()
        if not api_key:
            raise RuntimeError("Claude API key not set. Configure it in Settings.")
        self._client = anthropic.Anthropic(api_key=api_key)

    def generate_rolling_summaries(self, days: int = SUMMARY_ROLLING_DAYS, force: bool = False):
        """Generate summaries for the past N days, skipping days with no new content."""
        today = date.today()
        session = get_session()

        try:
            for i in range(days):
                target_date = today - timedelta(days=i)
                self._generate_day_summary(session, target_date, force=force)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        # Sync checklist items from the newly generated summaries
        try:
            self._sync_checklist_from_summaries(days)
        except Exception:
            logger.warning("Failed to sync checklist from summaries", exc_info=True)

    def _generate_day_summary(self, session, target_date: date, force: bool = False):
        """Generate or update summary for a single day."""
        date_str = target_date.isoformat()

        # Get all items for this day
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date, datetime.max.time())

        items = (
            session.query(CommunicationItem)
            .filter(CommunicationItem.timestamp >= day_start)
            .filter(CommunicationItem.timestamp <= day_end)
            .order_by(CommunicationItem.timestamp)
            .all()
        )

        if not items:
            return  # No communications this day

        current_item_ids = sorted([item.id for item in items])
        current_ids_json = json.dumps(current_item_ids)

        # Check if summary exists and is up to date
        existing = session.query(DailySummary).filter_by(date=date_str).first()
        if existing and not force:
            if existing.source_item_ids == current_ids_json:
                logger.debug(f"Summary for {date_str} is up to date, skipping")
                return

        # Build prompt content from items
        prompt_content = self._build_prompt_content(items, target_date)

        # Call Claude API
        logger.info(f"Generating summary for {date_str} ({len(items)} items)")
        response = self._client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_content}],
        )

        # Parse response
        response_text = response.content[0].text
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                logger.error(f"Failed to parse Claude response for {date_str}: {response_text[:200]}")
                parsed = {
                    "key_dates": [],
                    "deadlines": [],
                    "curriculum_updates": [],
                    "action_items": [],
                    "overview": {
                        "nia_whyte_lovable_lambs": "",
                        "zoe_whyte_hedgehogs": "",
                        "general_bisc": response_text[:500],
                    },
                }

        # Serialize the structured overview as JSON for storage in raw_summary
        overview = parsed.get("overview", {})
        if isinstance(overview, str):
            # Backwards compat: if model returned a plain string, treat as general
            overview = {
                "nia_whyte_lovable_lambs": "",
                "zoe_whyte_hedgehogs": "",
                "general_bisc": overview,
            }
        raw_summary_json = json.dumps(overview)

        # Store or update summary
        if existing:
            existing.key_dates = json.dumps(parsed.get("key_dates", []))
            existing.deadlines = json.dumps(parsed.get("deadlines", []))
            existing.curriculum_updates = json.dumps(parsed.get("curriculum_updates", []))
            existing.action_items = json.dumps(parsed.get("action_items", []))
            existing.raw_summary = raw_summary_json
            existing.source_item_ids = current_ids_json
            existing.generated_at = datetime.now()
        else:
            summary = DailySummary(
                date=date_str,
                key_dates=json.dumps(parsed.get("key_dates", [])),
                deadlines=json.dumps(parsed.get("deadlines", [])),
                curriculum_updates=json.dumps(parsed.get("curriculum_updates", [])),
                action_items=json.dumps(parsed.get("action_items", [])),
                raw_summary=raw_summary_json,
                source_item_ids=current_ids_json,
                generated_at=datetime.now(),
            )
            session.add(summary)

    def _build_prompt_content(self, items: list[CommunicationItem], target_date: date) -> str:
        """Build the user prompt from communication items."""
        parts = [f"Communications for {target_date.strftime('%A, %B %d, %Y')}:\n"]

        for i, item in enumerate(items, 1):
            parts.append(f"--- Item {i} ({item.source.upper()}) ---")
            parts.append(f"Subject: {item.title}")
            parts.append(f"From: {item.sender}")
            parts.append(f"Time: {item.timestamp.strftime('%I:%M %p')}")

            # Use plain text body, falling back to stripped HTML
            body = item.body_plain
            if not body and item.body_html:
                body = strip_html(item.body_html)
            if body:
                # Truncate very long bodies to manage token usage
                if len(body) > 3000:
                    body = body[:3000] + "\n[... truncated ...]"
                parts.append(f"Content:\n{body}")

            if item.bw_student_name:
                parts.append(f"Student: {item.bw_student_name}")
            if item.bw_action_type:
                parts.append(f"Activity Type: {item.bw_action_type}")

            parts.append("")

        return "\n".join(parts)

    def get_rolling_summaries(self, days: int = SUMMARY_ROLLING_DAYS) -> dict[str, DailySummary]:
        """Load existing summaries for the rolling window from the database.

        Returns dict mapping date string to DailySummary.
        """
        today = date.today()
        session = get_session()
        try:
            date_strings = [(today - timedelta(days=i)).isoformat() for i in range(days)]
            summaries = (
                session.query(DailySummary)
                .filter(DailySummary.date.in_(date_strings))
                .all()
            )
            # Detach from session so they can be used after close
            result = {}
            for s in summaries:
                session.expunge(s)
                result[s.date] = s
            return result
        finally:
            session.close()

    def get_aggregated_summary(self, days: int = SUMMARY_ROLLING_DAYS) -> dict[str, list[str]]:
        """Get aggregated summary items across the rolling window.

        Returns dict with keys: key_dates, deadlines, curriculum_updates, action_items.
        Each value is a deduplicated list of strings.
        """
        summaries = self.get_rolling_summaries(days)

        aggregated: dict[str, list[str]] = {
            "key_dates": [],
            "deadlines": [],
            "curriculum_updates": [],
            "action_items": [],
        }

        seen: dict[str, set[str]] = {k: set() for k in aggregated}

        for date_str in sorted(summaries.keys(), reverse=True):
            s = summaries[date_str]
            for category in aggregated:
                items = getattr(s, f"{category}_list", [])
                for item in items:
                    normalized = item.strip().lower()
                    if normalized not in seen[category]:
                        seen[category].add(normalized)
                        aggregated[category].append(item)

        return aggregated

    def get_rolling_raw_summaries(self, days: int = SUMMARY_ROLLING_DAYS) -> dict[str, list[str]]:
        """Aggregate structured overview summaries across the rolling window.

        Returns a dict with keys: nia_whyte_lovable_lambs, zoe_whyte_hedgehogs, general_bisc.
        Each value is a list of "date: summary" strings.
        """
        summaries = self.get_rolling_summaries(days)
        result: dict[str, list[str]] = {
            "nia_whyte_lovable_lambs": [],
            "zoe_whyte_hedgehogs": [],
            "general_bisc": [],
        }

        for date_str in sorted(summaries.keys(), reverse=True):
            s = summaries[date_str]
            if not s.raw_summary:
                continue

            # Try to parse as structured JSON; fall back to legacy plain text
            try:
                overview = json.loads(s.raw_summary)
            except (json.JSONDecodeError, TypeError):
                # Legacy format: plain text string — put into general_bisc
                overview = {"general_bisc": s.raw_summary}

            for key in result:
                text = overview.get(key, "")
                if text and text.strip():
                    result[key].append(f"{date_str}: {text.strip()}")

        return result

    def _sync_checklist_from_summaries(self, days: int = SUMMARY_ROLLING_DAYS):
        """Sync aggregated action_items and key_dates to the checklist table.

        Called after generate_rolling_summaries commits.
        """
        from src.services.checklist_service import ChecklistService

        aggregated = self.get_aggregated_summary(days)
        checklist_svc = ChecklistService()

        for category in ("action_items", "key_dates"):
            items = aggregated.get(category, [])
            checklist_svc.sync_items_from_summary(category, items)
