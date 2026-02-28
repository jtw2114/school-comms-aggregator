"""Calendar view tab showing key dates on an interactive monthly calendar."""

import calendar
import logging
from collections import defaultdict
from datetime import date, timedelta

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme import COLORS, RADIUS, TYPOGRAPHY, get_checkbox_label_style
from src.ui.widgets.find_bar import FindBar

logger = logging.getLogger(__name__)

# Calendar-specific colors
CAL_COLORS = {
    "today_bg": "rgba(0, 122, 255, 0.12)",
    "today_border": "#007AFF",
    "selected_bg": COLORS["surface_selected"],
    "selected_border": "#007AFF",
    "key_date_dot": "#007AFF",
    "action_item_dot": "#FF9500",
    "weekend_text": COLORS["text_tertiary"],
    "other_month_text": COLORS["text_disabled"],
}


# =============================================================================
# _MonthNavBar
# =============================================================================

class _MonthNavBar(QWidget):
    """Navigation bar: ◀ "Month YYYY" ▶ [Today]"""

    prev_clicked = Signal()
    next_clicked = Signal()
    today_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)

        self._btn_prev = QPushButton("\u25C0")
        self._btn_prev.setFixedSize(32, 32)
        self._btn_prev.setFlat(True)
        self._btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_prev.clicked.connect(self.prev_clicked)
        layout.addWidget(self._btn_prev)

        self._label = QLabel()
        self._label.setObjectName("page_title")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label, 1)

        self._btn_next = QPushButton("\u25B6")
        self._btn_next.setFixedSize(32, 32)
        self._btn_next.setFlat(True)
        self._btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_next.clicked.connect(self.next_clicked)
        layout.addWidget(self._btn_next)

        self._btn_today = QPushButton("Today")
        self._btn_today.setProperty("class", "secondary")
        self._btn_today.setFixedHeight(32)
        self._btn_today.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_today.clicked.connect(self.today_clicked)
        layout.addWidget(self._btn_today)

    def set_label(self, year: int, month: int):
        self._label.setText(f"{calendar.month_name[month]} {year}")


# =============================================================================
# _DayCell
# =============================================================================

class _DayCell(QFrame):
    """A single day cell in the calendar grid."""

    clicked = Signal(object)  # emits date or None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._date: date | None = None
        self._is_current_month = True

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(70)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        self._day_label = QLabel()
        self._day_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._day_label)

        self._dots_label = QLabel()
        self._dots_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self._dots_label.setWordWrap(True)
        layout.addWidget(self._dots_label, 1)

    def set_day(self, d: date | None, is_current_month: bool, is_today: bool,
                is_selected: bool, items: list):
        self._date = d
        self._is_current_month = is_current_month

        if d is None:
            self._day_label.setText("")
            self._dots_label.setText("")
            self.setStyleSheet("")
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Day number styling
        day_text = str(d.day)
        if not is_current_month:
            color = CAL_COLORS["other_month_text"]
        elif d.weekday() >= 5:  # Saturday/Sunday
            color = CAL_COLORS["weekend_text"]
        else:
            color = COLORS["text_primary"]
        self._day_label.setText(day_text)
        self._day_label.setStyleSheet(f"color: {color}; font-weight: {'600' if is_today else '400'}; background: transparent;")

        # Dots for events
        if items:
            key_dates = sum(1 for i in items if i.category == "key_dates")
            action_items = sum(1 for i in items if i.category == "action_items")
            dots = []
            # Show up to 3 dots
            shown = 0
            for _ in range(min(key_dates, 2)):
                dots.append(f'<span style="color:{CAL_COLORS["key_date_dot"]}; font-size:16px;">\u25CF</span>')
                shown += 1
            for _ in range(min(action_items, 2)):
                if shown >= 3:
                    break
                dots.append(f'<span style="color:{CAL_COLORS["action_item_dot"]}; font-size:16px;">\u25CF</span>')
                shown += 1
            total = len(items)
            if total > 3:
                dots.append(f'<span style="color:{COLORS["text_secondary"]}; font-size:10px;">+{total - 3}</span>')
            self._dots_label.setTextFormat(Qt.TextFormat.RichText)
            self._dots_label.setText(" ".join(dots))
        else:
            self._dots_label.setText("")

        # Cell background
        c = COLORS
        if is_today and is_selected:
            self.setStyleSheet(
                f"_DayCell {{ background-color: {CAL_COLORS['today_bg']}; "
                f"border: 2px solid {CAL_COLORS['today_border']}; "
                f"border-radius: {RADIUS['md']}px; }}"
            )
        elif is_today:
            self.setStyleSheet(
                f"_DayCell {{ background-color: {CAL_COLORS['today_bg']}; "
                f"border: 1px solid {CAL_COLORS['today_border']}; "
                f"border-radius: {RADIUS['md']}px; }}"
            )
        elif is_selected:
            self.setStyleSheet(
                f"_DayCell {{ background-color: {CAL_COLORS['selected_bg']}; "
                f"border: 2px solid {CAL_COLORS['selected_border']}; "
                f"border-radius: {RADIUS['md']}px; }}"
            )
        else:
            self.setStyleSheet(
                f"_DayCell {{ background-color: {c['surface']}; "
                f"border: 1px solid {c['separator']}; "
                f"border-radius: {RADIUS['md']}px; }}"
            )

    def mousePressEvent(self, event):
        if self._date and self._is_current_month:
            self.clicked.emit(self._date)
        super().mousePressEvent(event)


# =============================================================================
# _CalendarGrid
# =============================================================================

class _CalendarGrid(QWidget):
    """7-column grid for a month view with day headers."""

    day_clicked = Signal(object)  # emits date

    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(4)

        # Day-of-week headers
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for col, name in enumerate(day_names):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-weight: 600; "
                f"font-size: {TYPOGRAPHY['caption']}; background: transparent;"
            )
            self._grid.addWidget(lbl, 0, col)

        # Create 6x7 day cells
        self._cells: list[_DayCell] = []
        for row in range(6):
            for col in range(7):
                cell = _DayCell()
                cell.clicked.connect(self.day_clicked)
                self._grid.addWidget(cell, row + 1, col)
                self._cells.append(cell)

    def populate(self, year: int, month: int, items_by_date: dict, selected_date: date | None):
        today = date.today()
        cal = calendar.Calendar(firstweekday=6)  # Sunday first
        month_days = list(cal.itermonthdates(year, month))

        for i, cell in enumerate(self._cells):
            if i < len(month_days):
                d = month_days[i]
                is_current_month = d.month == month
                is_today = d == today
                is_selected = d == selected_date
                day_items = items_by_date.get(d, [])
                cell.set_day(d, is_current_month, is_today, is_selected, day_items)
                cell.setVisible(True)
            else:
                cell.set_day(None, False, False, False, [])
                cell.setVisible(False)


# =============================================================================
# _DayDetailPanel
# =============================================================================

class _DayDetailPanel(QFrame):
    """Shows details for a selected day with checkboxes."""

    item_toggled = Signal(int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SummaryCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVisible(False)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(8)

        self._header = QLabel()
        self._header.setObjectName("card_header")
        self._layout.addWidget(self._header)

        self._items_widget = QWidget()
        self._items_layout = QVBoxLayout(self._items_widget)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(6)
        self._layout.addWidget(self._items_widget)

    def show_day(self, d: date, items: list):
        # Clear existing items
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._header.setText(f"\U0001F4C5  {d.strftime('%A, %B %d, %Y')}")

        if not items:
            empty = QLabel("No events on this day")
            empty.setObjectName("caption")
            self._items_layout.addWidget(empty)
        else:
            for item in items:
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(8)

                # Category dot
                dot_color = CAL_COLORS["key_date_dot"] if item.category == "key_dates" else CAL_COLORS["action_item_dot"]
                dot = QLabel(f'<span style="color:{dot_color}; font-size:12px;">\u25CF</span>')
                dot.setTextFormat(Qt.TextFormat.RichText)
                dot.setFixedWidth(16)
                row.addWidget(dot)

                cb = QCheckBox(item.item_text)
                cb.setChecked(item.is_checked)
                cb.setStyleSheet(get_checkbox_label_style(item.is_checked))
                cb.toggled.connect(
                    lambda checked, iid=item.id, checkbox=cb: self._on_toggled(iid, checked, checkbox)
                )
                row.addWidget(cb, 1)

                row_widget = QWidget()
                row_widget.setLayout(row)
                self._items_layout.addWidget(row_widget)

        self.setVisible(True)

    def show_undated(self, items: list):
        """Show undated items for review."""
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._header.setText("Events Without Dates")

        if not items:
            empty = QLabel("All events have dates assigned")
            empty.setObjectName("caption")
            self._items_layout.addWidget(empty)
        else:
            for item in items:
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(8)

                dot_color = CAL_COLORS["key_date_dot"] if item.category == "key_dates" else CAL_COLORS["action_item_dot"]
                dot = QLabel(f'<span style="color:{dot_color}; font-size:12px;">\u25CF</span>')
                dot.setTextFormat(Qt.TextFormat.RichText)
                dot.setFixedWidth(16)
                row.addWidget(dot)

                cb = QCheckBox(item.item_text)
                cb.setChecked(item.is_checked)
                cb.setStyleSheet(get_checkbox_label_style(item.is_checked))
                cb.toggled.connect(
                    lambda checked, iid=item.id, checkbox=cb: self._on_toggled(iid, checked, checkbox)
                )
                row.addWidget(cb, 1)

                row_widget = QWidget()
                row_widget.setLayout(row)
                self._items_layout.addWidget(row_widget)

        self.setVisible(True)

    def _on_toggled(self, item_id: int, checked: bool, checkbox: QCheckBox):
        checkbox.setStyleSheet(get_checkbox_label_style(checked))
        self.item_toggled.emit(item_id, checked)


# =============================================================================
# _UpcomingList
# =============================================================================

class _UpcomingList(QFrame):
    """Compact list of events in the next 7 days."""

    item_toggled = Signal(int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SummaryCard")
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(6)

        self._items_widget = QWidget()
        self._items_layout = QVBoxLayout(self._items_widget)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(4)
        self._layout.addWidget(self._items_widget)

    def set_items(self, items: list):
        # Clear existing
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            empty = QLabel("No upcoming events in the next 7 days")
            empty.setObjectName("caption")
            self._items_layout.addWidget(empty)
            return

        # Group by date
        by_date: dict[date, list] = defaultdict(list)
        for item in items:
            if item.event_date:
                by_date[item.event_date].append(item)

        for d in sorted(by_date.keys()):
            # Date sub-header
            today = date.today()
            if d == today:
                date_text = f"Today \u2014 {d.strftime('%B %d')}"
            elif d == today + timedelta(days=1):
                date_text = f"Tomorrow \u2014 {d.strftime('%B %d')}"
            else:
                date_text = d.strftime("%A, %B %d")

            date_label = QLabel(date_text)
            date_label.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-weight: 600; "
                f"font-size: {TYPOGRAPHY['caption']}; padding-top: 4px; background: transparent;"
            )
            self._items_layout.addWidget(date_label)

            for item in by_date[d]:
                row = QHBoxLayout()
                row.setContentsMargins(8, 0, 0, 0)
                row.setSpacing(8)

                dot_color = CAL_COLORS["key_date_dot"] if item.category == "key_dates" else CAL_COLORS["action_item_dot"]
                dot = QLabel(f'<span style="color:{dot_color}; font-size:10px;">\u25CF</span>')
                dot.setTextFormat(Qt.TextFormat.RichText)
                dot.setFixedWidth(14)
                row.addWidget(dot)

                cb = QCheckBox(item.item_text)
                cb.setChecked(item.is_checked)
                cb.setStyleSheet(get_checkbox_label_style(item.is_checked))
                cb.toggled.connect(
                    lambda checked, iid=item.id, checkbox=cb: self._on_toggled(iid, checked, checkbox)
                )
                row.addWidget(cb, 1)

                row_widget = QWidget()
                row_widget.setLayout(row)
                self._items_layout.addWidget(row_widget)

    def _on_toggled(self, item_id: int, checked: bool, checkbox: QCheckBox):
        checkbox.setStyleSheet(get_checkbox_label_style(checked))
        self.item_toggled.emit(item_id, checked)


# =============================================================================
# _UndatedBanner
# =============================================================================

class _UndatedBanner(QFrame):
    """Banner showing count of key_dates items with no event_date assigned."""

    review_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SummaryCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVisible(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        self._label = QLabel()
        self._label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {TYPOGRAPHY['body']}; background: transparent;"
        )
        layout.addWidget(self._label, 1)

        self._btn_review = QPushButton("Review")
        self._btn_review.setProperty("class", "secondary")
        self._btn_review.setFixedHeight(28)
        self._btn_review.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_review.clicked.connect(self.review_clicked)
        layout.addWidget(self._btn_review)

    def set_count(self, count: int):
        if count > 0:
            noun = "event" if count == 1 else "events"
            self._label.setText(f"{count} {noun} with no date assigned")
            self.setVisible(True)
        else:
            self.setVisible(False)


# =============================================================================
# CalendarView (main widget)
# =============================================================================

class CalendarView(QWidget):
    """Calendar tab showing key dates on a monthly grid with upcoming events.

    Layout:
    ┌────────────────────────────┬─────────────────────────┐
    │  ◀  Month YYYY  ▶ [Today] │                         │
    ├────────────────────────────┤   DayDetailPanel        │
    │                            │   (selected day)        │
    │     CalendarGrid           ├─────────────────────────┤
    │     (month grid)           │  Upcoming (Next 7 Days) │
    │                            │   compact list          │
    ├────────────────────────────┴─────────────────────────┤
    │  N events with no date assigned           [Review]   │
    └──────────────────────────────────────────────────────┘
    """

    checklist_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_year = date.today().year
        self._current_month = date.today().month
        self._selected_date: date | None = None

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Find bar (Ctrl+F)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._find_bar = FindBar(self._scroll)
        outer.addWidget(self._find_bar)
        outer.addWidget(self._scroll)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setSpacing(16)
        self._scroll.setWidget(container)

        # Month navigation bar (full width)
        self._nav = _MonthNavBar()
        self._nav.prev_clicked.connect(self._go_prev_month)
        self._nav.next_clicked.connect(self._go_next_month)
        self._nav.today_clicked.connect(self._go_today)
        self._layout.addWidget(self._nav)

        # ---- Side-by-side: calendar grid (left) + detail/upcoming (right) ----
        content_row = QHBoxLayout()
        content_row.setSpacing(20)

        # Left: calendar grid
        self._grid = _CalendarGrid()
        self._grid.day_clicked.connect(self._on_day_clicked)
        content_row.addWidget(self._grid, 3)

        # Right: detail panel + upcoming list
        right_panel = QVBoxLayout()
        right_panel.setSpacing(16)

        self._detail = _DayDetailPanel()
        self._detail.item_toggled.connect(self._on_item_toggled)
        right_panel.addWidget(self._detail)

        upcoming_header = QLabel("Upcoming (Next 7 Days)")
        upcoming_header.setObjectName("section_header")
        right_panel.addWidget(upcoming_header)

        self._upcoming = _UpcomingList()
        self._upcoming.item_toggled.connect(self._on_item_toggled)
        right_panel.addWidget(self._upcoming)

        right_panel.addStretch()
        content_row.addLayout(right_panel, 2)

        self._layout.addLayout(content_row, 1)

        # ---- Bottom banner: undated items ----
        self._undated_banner = _UndatedBanner()
        self._undated_banner.review_clicked.connect(self._on_review_undated)
        self._layout.addWidget(self._undated_banner)

        # Initial load
        self.refresh()

    def refresh(self):
        """Reload calendar data from database."""
        try:
            from src.services.checklist_service import ChecklistService
            svc = ChecklistService()

            # Get items for current month
            month_items = svc.get_items_for_month(self._current_year, self._current_month)
            items_by_date: dict[date, list] = defaultdict(list)
            for item in month_items:
                if item.event_date:
                    items_by_date[item.event_date].append(item)

            # Update nav label
            self._nav.set_label(self._current_year, self._current_month)

            # Populate grid
            self._grid.populate(
                self._current_year, self._current_month,
                items_by_date, self._selected_date
            )

            # Update detail panel if a day is selected
            if self._selected_date:
                detail_items = items_by_date.get(self._selected_date, [])
                self._detail.show_day(self._selected_date, detail_items)
            else:
                self._detail.setVisible(False)

            # Update upcoming list (next 7 days)
            today = date.today()
            upcoming_items = svc.get_items_for_range(today, today + timedelta(days=6))
            self._upcoming.set_items(upcoming_items)

            # Update undated items banner
            undated = svc.get_undated_items("key_dates")
            self._undated_banner.set_count(len(undated))

        except Exception:
            logger.warning("Failed to load calendar data", exc_info=True)

    @Slot()
    def _go_prev_month(self):
        if self._current_month == 1:
            self._current_month = 12
            self._current_year -= 1
        else:
            self._current_month -= 1
        self._selected_date = None
        self.refresh()

    @Slot()
    def _go_next_month(self):
        if self._current_month == 12:
            self._current_month = 1
            self._current_year += 1
        else:
            self._current_month += 1
        self._selected_date = None
        self.refresh()

    @Slot()
    def _go_today(self):
        today = date.today()
        self._current_year = today.year
        self._current_month = today.month
        self._selected_date = today
        self.refresh()

    @Slot(object)
    def _on_day_clicked(self, d):
        if self._selected_date == d:
            self._selected_date = None  # Toggle off
        else:
            self._selected_date = d
        self.refresh()

    @Slot(int, bool)
    def _on_item_toggled(self, item_id: int, checked: bool):
        try:
            from src.services.checklist_service import ChecklistService
            svc = ChecklistService()
            svc.set_item_checked(item_id, checked)
            self.checklist_changed.emit()
        except Exception:
            logger.warning("Failed to persist checklist toggle", exc_info=True)

    @Slot()
    def _on_review_undated(self):
        """Show undated items in the detail panel for manual date assignment."""
        try:
            from src.services.checklist_service import ChecklistService
            svc = ChecklistService()
            undated = svc.get_undated_items("key_dates")
            if undated:
                self._selected_date = None
                self._detail.show_undated(undated)
                self._grid.populate(
                    self._current_year, self._current_month,
                    {}, None,
                )
                self.refresh()
        except Exception:
            logger.warning("Failed to load undated items", exc_info=True)
