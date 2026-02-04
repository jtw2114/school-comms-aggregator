"""Brightwheel authentication dialog with Playwright login and manual cookie fallback."""

import traceback

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.services.brightwheel_auth import BrightwheelAuth
from src.services.credential_manager import get_bw_email, get_bw_password


class _LoginWorker(QThread):
    success = Signal()
    error = Signal(str)

    def __init__(self, email: str, password: str):
        super().__init__()
        self.email = email
        self.password = password

    def run(self):
        try:
            auth = BrightwheelAuth()
            auth.login(self.email, self.password, headless=False)
            self.success.emit()
        except Exception as e:
            self.error.emit(f"{e}\n{traceback.format_exc()}")


class BrightwheelAuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Brightwheel Setup")
        self.setMinimumWidth(450)
        self._worker = None

        layout = QVBoxLayout(self)

        # Automated login
        auto_group = QGroupBox("Automated Login (Playwright)")
        auto_layout = QVBoxLayout()

        email = get_bw_email()
        has_creds = bool(email and get_bw_password())
        auto_layout.addWidget(QLabel(
            f"Stored credentials: {'Found ({email})' if has_creds else 'NOT SET (use Settings)'}"
        ))
        auto_layout.addWidget(QLabel(
            "This opens a browser window. If Brightwheel requires 2FA,\n"
            "complete it in the browser. The window will close automatically."
        ))

        self._status_label = QLabel("")
        auto_layout.addWidget(self._status_label)

        self._login_btn = QPushButton("Login with Playwright")
        self._login_btn.setEnabled(has_creds)
        self._login_btn.clicked.connect(self._start_login)
        auto_layout.addWidget(self._login_btn)

        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)

        # Manual cookie fallback
        manual_group = QGroupBox("Manual Cookie Fallback")
        manual_layout = QVBoxLayout()
        manual_layout.addWidget(QLabel(
            "If automated login fails, paste the _brightwheel_v2 cookie value\n"
            "from your browser's developer tools."
        ))

        cookie_row = QHBoxLayout()
        self._cookie_input = QLineEdit()
        self._cookie_input.setPlaceholderText("Paste _brightwheel_v2 cookie value here")
        cookie_row.addWidget(self._cookie_input, 1)

        save_cookie_btn = QPushButton("Save Cookie")
        save_cookie_btn.clicked.connect(self._save_manual_cookie)
        cookie_row.addWidget(save_cookie_btn)

        manual_layout.addLayout(cookie_row)
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _start_login(self):
        email = get_bw_email()
        password = get_bw_password()
        if not email or not password:
            QMessageBox.warning(self, "Missing Credentials",
                                "Set Brightwheel email and password in Settings first.")
            return

        self._login_btn.setEnabled(False)
        self._status_label.setText("Opening browser...")

        self._worker = _LoginWorker(email, password)
        self._worker.success.connect(self._on_success)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_success(self):
        self._login_btn.setEnabled(True)
        self._status_label.setText("Login successful! Session saved.")
        QMessageBox.information(self, "Success", "Brightwheel session authenticated and saved.")

    def _on_error(self, msg: str):
        self._login_btn.setEnabled(True)
        self._status_label.setText("Login failed.")
        QMessageBox.warning(self, "Error", f"Brightwheel login failed:\n{msg}")

    def _save_manual_cookie(self):
        cookie = self._cookie_input.text().strip()
        if not cookie:
            return

        auth = BrightwheelAuth()
        auth.set_manual_cookie(cookie)

        import json
        from src.config.settings import BW_SESSION_PATH
        # Save a minimal session file
        session = {"cookies": [{"name": "_brightwheel_v2", "value": cookie, "domain": ".mybrightwheel.com", "path": "/"}]}
        BW_SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(BW_SESSION_PATH, "w") as f:
            json.dump(session, f)

        self._status_label.setText("Manual cookie saved.")
        QMessageBox.information(self, "Saved", "Cookie saved. Try syncing Brightwheel now.")
