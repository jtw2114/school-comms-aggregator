"""Individual communication item card for the list view."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)

from src.ui.theme import get_card_style, source_badge_html
from src.utils.html_utils import truncate_text


class CommunicationCard(QFrame):
    """Clickable card representing a single communication item in the list."""

    clicked = Signal(int)  # Emits item ID

    def __init__(self, item_id: int, title: str, sender: str, timestamp_str: str,
                 source: str, preview: str = "", parent=None):
        super().__init__(parent)
        self._item_id = item_id
        self._selected = False

        self.setObjectName("CommunicationCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(get_card_style(selected=False))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Top row: source badge + title
        top = QHBoxLayout()
        top.setSpacing(8)
        badge = QLabel(source_badge_html(source))
        badge.setTextFormat(Qt.TextFormat.RichText)
        badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        top.addWidget(badge)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setObjectName("card_header")
        top.addWidget(title_label, 1)
        layout.addLayout(top)

        # Sender + timestamp
        meta = QLabel(f"{sender} • {timestamp_str}")
        meta.setObjectName("caption")
        layout.addWidget(meta)

        # Preview
        if preview:
            prev = QLabel(truncate_text(preview, 120))
            prev.setWordWrap(True)
            prev.setObjectName("caption")
            layout.addWidget(prev)

    def mousePressEvent(self, event):
        self.clicked.emit(self._item_id)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setStyleSheet(get_card_style(selected))
