"""Collapsible card widget for displaying a summary category (dates, deadlines, etc.)."""

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

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setStyleSheet("""
            SummaryCard {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin: 4px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        # Header
        header_text = f"{icon}  {title}" if icon else title
        self._header = QLabel(f"<b style='font-size:14px;'>{header_text}</b>")
        layout.addWidget(self._header)

        # Items container
        self._items_widget = QWidget()
        self._items_layout = QVBoxLayout(self._items_widget)
        self._items_layout.setContentsMargins(8, 4, 0, 4)
        self._items_layout.setSpacing(2)
        layout.addWidget(self._items_widget)

        # Empty state
        self._empty_label = QLabel("<i style='color:#999;'>No items</i>")
        self._empty_label.setVisible(True)
        self._items_layout.addWidget(self._empty_label)

    def set_items(self, items: list[str]):
        """Replace the displayed items."""
        # Clear existing
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            self._empty_label = QLabel("<i style='color:#999;'>No items</i>")
            self._items_layout.addWidget(self._empty_label)
            return

        for item_text in items:
            bullet = QLabel(f"  \u2022  {item_text}")
            bullet.setWordWrap(True)
            bullet.setStyleSheet("font-size: 13px; padding: 2px 0;")
            self._items_layout.addWidget(bullet)

    def clear(self):
        """Clear all items."""
        self.set_items([])
