"""Persistent checklist service for action items and key dates."""

import difflib
import logging
from datetime import datetime

from src.models.base import get_session
from src.models.communication import ChecklistItem

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 0.75


class ChecklistService:
    """Manages persistent checklist items that carry across syncs."""

    def get_checklist_items(self, category: str) -> list[ChecklistItem]:
        """Return all checklist items for a category, ordered by creation date."""
        session = get_session()
        try:
            items = (
                session.query(ChecklistItem)
                .filter_by(category=category)
                .order_by(ChecklistItem.created_at)
                .all()
            )
            for item in items:
                session.expunge(item)
            return items
        finally:
            session.close()

    def get_unchecked_items(self, category: str) -> list[ChecklistItem]:
        """Return unchecked checklist items for a category."""
        session = get_session()
        try:
            items = (
                session.query(ChecklistItem)
                .filter_by(category=category, is_checked=False)
                .order_by(ChecklistItem.created_at)
                .all()
            )
            for item in items:
                session.expunge(item)
            return items
        finally:
            session.close()

    def get_checked_items(self, category: str) -> list[ChecklistItem]:
        """Return checked (archived) checklist items for a category."""
        session = get_session()
        try:
            items = (
                session.query(ChecklistItem)
                .filter_by(category=category, is_checked=True)
                .order_by(ChecklistItem.checked_at.desc())
                .all()
            )
            for item in items:
                session.expunge(item)
            return items
        finally:
            session.close()

    def toggle_item(self, item_id: int) -> bool:
        """Toggle the checked state of an item. Returns new checked state."""
        session = get_session()
        try:
            item = session.query(ChecklistItem).get(item_id)
            if not item:
                return False
            item.is_checked = not item.is_checked
            item.checked_at = datetime.now() if item.is_checked else None
            session.commit()
            return item.is_checked
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def set_item_checked(self, item_id: int, checked: bool):
        """Explicitly set the checked state of an item."""
        session = get_session()
        try:
            item = session.query(ChecklistItem).get(item_id)
            if not item:
                return
            item.is_checked = checked
            item.checked_at = datetime.now() if checked else None
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def sync_items_from_summary(self, category: str, new_texts: list[str]):
        """Sync new summary items against existing checklist items.

        Uses fuzzy matching to preserve checked state for items that match.
        Adds new items, removes unchecked items that disappeared, but keeps
        checked items even if they no longer appear in summaries.
        """
        session = get_session()
        try:
            existing = (
                session.query(ChecklistItem)
                .filter_by(category=category)
                .all()
            )

            existing_map = {item.id: item for item in existing}
            matched_existing_ids = set()
            matched_new_indices = set()

            # Match new texts against existing items using fuzzy matching
            for new_idx, new_text in enumerate(new_texts):
                best_match_id = None
                best_ratio = 0.0

                for item_id, item in existing_map.items():
                    if item_id in matched_existing_ids:
                        continue
                    ratio = difflib.SequenceMatcher(
                        None, item.item_text.lower(), new_text.lower()
                    ).ratio()
                    if ratio > best_ratio and ratio >= MATCH_THRESHOLD:
                        best_ratio = ratio
                        best_match_id = item_id

                if best_match_id is not None:
                    # Update text but preserve checked state
                    matched_existing_ids.add(best_match_id)
                    matched_new_indices.add(new_idx)
                    existing_map[best_match_id].item_text = new_text

            # Add new items that didn't match anything
            for new_idx, new_text in enumerate(new_texts):
                if new_idx not in matched_new_indices:
                    new_item = ChecklistItem(
                        category=category,
                        item_text=new_text,
                        is_checked=False,
                        created_at=datetime.now(),
                    )
                    session.add(new_item)

            # Remove unmatched unchecked items (they disappeared from summaries)
            # But keep checked items even if they disappeared
            for item_id, item in existing_map.items():
                if item_id not in matched_existing_ids and not item.is_checked:
                    session.delete(item)

            session.commit()
            logger.info(
                f"Checklist sync [{category}]: {len(matched_existing_ids)} matched, "
                f"{len(new_texts) - len(matched_new_indices)} added, "
                f"{sum(1 for iid in existing_map if iid not in matched_existing_ids and not existing_map[iid].is_checked)} removed"
            )
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
