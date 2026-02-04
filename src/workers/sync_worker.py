"""Background thread for syncing communications from Gmail and Brightwheel."""

import traceback

from PySide6.QtCore import QThread, Signal

from src.services.sync_service import SyncService


class SyncWorker(QThread):
    """Runs sync operations in a background thread."""

    finished_signal = Signal()
    error_signal = Signal(str)
    progress_signal = Signal(str)

    def __init__(self, sources: list[str], parent=None):
        super().__init__(parent)
        self._sources = sources

    def run(self):
        try:
            svc = SyncService(progress_callback=self._on_progress)

            for source in self._sources:
                if source == "gmail":
                    svc.sync_gmail()
                elif source == "brightwheel":
                    svc.sync_brightwheel()
                elif source == "whatsapp":
                    svc.sync_whatsapp()

            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))

    def _on_progress(self, msg: str):
        self.progress_signal.emit(msg)
