"""Communications tab: unified list of all items with filters and detail panel."""

from datetime import datetime

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.models.base import get_session
from src.models.communication import CommunicationItem
from src.ui.detail_panel import DetailPanel
from src.ui.filter_toolbar import FilterToolbar
from src.ui.widgets.communication_card import CommunicationCard


class CommunicationsView(QWidget):
    """Full communications list with filtering and detail panel."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Filter toolbar
        self._filters = FilterToolbar()
        self._filters.filters_changed.connect(self._apply_filters)
        layout.addWidget(self._filters)

        # Splitter: list | detail
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: scrollable list of cards
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self._list_scroll = QScrollArea()
        self._list_scroll.setWidgetResizable(True)
        self._list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_scroll.setMinimumWidth(300)

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()
        self._list_scroll.setWidget(self._list_widget)

        list_layout.addWidget(self._list_scroll)
        splitter.addWidget(list_container)

        # Right: detail panel
        self._detail = DetailPanel()
        splitter.addWidget(self._detail)

        splitter.setSizes([350, 650])
        layout.addWidget(splitter, 1)

        self._cards: list[CommunicationCard] = []
        self._selected_id: int | None = None

        # Initial load
        self.refresh()

    def refresh(self):
        """Reload the communications list with current filters."""
        self._apply_filters()

    @Slot()
    def _apply_filters(self):
        """Query database with current filters and rebuild the list."""
        session = get_session()
        try:
            query = session.query(CommunicationItem)

            # Source filter
            source = self._filters.source_filter
            if source:
                query = query.filter(CommunicationItem.source == source)

            # Type filter
            type_filter = self._filters.type_filter
            if type_filter:
                if type_filter == "email":
                    query = query.filter(CommunicationItem.source == "gmail")
                else:
                    query = query.filter(
                        CommunicationItem.bw_action_type.ilike(f"%{type_filter}%")
                    )

            # Date range
            date_from = datetime.combine(self._filters.date_from, datetime.min.time())
            date_to = datetime.combine(self._filters.date_to, datetime.max.time())
            query = query.filter(CommunicationItem.timestamp >= date_from)
            query = query.filter(CommunicationItem.timestamp <= date_to)

            # Search text
            search = self._filters.search_text
            if search:
                pattern = f"%{search}%"
                query = query.filter(
                    CommunicationItem.title.ilike(pattern)
                    | CommunicationItem.body_plain.ilike(pattern)
                    | CommunicationItem.sender.ilike(pattern)
                )

            # Order by newest first, limit to 200
            items = query.order_by(CommunicationItem.timestamp.desc()).limit(200).all()

            self._rebuild_list(items)

        finally:
            session.close()

    def _rebuild_list(self, items: list[CommunicationItem]):
        """Clear and rebuild the card list."""
        # Remove old cards
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        # Remove stretch
        while self._list_layout.count():
            child = self._list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            empty = QLabel("<i style='color:#999;padding:20px;'>No communications found</i>")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list_layout.addWidget(empty)
            self._list_layout.addStretch()
            return

        for item in items:
            card = CommunicationCard(
                item_id=item.id,
                title=item.title,
                sender=item.sender,
                timestamp_str=item.timestamp.strftime("%b %d, %I:%M %p"),
                source=item.source,
                preview=item.body_plain or "",
            )
            card.clicked.connect(self._on_card_clicked)
            self._cards.append(card)
            self._list_layout.addWidget(card)

        self._list_layout.addStretch()

    @Slot(int)
    def _on_card_clicked(self, item_id: int):
        """Handle card selection."""
        self._selected_id = item_id

        # Update card selection state
        for card in self._cards:
            card.set_selected(card._item_id == item_id)

        # Show detail
        self._detail.show_item(item_id)
