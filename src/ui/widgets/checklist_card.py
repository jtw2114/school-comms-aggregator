"""Checklist card widget with persistent checkboxes for action items / key dates."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme import COLORS


class ChecklistCard(QFrame):
    """A card with checkbox items that emit toggled signals."""

    item_toggled = Signal(int, bool)  # (item_id, checked)

    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._title_text = title
        self._icon = icon

        self.setObjectName("ChecklistCard")
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
        self._items_layout.setSpacing(4)
        self._content_layout.addWidget(self._items_widget)

        # Empty state
        self._empty_label = QLabel(f"<i style='color:{COLORS['text_muted']};'>No items</i>")
        self._items_layout.addWidget(self._empty_label)

    def set_checklist_items(self, items: list[tuple[int, str, bool]]):
        """Set checklist items. Each item is (id, text, is_checked)."""
        # Clear existing
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            self._empty_label = QLabel(f"<i style='color:{COLORS['text_muted']};'>No items</i>")
            self._items_layout.addWidget(self._empty_label)
            return

        for item_id, text, is_checked in items:
            cb = QCheckBox(text)
            cb.setChecked(is_checked)
            if is_checked:
                cb.setStyleSheet(
                    f"color: {COLORS['text_muted']}; text-decoration: line-through;"
                )
            else:
                cb.setStyleSheet(f"color: {COLORS['text_primary']};")

            # Capture item_id in closure
            cb.toggled.connect(lambda checked, iid=item_id, checkbox=cb: self._on_toggled(iid, checked, checkbox))
            self._items_layout.addWidget(cb)

    def _on_toggled(self, item_id: int, checked: bool, checkbox: QCheckBox):
        """Handle checkbox toggle — update style and emit signal."""
        if checked:
            checkbox.setStyleSheet(
                f"color: {COLORS['text_muted']}; text-decoration: line-through;"
            )
        else:
            checkbox.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.item_toggled.emit(item_id, checked)
