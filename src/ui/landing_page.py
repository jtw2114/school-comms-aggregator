"""Landing page with navigation buttons to main app sections."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme import get_landing_button_style


class LandingPage(QWidget):
    """Landing page with 3 large navigation buttons."""

    navigate_to_tab = Signal(int)  # Emits tab index (0=Dashboard, 1=Comms, 2=Archive)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setSpacing(40)

        # Title section
        title_container = QVBoxLayout()
        title_container.setSpacing(8)

        title = QLabel("School Comms Aggregator")
        title.setObjectName("landing_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_container.addWidget(title)

        subtitle = QLabel("Stay organized with school communications")
        subtitle.setObjectName("landing_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_container.addWidget(subtitle)

        layout.addLayout(title_container)
        layout.addStretch(1)

        # Navigation buttons
        btn_container = QHBoxLayout()
        btn_container.setSpacing(24)
        btn_container.setContentsMargins(20, 0, 20, 0)

        # Dashboard button
        self._btn_dashboard = self._create_nav_button(
            icon="\U0001F4CA",  # 📊
            title="Dashboard",
            description="View summaries,\nkey dates & action items",
            tab_index=0,
        )
        btn_container.addWidget(self._btn_dashboard)

        # Communications button
        self._btn_comms = self._create_nav_button(
            icon="\U0001F4E7",  # 📧
            title="Communications",
            description="Browse all messages\nfrom Gmail & Brightwheel",
            tab_index=1,
        )
        btn_container.addWidget(self._btn_comms)

        # Archive button
        self._btn_archive = self._create_nav_button(
            icon="\U0001F4E6",  # 📦
            title="Archive",
            description="View completed\naction items & dates",
            tab_index=2,
        )
        btn_container.addWidget(self._btn_archive)

        layout.addLayout(btn_container)
        layout.addStretch(2)

    def _create_nav_button(
        self, icon: str, title: str, description: str, tab_index: int
    ) -> QPushButton:
        """Create a styled navigation button."""
        btn = QPushButton(f"{icon}\n\n{title}\n\n{description}")
        btn.setFixedSize(200, 180)
        btn.setStyleSheet(get_landing_button_style())
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.navigate_to_tab.emit(tab_index))
        return btn
