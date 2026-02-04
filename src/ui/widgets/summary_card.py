"""Collapsible card widget for displaying a summary category (dates, deadlines, etc.)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme import COLORS


class SummaryCard(QFrame):
    """A styled card with a title/icon header and a list of bullet items."""

    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._title_text = title
        self._icon = icon

        self.setObjectName("SummaryCard")
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Accent strip at top
        accent_strip = QFrame()
        accent_strip.setFixedHeight(4)
        accent_strip.setStyleSheet(f"background-color: {COLORS['accent']}; border-radius: 0;")
        layout.addWidget(accent_strip)

        # Content area
        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(14, 10, 14, 10)
        self._content_layout.setSpacing(4)
        layout.addWidget(content)

        # Header
        header_text = f"{icon}  {title}" if icon else title
        self._header = QLabel(
            f"<b style='font-size:14px;color:{COLORS['navy']};'>{header_text}</b>"
        )
        self._content_layout.addWidget(self._header)

        # Items container
        self._items_widget = QWidget()
        self._items_layout = QVBoxLayout(self._items_widget)
        self._items_layout.setContentsMargins(8, 4, 0, 4)
        self._items_layout.setSpacing(2)
        self._content_layout.addWidget(self._items_widget)

        # Empty state
        self._empty_label = QLabel(f"<i style='color:{COLORS['text_muted']};'>No items</i>")
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
            self._empty_label = QLabel(f"<i style='color:{COLORS['text_muted']};'>No items</i>")
            self._items_layout.addWidget(self._empty_label)
            return

        for item_text in items:
            bullet = QLabel(
                f"<table cellpadding='0' cellspacing='0'><tr>"
                f"<td style='vertical-align:top;padding-right:6px;'>\u2022</td>"
                f"<td>{item_text}</td>"
                f"</tr></table>"
            )
            bullet.setTextFormat(Qt.TextFormat.RichText)
            bullet.setWordWrap(True)
            self._items_layout.addWidget(bullet)

    def clear(self):
        """Clear all items."""
        self.set_items([])
