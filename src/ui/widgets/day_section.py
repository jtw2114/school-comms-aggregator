"""Expandable day-by-day breakdown section for the dashboard."""

from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.models.base import get_session
from src.models.communication import CommunicationItem
from src.ui.theme import COLORS, source_badge_html
from src.utils.date_utils import date_label
from src.utils.html_utils import truncate_text


class DaySection(QFrame):
    """An expandable section showing all communications for a single day."""

    def __init__(self, target_date: date, parent=None):
        super().__init__(parent)
        self._date = target_date
        self._expanded = False
        self._items_loaded = False

        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"DaySection {{ border-bottom: 1px solid {COLORS['border_light']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        # Header row (clickable)
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 4, 0, 4)

        self._toggle_btn = QPushButton(self._header_text())
        self._toggle_btn.setFlat(True)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle)
        header_layout.addWidget(self._toggle_btn, 1)

        layout.addWidget(header)

        # Expandable content
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(24, 0, 8, 8)
        self._content_layout.setSpacing(4)
        self._content.setVisible(False)
        layout.addWidget(self._content)

    def _header_text(self) -> str:
        arrow = "\u25BC" if self._expanded else "\u25B6"
        label = date_label(self._date)
        count = self._get_item_count()
        return f"  {arrow}  {label} ({count} item{'s' if count != 1 else ''})"

    def _get_item_count(self) -> int:
        session = get_session()
        try:
            day_start = datetime.combine(self._date, datetime.min.time())
            day_end = datetime.combine(self._date, datetime.max.time())
            return (
                session.query(CommunicationItem)
                .filter(CommunicationItem.timestamp >= day_start)
                .filter(CommunicationItem.timestamp <= day_end)
                .count()
            )
        finally:
            session.close()

    def _toggle(self):
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._toggle_btn.setText(self._header_text())

        if self._expanded and not self._items_loaded:
            self._load_items()

    def _load_items(self):
        self._items_loaded = True
        session = get_session()
        try:
            day_start = datetime.combine(self._date, datetime.min.time())
            day_end = datetime.combine(self._date, datetime.max.time())
            items = (
                session.query(CommunicationItem)
                .filter(CommunicationItem.timestamp >= day_start)
                .filter(CommunicationItem.timestamp <= day_end)
                .order_by(CommunicationItem.timestamp.desc())
                .all()
            )

            for item in items:
                item_widget = self._make_item_widget(item)
                self._content_layout.addWidget(item_widget)

            if not items:
                empty = QLabel(f"<i style='color:{COLORS['text_muted']};'>No items</i>")
                self._content_layout.addWidget(empty)
        finally:
            session.close()

    def _make_item_widget(self, item: CommunicationItem) -> QWidget:
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 4px;
                padding: 6px;
                margin: 2px 0;
            }}
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # Source badge + title
        badge = source_badge_html(item.source)
        title_label = QLabel(f"{badge}  <b>{item.title}</b>")
        title_label.setWordWrap(True)
        title_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(title_label)

        # Sender + time
        time_str = item.timestamp.strftime("%I:%M %p")
        meta_label = QLabel(
            f"<span style='color:{COLORS['text_secondary']};font-size:11px;'>"
            f"{item.sender} - {time_str}</span>"
        )
        meta_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(meta_label)

        # Preview text
        preview = truncate_text(item.body_plain or "", 150)
        if preview:
            preview_label = QLabel(preview)
            preview_label.setWordWrap(True)
            preview_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            layout.addWidget(preview_label)

        return widget

    def refresh(self):
        """Reload the section."""
        self._items_loaded = False
        # Clear content
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._toggle_btn.setText(self._header_text())
        if self._expanded:
            self._load_items()
