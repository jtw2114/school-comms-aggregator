"""Dashboard tab: 14-day rolling summary with overview, checklists, and day-by-day breakdown."""

import logging

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import SUMMARY_ROLLING_DAYS
from src.ui.widgets.find_bar import FindBar
from src.ui.widgets.summary_card import SummaryCard
from src.ui.widgets.checklist_card import ChecklistCard
from src.ui.widgets.day_section import DaySection
from src.utils.date_utils import get_rolling_date_range

logger = logging.getLogger(__name__)


class DashboardView(QWidget):
    """Main dashboard with overview, checklists, summary sections, and day-by-day breakdown."""

    regenerate_requested = Signal()
    checklist_changed = Signal()  # Emitted when a checklist item is toggled

    def __init__(self, parent=None):
        super().__init__(parent)

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Scrollable content
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Find bar (Ctrl+F)
        self._find_bar = FindBar(self._scroll)
        outer.addWidget(self._find_bar)

        outer.addWidget(self._scroll)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setSpacing(16)
        self._scroll.setWidget(container)

        # Header row: title + regenerate button
        header_row = QHBoxLayout()
        title = QLabel("14-Day Rolling Summary")
        title.setObjectName("page_title")
        header_row.addWidget(title)
        header_row.addStretch()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter dashboard...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setMaximumWidth(250)
        self._search_input.textChanged.connect(self._on_filter)
        header_row.addWidget(self._search_input)

        self._regen_btn = QPushButton("Regenerate Summaries")
        self._regen_btn.clicked.connect(self._on_regenerate_clicked)
        header_row.addWidget(self._regen_btn)
        self._layout.addLayout(header_row)

        # Error label (hidden by default)
        self._error_label = QLabel()
        self._error_label.setObjectName("error_banner")
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        self._layout.addWidget(self._error_label)

        # Overview cards (one per child + general)
        self._nia_card = SummaryCard("Updates on Nia Whyte and the Lovable Lambs", "\U0001F411")
        self._layout.addWidget(self._nia_card)

        self._zoe_card = SummaryCard("Updates on Zoe Whyte and the Hedgehogs", "\U0001F994")
        self._layout.addWidget(self._zoe_card)

        self._general_card = SummaryCard("General BISC Updates", "\U0001F3EB")
        self._layout.addWidget(self._general_card)

        # Checklist cards (Key Dates + Action Items)
        self._key_dates_card = ChecklistCard("Key Dates", "\U0001F4C5")
        self._key_dates_card.item_toggled.connect(self._on_checklist_toggled)
        self._layout.addWidget(self._key_dates_card)

        self._action_items_card = ChecklistCard("Action Items", "\u2705")
        self._action_items_card.item_toggled.connect(self._on_checklist_toggled)
        self._layout.addWidget(self._action_items_card)

        # Summary cards (Deadlines + Curriculum)
        self._deadlines_card = SummaryCard("Deadlines", "\u26A0\uFE0F")
        self._layout.addWidget(self._deadlines_card)

        self._curriculum_card = SummaryCard("Curriculum Updates", "\U0001F4DA")
        self._layout.addWidget(self._curriculum_card)

        # Day-by-day breakdown section header
        section_header = QLabel("Day-by-day breakdown")
        section_header.setObjectName("section_header")
        self._layout.addWidget(section_header)

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
            from src.utils.date_parser import sort_strings_by_date
            svc = SummaryService()
            agg = svc.get_aggregated_summary()

            # Overview: show structured summaries per child/general
            overview = svc.get_rolling_raw_summaries()
            self._nia_card.set_items(overview.get("nia_whyte_lovable_lambs", []))
            self._zoe_card.set_items(overview.get("zoe_whyte_hedgehogs", []))
            self._general_card.set_items(overview.get("general_bisc", []))

            # Sort deadlines chronologically
            self._deadlines_card.set_items(sort_strings_by_date(agg["deadlines"]))
            self._curriculum_card.set_items(agg["curriculum_updates"])
        except Exception:
            self._nia_card.set_items([])
            self._zoe_card.set_items([])
            self._general_card.set_items([])
            self._deadlines_card.set_items([])
            self._curriculum_card.set_items([])

        # Load unchecked checklist items
        try:
            from src.services.checklist_service import ChecklistService
            from src.utils.date_parser import sort_items_by_date, sort_items_alphabetically
            checklist_svc = ChecklistService()

            # Key dates: sort chronologically
            key_dates_items = checklist_svc.get_unchecked_items("key_dates")
            key_dates_items = sort_items_by_date(key_dates_items)
            self._key_dates_card.set_checklist_items(
                [(item.id, item.item_text, item.is_checked) for item in key_dates_items]
            )

            # Action items: sort alphabetically
            action_items = checklist_svc.get_unchecked_items("action_items")
            action_items = sort_items_alphabetically(action_items)
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
        """Persist checklist toggle to database and emit signal."""
        try:
            from src.services.checklist_service import ChecklistService
            svc = ChecklistService()
            svc.set_item_checked(item_id, checked)
            self.checklist_changed.emit()
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

    @Slot(str)
    def _on_filter(self, query: str):
        """Filter all cards and day sections based on search query."""
        cards = [
            self._nia_card, self._zoe_card, self._general_card,
            self._deadlines_card, self._curriculum_card,
            self._key_dates_card, self._action_items_card,
        ]
        for card in cards:
            visible_count = card.filter_text(query)
            card.setVisible(visible_count > 0 or not query)

        for section in self._day_sections:
            if section._items_loaded:
                visible_count = section.filter_text(query)
                section.setVisible(visible_count > 0 or not query)
            else:
                # Show unexpanded sections when no filter, hide when filtering
                section.setVisible(not query)

    def set_error(self, message: str):
        """Show an error message on the dashboard."""
        self._error_label.setText(message)
        self._error_label.setVisible(True)
