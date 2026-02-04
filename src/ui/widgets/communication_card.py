"""Individual communication item card for the list view."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)

from src.utils.html_utils import truncate_text


class CommunicationCard(QFrame):
    """Clickable card representing a single communication item in the list."""

    clicked = Signal(int)  # Emits item ID

    def __init__(self, item_id: int, title: str, sender: str, timestamp_str: str,
                 source: str, preview: str = "", parent=None):
        super().__init__(parent)
        self._item_id = item_id
        self._selected = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameStyle(QFrame.Shape.Box)
        self._apply_style(selected=False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # Top row: source badge + title
        top = QHBoxLayout()
        source_color = "#4285f4" if source == "gmail" else "#ff9800"
        badge = QLabel(
            f"<span style='background-color:{source_color};color:white;"
            f"padding:1px 6px;border-radius:3px;font-size:10px;'>"
            f"{source.upper()}</span>"
        )
        badge.setTextFormat(Qt.TextFormat.RichText)
        badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        top.addWidget(badge)

        title_label = QLabel(f"<b>{title}</b>")
        title_label.setWordWrap(True)
        title_label.setTextFormat(Qt.TextFormat.RichText)
        top.addWidget(title_label, 1)
        layout.addLayout(top)

        # Sender + timestamp
        meta = QLabel(f"<span style='color:#666;font-size:11px;'>{sender} \u2022 {timestamp_str}</span>")
        meta.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(meta)

        # Preview
        if preview:
            prev = QLabel(truncate_text(preview, 120))
            prev.setWordWrap(True)
            prev.setStyleSheet("color: #555; font-size: 12px;")
            layout.addWidget(prev)

    def mousePressEvent(self, event):
        self.clicked.emit(self._item_id)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style(selected)

    def _apply_style(self, selected: bool):
        bg = "#e3f2fd" if selected else "#ffffff"
        border = "#1976d2" if selected else "#ddd"
        self.setStyleSheet(f"""
            CommunicationCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 4px;
                margin: 2px 4px;
            }}
        """)
