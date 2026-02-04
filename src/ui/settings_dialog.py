"""Settings dialog for configuring credentials and preferences."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.services.credential_manager import (
    get_bw_email,
    get_bw_password,
    get_claude_api_key,
    get_wa_groups,
    set_bw_email,
    set_bw_password,
    set_claude_api_key,
    set_wa_groups,
)
from src.config.settings import GOOGLE_CREDENTIALS_PATH


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Brightwheel credentials
        bw_group = QGroupBox("Brightwheel Credentials")
        bw_layout = QFormLayout()

        self._bw_email = QLineEdit()
        self._bw_email.setPlaceholderText("your@email.com")
        bw_layout.addRow("Email:", self._bw_email)

        self._bw_password = QLineEdit()
        self._bw_password.setEchoMode(QLineEdit.EchoMode.Password)
        self._bw_password.setPlaceholderText("Enter password")
        bw_layout.addRow("Password:", self._bw_password)

        bw_group.setLayout(bw_layout)
        layout.addWidget(bw_group)

        # Claude API key
        claude_group = QGroupBox("Claude API Key")
        claude_layout = QFormLayout()

        self._claude_key = QLineEdit()
        self._claude_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._claude_key.setPlaceholderText("sk-ant-...")
        claude_layout.addRow("API Key:", self._claude_key)

        claude_group.setLayout(claude_layout)
        layout.addWidget(claude_group)

        # WhatsApp groups
        wa_group = QGroupBox("WhatsApp Groups")
        wa_layout = QFormLayout()

        self._wa_groups = QLineEdit()
        self._wa_groups.setPlaceholderText("BISC Parents, Hedgehogs Parents, ...")
        wa_layout.addRow("Group Names:", self._wa_groups)

        wa_group.setLayout(wa_layout)
        layout.addWidget(wa_group)

        # Google credentials file
        google_group = QGroupBox("Google OAuth Credentials")
        google_layout = QHBoxLayout()

        self._google_path_label = QLabel(str(GOOGLE_CREDENTIALS_PATH))
        self._google_path_label.setWordWrap(True)
        google_layout.addWidget(self._google_path_label, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_google_creds)
        google_layout.addWidget(browse_btn)

        google_group.setLayout(google_layout)
        layout.addWidget(google_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_current()

    def _load_current(self):
        email = get_bw_email()
        if email:
            self._bw_email.setText(email)

        password = get_bw_password()
        if password:
            self._bw_password.setPlaceholderText("(saved)")

        api_key = get_claude_api_key()
        if api_key:
            self._claude_key.setPlaceholderText("(saved)")

        wa_groups = get_wa_groups()
        if wa_groups:
            self._wa_groups.setText(", ".join(wa_groups))

    def _browse_google_creds(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Google credentials.json", "", "JSON Files (*.json)"
        )
        if path:
            import shutil
            shutil.copy2(path, GOOGLE_CREDENTIALS_PATH)
            self._google_path_label.setText(str(GOOGLE_CREDENTIALS_PATH))
            QMessageBox.information(self, "Copied", "credentials.json copied to project credentials folder.")

    def _save(self):
        email = self._bw_email.text().strip()
        if email:
            set_bw_email(email)

        password = self._bw_password.text()
        if password:
            set_bw_password(password)

        api_key = self._claude_key.text().strip()
        if api_key:
            set_claude_api_key(api_key)

        wa_text = self._wa_groups.text().strip()
        if wa_text:
            groups = [g.strip() for g in wa_text.split(",") if g.strip()]
            set_wa_groups(groups)
        else:
            set_wa_groups([])

        self.accept()
