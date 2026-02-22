"""Checklist card widget with persistent checkboxes for action items / key dates."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme import get_checkbox_label_style


class ChecklistCard(QFrame):
    """A card with checkbox items that emit toggled signals."""

    item_toggled = Signal(int, bool)  # (item_id, checked)

    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._title_text = title
        self._icon = icon

        self.setObjectName("ChecklistCard")
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
        self._items_layout.setSpacing(6)
        layout.addWidget(self._items_widget)

        self._checkboxes: list[QCheckBox] = []

        # Empty state
        self._empty_label = QLabel("No items")
        self._empty_label.setObjectName("caption")
        self._items_layout.addWidget(self._empty_label)

    def set_checklist_items(self, items: list[tuple[int, str, bool]]):
        """Set checklist items. Each item is (id, text, is_checked)."""
        # Clear existing
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._checkboxes: list[QCheckBox] = []

        if not items:
            self._empty_label = QLabel("No items")
            self._empty_label.setObjectName("caption")
            self._items_layout.addWidget(self._empty_label)
            return

        for item_id, text, is_checked in items:
            cb = QCheckBox(text)
            cb.setChecked(is_checked)
            cb.setStyleSheet(get_checkbox_label_style(is_checked))

            # Capture item_id in closure
            cb.toggled.connect(lambda checked, iid=item_id, checkbox=cb: self._on_toggled(iid, checked, checkbox))
            self._checkboxes.append(cb)
            self._items_layout.addWidget(cb)

    def filter_text(self, query: str) -> int:
        """Show/hide checkbox items matching query. Returns count of visible items."""
        if not query:
            for cb in self._checkboxes:
                cb.setVisible(True)
            return len(self._checkboxes)

        query_lower = query.lower()
        visible = 0
        for cb in self._checkboxes:
            matches = query_lower in cb.text().lower()
            cb.setVisible(matches)
            if matches:
                visible += 1
        return visible

    def _on_toggled(self, item_id: int, checked: bool, checkbox: QCheckBox):
        """Handle checkbox toggle — update style and emit signal."""
        checkbox.setStyleSheet(get_checkbox_label_style(checked))
        self.item_toggled.emit(item_id, checked)
