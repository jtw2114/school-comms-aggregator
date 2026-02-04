"""Background thread for generating AI summaries via Claude API."""

import traceback

from PySide6.QtCore import QThread, Signal

from src.services.summary_service import SummaryService


class SummaryWorker(QThread):
    """Runs summary generation in a background thread."""

    finished_signal = Signal()
    error_signal = Signal(str)
    progress_signal = Signal(str)

    def __init__(self, force: bool = False, parent=None):
        super().__init__(parent)
        self._force = force

    def run(self):
        try:
            self.progress_signal.emit("Generating AI summaries...")
            svc = SummaryService()
            svc.generate_rolling_summaries(force=self._force)
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(f"{e}")
