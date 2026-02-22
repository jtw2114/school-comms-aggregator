"""Find-in-page overlay bar (Ctrl+F) that highlights text matches in visible content."""

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QWidget,
)

from src.ui.theme import COLORS


class FindBar(QWidget):
    """A horizontal bar for browser-style find-in-page with match highlighting."""

    def __init__(self, scroll_area: QScrollArea, parent=None):
        super().__init__(parent)
        self._scroll_area = scroll_area
        self._matches: list[QLabel] = []
        self._match_spans: list[tuple[QLabel, str]] = []  # (label, original_text)
        self._current_index = -1
        self._original_texts: dict[int, str] = {}  # id(label) -> original rich/plain text
        self._query = ""

        self.setVisible(False)
        self.setObjectName("FindBar")
        c = COLORS
        self.setStyleSheet(
            f"QWidget#FindBar {{ background-color: {c['surface']}; "
            f"border-bottom: 1px solid {c['separator']}; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Find in page...")
        self._input.setClearButtonEnabled(True)
        self._input.setMaximumWidth(300)
        self._input.textChanged.connect(self._on_query_changed)
        self._input.returnPressed.connect(self.go_next)
        layout.addWidget(self._input)

        self._count_label = QLabel("")
        self._count_label.setObjectName("caption")
        self._count_label.setMinimumWidth(60)
        layout.addWidget(self._count_label)

        btn_prev = QPushButton("\u25B2")  # Up arrow
        btn_prev.setFlat(True)
        btn_prev.setFixedSize(28, 28)
        btn_prev.setToolTip("Previous match (Shift+Enter)")
        btn_prev.clicked.connect(self.go_prev)
        layout.addWidget(btn_prev)

        btn_next = QPushButton("\u25BC")  # Down arrow
        btn_next.setFlat(True)
        btn_next.setFixedSize(28, 28)
        btn_next.setToolTip("Next match (Enter)")
        btn_next.clicked.connect(self.go_next)
        layout.addWidget(btn_next)

        btn_close = QPushButton("\u2715")  # X
        btn_close.setFlat(True)
        btn_close.setFixedSize(28, 28)
        btn_close.setToolTip("Close (Escape)")
        btn_close.clicked.connect(self.close_bar)
        layout.addWidget(btn_close)

        layout.addStretch()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_bar()
        elif event.key() == Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.go_prev()
        else:
            super().keyPressEvent(event)

    def open_bar(self):
        """Show the find bar and focus the input."""
        self.setVisible(True)
        self._input.setFocus()
        self._input.selectAll()

    def close_bar(self):
        """Hide the find bar and clear highlights."""
        self._restore_all()
        self._input.clear()
        self._matches.clear()
        self._current_index = -1
        self._count_label.setText("")
        self.setVisible(False)

    def toggle(self):
        """Toggle visibility of the find bar."""
        if self.isVisible():
            self.close_bar()
        else:
            self.open_bar()

    def _on_query_changed(self, text: str):
        self._restore_all()
        self._query = text.strip()
        self._matches.clear()
        self._current_index = -1

        if not self._query:
            self._count_label.setText("")
            return

        self._find_matches()
        self._highlight_all()
        self._update_count()

        if self._matches:
            self._current_index = 0
            self._scroll_to_current()

    def _find_matches(self):
        """Find all QLabel widgets in the scroll area whose text contains the query."""
        if not self._scroll_area.widget():
            return
        labels = self._scroll_area.widget().findChildren(QLabel)
        query_lower = self._query.lower()
        for label in labels:
            if not label.isVisible():
                continue
            plain = label.text()
            # Skip labels that are already using rich text for badges etc.
            if plain and query_lower in plain.lower():
                self._matches.append(label)

    def _highlight_all(self):
        """Apply yellow highlight to all matched substrings."""
        for label in self._matches:
            original = label.text()
            self._original_texts[id(label)] = original
            # Escape HTML in the original text if it's plain text
            if not label.textFormat() == Qt.TextFormat.RichText:
                highlighted = self._insert_highlights(original, self._query)
                label.setTextFormat(Qt.TextFormat.RichText)
                label.setText(highlighted)

    def _insert_highlights(self, text: str, query: str) -> str:
        """Wrap matched substrings with a yellow background span."""
        escaped_query = re.escape(query)
        pattern = re.compile(f"({escaped_query})", re.IGNORECASE)

        def replacer(match):
            return f'<span style="background-color: #FFEB3B; color: #000;">{match.group(0)}</span>'

        return pattern.sub(replacer, text)

    def _restore_all(self):
        """Restore all labels to their original text."""
        for label in self._matches:
            lid = id(label)
            if lid in self._original_texts:
                label.setTextFormat(Qt.TextFormat.PlainText)
                label.setText(self._original_texts[lid])
        self._original_texts.clear()

    def _update_count(self):
        total = len(self._matches)
        if total == 0:
            self._count_label.setText("No matches")
        else:
            current = self._current_index + 1 if self._current_index >= 0 else 0
            self._count_label.setText(f"{current} of {total}")

    def _scroll_to_current(self):
        """Scroll the current match into view."""
        if 0 <= self._current_index < len(self._matches):
            label = self._matches[self._current_index]
            self._scroll_area.ensureWidgetVisible(label, 50, 50)
        self._update_count()

    def go_next(self):
        """Move to the next match."""
        if not self._matches:
            return
        self._current_index = (self._current_index + 1) % len(self._matches)
        self._scroll_to_current()

    def go_prev(self):
        """Move to the previous match."""
        if not self._matches:
            return
        self._current_index = (self._current_index - 1) % len(self._matches)
        self._scroll_to_current()
