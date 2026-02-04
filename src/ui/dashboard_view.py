"""Dashboard tab: 8-day rolling summary with key dates, deadlines, curriculum, actions."""

from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import SUMMARY_ROLLING_DAYS
from src.ui.widgets.summary_card import SummaryCard
from src.ui.widgets.day_section import DaySection
from src.utils.date_utils import get_rolling_date_range


class DashboardView(QWidget):
    """Main dashboard with 4 summary sections and day-by-day breakdown."""

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

        # Title
        title = QLabel("<h2>8-Day Rolling Summary</h2>")
        self._layout.addWidget(title)

        # Summary cards
        self._key_dates_card = SummaryCard("KEY DATES", "\U0001F4C5")
        self._layout.addWidget(self._key_dates_card)

        self._deadlines_card = SummaryCard("DEADLINES", "\u26A0\uFE0F")
        self._layout.addWidget(self._deadlines_card)

        self._curriculum_card = SummaryCard("CURRICULUM UPDATES", "\U0001F4DA")
        self._layout.addWidget(self._curriculum_card)

        self._action_items_card = SummaryCard("ACTION ITEMS", "\u2705")
        self._layout.addWidget(self._action_items_card)

        # Day-by-day breakdown
        separator = QLabel("<hr><b style='font-size:13px;'>Day-by-day breakdown</b>")
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
        """Reload summary data from database."""
        try:
            from src.services.summary_service import SummaryService
            svc = SummaryService()
            agg = svc.get_aggregated_summary()

            self._key_dates_card.set_items(agg["key_dates"])
            self._deadlines_card.set_items(agg["deadlines"])
            self._curriculum_card.set_items(agg["curriculum_updates"])
            self._action_items_card.set_items(agg["action_items"])
        except Exception:
            # No API key or no summaries yet - show empty state
            self._key_dates_card.set_items([])
            self._deadlines_card.set_items([])
            self._curriculum_card.set_items([])
            self._action_items_card.set_items([])

        # Refresh day sections
        for section in self._day_sections:
            section.refresh()
