"""Gmail OAuth2 setup wizard dialog."""

import traceback

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.services.gmail_service import GmailService
from src.config.settings import GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH


class _AuthWorker(QThread):
    success = Signal()
    error = Signal(str)

    def __init__(self, force_new: bool = False):
        super().__init__()
        self.force_new = force_new

    def run(self):
        try:
            svc = GmailService()
            svc.authenticate(force_new=self.force_new)
            self.success.emit()
        except Exception as e:
            self.error.emit(f"{e}\n{traceback.format_exc()}")


class GmailAuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gmail Setup")
        self.setMinimumWidth(420)
        self._worker = None

        layout = QVBoxLayout(self)

        # Status
        has_creds = GOOGLE_CREDENTIALS_PATH.exists()
        has_token = GOOGLE_TOKEN_PATH.exists()

        layout.addWidget(QLabel("<b>Gmail OAuth2 Setup</b>"))
        layout.addWidget(QLabel(
            f"credentials.json: {'Found' if has_creds else 'NOT FOUND'}"
        ))
        layout.addWidget(QLabel(
            f"Existing token: {'Found' if has_token else 'None'}"
        ))

        if not has_creds:
            layout.addWidget(QLabel(
                "Download credentials.json from the Google Cloud Console\n"
                "and place it in the credentials/ folder, or use Settings to browse to it."
            ))

        # Buttons
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self._auth_btn = QPushButton("Authorize Gmail Access")
        self._auth_btn.setEnabled(has_creds)
        self._auth_btn.clicked.connect(self._start_auth)
        layout.addWidget(self._auth_btn)

        self._reauth_btn = QPushButton("Re-authorize (new token)")
        self._reauth_btn.setEnabled(has_creds)
        self._reauth_btn.clicked.connect(self._start_reauth)
        layout.addWidget(self._reauth_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _start_auth(self):
        self._run(force_new=False)

    def _start_reauth(self):
        self._run(force_new=True)

    def _run(self, force_new: bool):
        self._auth_btn.setEnabled(False)
        self._reauth_btn.setEnabled(False)
        self._status_label.setText("Opening browser for authorization...")

        self._worker = _AuthWorker(force_new=force_new)
        self._worker.success.connect(self._on_success)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_success(self):
        self._status_label.setText("Gmail authorized successfully!")
        self._auth_btn.setEnabled(True)
        self._reauth_btn.setEnabled(True)
        QMessageBox.information(self, "Success", "Gmail access authorized.")

    def _on_error(self, msg: str):
        self._status_label.setText("Authorization failed.")
        self._auth_btn.setEnabled(True)
        self._reauth_btn.setEnabled(True)
        QMessageBox.warning(self, "Error", f"Gmail auth failed:\n{msg}")
