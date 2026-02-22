"""Filter toolbar for the communications view: source, type, date range, search."""

from datetime import date, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
)


class FilterToolbar(QWidget):
    """Horizontal bar with source, type, date range, and search filters."""

    filters_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FilterToolbar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Source filter
        layout.addWidget(QLabel("Source:"))
        self._source_combo = QComboBox()
        self._source_combo.addItems(["All", "Gmail", "Brightwheel", "WhatsApp"])
        self._source_combo.currentIndexChanged.connect(self._emit_changed)
        layout.addWidget(self._source_combo)

        # Type filter (Brightwheel activity types)
        layout.addWidget(QLabel("Type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(["All", "Email", "Activity", "Note", "Photo", "Check-in", "Check-out"])
        self._type_combo.currentIndexChanged.connect(self._emit_changed)
        layout.addWidget(self._type_combo)

        # Date range
        layout.addWidget(QLabel("From:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(date.today() - timedelta(days=30))
        self._date_from.dateChanged.connect(self._emit_changed)
        layout.addWidget(self._date_from)

        layout.addWidget(QLabel("To:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(date.today())
        self._date_to.dateChanged.connect(self._emit_changed)
        layout.addWidget(self._date_to)

        # Search
        layout.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search title, body...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._emit_changed)
        layout.addWidget(self._search_input, 1)

    def _emit_changed(self):
        self.filters_changed.emit()

    @property
    def source_filter(self) -> str | None:
        """Returns 'gmail', 'brightwheel', or None for all."""
        text = self._source_combo.currentText().lower()
        return text if text != "all" else None

    @property
    def type_filter(self) -> str | None:
        text = self._type_combo.currentText().lower()
        return text if text != "all" else None

    @property
    def date_from(self) -> date:
        return self._date_from.date().toPython()

    @property
    def date_to(self) -> date:
        return self._date_to.date().toPython()

    @property
    def search_text(self) -> str:
        return self._search_input.text().strip()
