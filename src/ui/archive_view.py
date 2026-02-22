"""Archive view showing completed (checked) checklist items."""

import logging

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.checklist_card import ChecklistCard
from src.ui.widgets.find_bar import FindBar
from src.utils.date_parser import sort_items_by_date, sort_items_alphabetically

logger = logging.getLogger(__name__)


class ArchiveView(QWidget):
    """Archive view showing completed checklist items that can be unchecked to restore."""

    checklist_changed = Signal()  # Emitted when an item is toggled

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

        # Header
        title = QLabel("\U0001F4E6 Completed Items Archive")
        title.setObjectName("page_title")
        self._layout.addWidget(title)

        description = QLabel("Uncheck an item to move it back to the Dashboard.")
        description.setObjectName("caption")
        description.setWordWrap(True)
        self._layout.addWidget(description)

        # Search bar
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter archived items...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setMaximumWidth(350)
        self._search_input.textChanged.connect(self._on_filter)
        self._layout.addWidget(self._search_input)

        # Archived Key Dates
        self._key_dates_card = ChecklistCard("Archived Key Dates", "\U0001F4C5")
        self._key_dates_card.item_toggled.connect(self._on_checklist_toggled)
        self._layout.addWidget(self._key_dates_card)

        # Archived Action Items
        self._action_items_card = ChecklistCard("Archived Action Items", "\u2705")
        self._action_items_card.item_toggled.connect(self._on_checklist_toggled)
        self._layout.addWidget(self._action_items_card)

        self._layout.addStretch()

        # Load initial data
        self.refresh()

    def refresh(self):
        """Reload archived (checked) items from database."""
        try:
            from src.services.checklist_service import ChecklistService
            checklist_svc = ChecklistService()

            # Key dates: sort chronologically
            key_dates_items = checklist_svc.get_checked_items("key_dates")
            key_dates_items = sort_items_by_date(key_dates_items)
            self._key_dates_card.set_checklist_items(
                [(item.id, item.item_text, item.is_checked) for item in key_dates_items]
            )

            # Action items: sort alphabetically
            action_items = checklist_svc.get_checked_items("action_items")
            action_items = sort_items_alphabetically(action_items)
            self._action_items_card.set_checklist_items(
                [(item.id, item.item_text, item.is_checked) for item in action_items]
            )
        except Exception:
            logger.warning("Failed to load archived items", exc_info=True)
            self._key_dates_card.set_checklist_items([])
            self._action_items_card.set_checklist_items([])

    @Slot(str)
    def _on_filter(self, query: str):
        """Filter checklist cards based on search query."""
        for card in [self._key_dates_card, self._action_items_card]:
            visible_count = card.filter_text(query)
            card.setVisible(visible_count > 0 or not query)

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
