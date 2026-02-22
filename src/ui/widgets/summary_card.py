"""Card widget for displaying a summary category (dates, deadlines, etc.)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SummaryCard(QFrame):
    """A styled card with a title/icon header and a list of bullet items."""

    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._title_text = title
        self._icon = icon

        self.setObjectName("SummaryCard")
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header
        header_text = f"{icon}  {title}" if icon else title
        self._header = QLabel(header_text)
        self._header.setObjectName("card_header")
        layout.addWidget(self._header)

        # Items container
        self._items_widget = QWidget()
        self._items_layout = QVBoxLayout(self._items_widget)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(4)
        layout.addWidget(self._items_widget)

        self._item_labels: list[QLabel] = []

        # Empty state
        self._empty_label = QLabel("No items")
        self._empty_label.setObjectName("caption")
        self._empty_label.setVisible(True)
        self._items_layout.addWidget(self._empty_label)

    def set_items(self, items: list[str]):
        """Replace the displayed items."""
        # Clear existing
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._item_labels: list[QLabel] = []

        if not items:
            self._empty_label = QLabel("No items")
            self._empty_label.setObjectName("caption")
            self._items_layout.addWidget(self._empty_label)
            return

        for item_text in items:
            bullet = QLabel(f"•  {item_text}")
            bullet.setWordWrap(True)
            self._item_labels.append(bullet)
            self._items_layout.addWidget(bullet)

    def filter_text(self, query: str) -> int:
        """Show/hide bullet items matching query. Returns count of visible items."""
        if not query:
            for label in self._item_labels:
                label.setVisible(True)
            return len(self._item_labels)

        query_lower = query.lower()
        visible = 0
        for label in self._item_labels:
            matches = query_lower in label.text().lower()
            label.setVisible(matches)
            if matches:
                visible += 1
        return visible

    def clear(self):
        """Clear all items."""
        self.set_items([])
