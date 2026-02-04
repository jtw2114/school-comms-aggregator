"""WhatsApp setup dialog for QR code authentication via Playwright."""

import traceback

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.services.whatsapp_service import WhatsAppService


class _SetupWorker(QThread):
    success = Signal()
    error = Signal(str)

    def run(self):
        try:
            svc = WhatsAppService()
            svc.setup()
            self.success.emit()
        except Exception as e:
            self.error.emit(f"{e}\n{traceback.format_exc()}")


class WhatsAppSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WhatsApp Setup")
        self.setMinimumWidth(450)
        self._worker = None

        layout = QVBoxLayout(self)

        # QR code login group
        qr_group = QGroupBox("WhatsApp Web Login")
        qr_layout = QVBoxLayout()

        svc = WhatsAppService()
        has_session = svc.has_session()
        qr_layout.addWidget(QLabel(
            f"Session: {'Found' if has_session else 'NOT SET (scan QR code below)'}"
        ))
        qr_layout.addWidget(QLabel(
            "A browser will open to WhatsApp Web.\n"
            "Scan the QR code with your phone to log in.\n"
            "The browser will close automatically once connected."
        ))

        self._status_label = QLabel("")
        qr_layout.addWidget(self._status_label)

        self._setup_btn = QPushButton("Open WhatsApp Web")
        self._setup_btn.clicked.connect(self._start_setup)
        qr_layout.addWidget(self._setup_btn)

        qr_group.setLayout(qr_layout)
        layout.addWidget(qr_group)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _start_setup(self):
        self._setup_btn.setEnabled(False)
        self._status_label.setText("Opening browser... scan the QR code with your phone.")

        self._worker = _SetupWorker()
        self._worker.success.connect(self._on_success)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_success(self):
        self._setup_btn.setEnabled(True)
        self._status_label.setText("Session saved successfully!")
        QMessageBox.information(self, "Success", "WhatsApp session authenticated and saved.")

    def _on_error(self, msg: str):
        self._setup_btn.setEnabled(True)
        self._status_label.setText("Setup failed.")
        QMessageBox.warning(self, "Error", f"WhatsApp setup failed:\n{msg}")
