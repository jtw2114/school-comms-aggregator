"""Dashboard tab: 8-day rolling summary with overview, checklists, and day-by-day breakdown."""

import logging

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import SUMMARY_ROLLING_DAYS
from src.ui.theme import COLORS
from src.ui.widgets.summary_card import SummaryCard
from src.ui.widgets.checklist_card import ChecklistCard
from src.ui.widgets.day_section import DaySection
from src.utils.date_utils import get_rolling_date_range

logger = logging.getLogger(__name__)


class DashboardView(QWidget):
    """Main dashboard with overview, checklists, summary sections, and day-by-day breakdown."""

    regenerate_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)
        scroll.setWidget(container)

        # Header row: title + regenerate button
        header_row = QHBoxLayout()
        title = QLabel(
            f"<h2 style='color:{COLORS['navy']};margin:0;'>8-Day Rolling Summary</h2>"
        )
        header_row.addWidget(title)
        header_row.addStretch()

        self._regen_btn = QPushButton("Regenerate Summaries")
        self._regen_btn.clicked.connect(self._on_regenerate_clicked)
        header_row.addWidget(self._regen_btn)
        self._layout.addLayout(header_row)

        # Error label (hidden by default)
        self._error_label = QLabel()
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(
            f"color: {COLORS['error']}; background-color: rgba(224,80,80,0.1);"
            f"padding: 8px 12px; border-radius: 4px; font-size: 12px;"
        )
        self._error_label.setVisible(False)
        self._layout.addWidget(self._error_label)

        # Overview card (raw summary text)
        self._overview_card = SummaryCard("OVERVIEW", "\U0001F4CB")
        self._layout.addWidget(self._overview_card)

        # Checklist cards (Key Dates + Action Items)
        self._key_dates_card = ChecklistCard("KEY DATES", "\U0001F4C5")
        self._key_dates_card.item_toggled.connect(self._on_checklist_toggled)
        self._layout.addWidget(self._key_dates_card)

        self._action_items_card = ChecklistCard("ACTION ITEMS", "\u2705")
        self._action_items_card.item_toggled.connect(self._on_checklist_toggled)
        self._layout.addWidget(self._action_items_card)

        # Summary cards (Deadlines + Curriculum)
        self._deadlines_card = SummaryCard("DEADLINES", "\u26A0\uFE0F")
        self._layout.addWidget(self._deadlines_card)

        self._curriculum_card = SummaryCard("CURRICULUM UPDATES", "\U0001F4DA")
        self._layout.addWidget(self._curriculum_card)

        # Day-by-day breakdown
        separator = QLabel(
            f"<hr><b style='font-size:13px;color:{COLORS['navy']};'>Day-by-day breakdown</b>"
        )
        separator.setTextFormat(Qt.TextFormat.RichText)
        self._layout.addWidget(separator)

        self._day_sections: list[DaySection] = []
        for d in get_rolling_date_range():
            section = DaySection(d)
            self._day_sections.append(section)
            self._layout.addWidget(section)

        self._layout.addStretch()

        # Load initial data
        self.refresh()

    def refresh(self):
        """Reload summary and checklist data from database."""
        # Load summary data
        try:
            from src.services.summary_service import SummaryService
            svc = SummaryService()
            agg = svc.get_aggregated_summary()

            # Overview: show raw summary text
            raw_text = svc.get_rolling_raw_summaries()
            if raw_text:
                # Split into individual summary lines for display
                self._overview_card.set_items(
                    [line.strip() for line in raw_text.split("\n\n") if line.strip()]
                )
            else:
                self._overview_card.set_items([])

            self._deadlines_card.set_items(agg["deadlines"])
            self._curriculum_card.set_items(agg["curriculum_updates"])
        except Exception:
            self._overview_card.set_items([])
            self._deadlines_card.set_items([])
            self._curriculum_card.set_items([])

        # Load checklist items
        try:
            from src.services.checklist_service import ChecklistService
            checklist_svc = ChecklistService()

            key_dates_items = checklist_svc.get_checklist_items("key_dates")
            self._key_dates_card.set_checklist_items(
                [(item.id, item.item_text, item.is_checked) for item in key_dates_items]
            )

            action_items = checklist_svc.get_checklist_items("action_items")
            self._action_items_card.set_checklist_items(
                [(item.id, item.item_text, item.is_checked) for item in action_items]
            )
        except Exception:
            self._key_dates_card.set_checklist_items([])
            self._action_items_card.set_checklist_items([])

        # Refresh day sections
        for section in self._day_sections:
            section.refresh()

    @Slot(int, bool)
    def _on_checklist_toggled(self, item_id: int, checked: bool):
        """Persist checklist toggle to database."""
        try:
            from src.services.checklist_service import ChecklistService
            svc = ChecklistService()
            svc.set_item_checked(item_id, checked)
        except Exception:
            logger.warning("Failed to persist checklist toggle", exc_info=True)

    @Slot()
    def _on_regenerate_clicked(self):
        """Emit signal and disable button while regenerating."""
        self._regen_btn.setEnabled(False)
        self._regen_btn.setText("Regenerating...")
        self._error_label.setVisible(False)
        self.regenerate_requested.emit()

    def set_regenerate_enabled(self, enabled: bool):
        """Re-enable the regenerate button after completion."""
        self._regen_btn.setEnabled(enabled)
        self._regen_btn.setText("Regenerate Summaries")

    def set_error(self, message: str):
        """Show an error message on the dashboard."""
        self._error_label.setText(message)
        self._error_label.setVisible(True)
