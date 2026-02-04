"""Custom status bar with sync status indicator and item counts."""

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QLabel, QProgressBar, QStatusBar

from src.models.base import get_session
from src.models.communication import CommunicationItem


class SyncStatusBar(QStatusBar):
    """Status bar showing sync progress, messages, and item counts."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Progress indicator
        self._progress = QProgressBar()
        self._progress.setFixedWidth(120)
        self._progress.setMaximumHeight(16)
        self._progress.setRange(0, 0)  # Indeterminate
        self._progress.setVisible(False)
        self.addPermanentWidget(self._progress)

        # Item count
        self._count_label = QLabel()
        self.addPermanentWidget(self._count_label)

        self.update_counts()

    @Slot(bool)
    def set_syncing(self, syncing: bool):
        self._progress.setVisible(syncing)
        if not syncing:
            self.update_counts()

    @Slot(str)
    def set_message(self, message: str):
        self.showMessage(message, 5000)

    def update_counts(self):
        session = get_session()
        try:
            gmail_count = session.query(CommunicationItem).filter_by(source="gmail").count()
            bw_count = session.query(CommunicationItem).filter_by(source="brightwheel").count()
            total = gmail_count + bw_count
            self._count_label.setText(
                f"Items: {total} (Gmail: {gmail_count}, BW: {bw_count})"
            )
        finally:
            session.close()
