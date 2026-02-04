"""Main application window with tabbed interface."""

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.ui.dashboard_view import DashboardView
from src.ui.communications_view import CommunicationsView
from src.ui.settings_dialog import SettingsDialog
from src.ui.gmail_auth_dialog import GmailAuthDialog
from src.ui.brightwheel_auth_dialog import BrightwheelAuthDialog
from src.workers.sync_worker import SyncWorker
from src.workers.summary_worker import SummaryWorker
from src.ui.widgets.status_bar import SyncStatusBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("School Comms Aggregator")
        self.resize(1100, 750)

        self._sync_worker = None
        self._summary_worker = None

        self._build_menu_bar()
        self._build_toolbar()
        self._build_central()
        self._build_status_bar()

    # ---- Menu bar ----
    def _build_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("&Settings...", self._open_settings)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)

        accounts_menu = menu_bar.addMenu("&Accounts")
        accounts_menu.addAction("Setup &Gmail...", self._setup_gmail)
        accounts_menu.addAction("Setup &Brightwheel...", self._setup_brightwheel)

        sync_menu = menu_bar.addMenu("S&ync")
        sync_menu.addAction("Sync &All", self._sync_all)
        sync_menu.addAction("Sync &Gmail Only", lambda: self._sync_source("gmail"))
        sync_menu.addAction("Sync &Brightwheel Only", lambda: self._sync_source("brightwheel"))

    # ---- Toolbar ----
    def _build_toolbar(self):
        toolbar = QToolBar("Sync")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._btn_sync_all = QPushButton("Sync All")
        self._btn_sync_all.clicked.connect(self._sync_all)
        toolbar.addWidget(self._btn_sync_all)

        self._btn_sync_gmail = QPushButton("Sync Gmail")
        self._btn_sync_gmail.clicked.connect(lambda: self._sync_source("gmail"))
        toolbar.addWidget(self._btn_sync_gmail)

        self._btn_sync_bw = QPushButton("Sync BW")
        self._btn_sync_bw.clicked.connect(lambda: self._sync_source("brightwheel"))
        toolbar.addWidget(self._btn_sync_bw)

        spacer = QWidget()
        spacer.setFixedWidth(20)
        toolbar.addWidget(spacer)

        self._last_sync_label = QLabel("Last synced: never")
        toolbar.addWidget(self._last_sync_label)

    # ---- Central tabs ----
    def _build_central(self):
        self._tabs = QTabWidget()

        self._dashboard = DashboardView()
        self._tabs.addTab(self._dashboard, "Dashboard")

        self._comms_view = CommunicationsView()
        self._tabs.addTab(self._comms_view, "All Communications")

        self.setCentralWidget(self._tabs)

    # ---- Status bar ----
    def _build_status_bar(self):
        self._sync_status_bar = SyncStatusBar()
        self.setStatusBar(self._sync_status_bar)

    # ---- Slots ----
    @Slot()
    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    @Slot()
    def _setup_gmail(self):
        dlg = GmailAuthDialog(self)
        dlg.exec()

    @Slot()
    def _setup_brightwheel(self):
        dlg = BrightwheelAuthDialog(self)
        dlg.exec()

    @Slot()
    def _sync_all(self):
        self._run_sync(sources=["gmail", "brightwheel"])

    @Slot()
    def _sync_source(self, source: str):
        self._run_sync(sources=[source])

    def _run_sync(self, sources: list[str]):
        if self._sync_worker and self._sync_worker.isRunning():
            return  # already syncing

        self._set_sync_buttons_enabled(False)
        self._sync_status_bar.set_syncing(True)

        self._sync_worker = SyncWorker(sources)
        self._sync_worker.finished_signal.connect(self._on_sync_finished)
        self._sync_worker.progress_signal.connect(self._sync_status_bar.set_message)
        self._sync_worker.error_signal.connect(self._on_sync_error)
        self._sync_worker.start()

    @Slot()
    def _on_sync_finished(self):
        self._set_sync_buttons_enabled(True)
        self._sync_status_bar.set_syncing(False)
        self._sync_status_bar.set_message("Sync complete")

        from datetime import datetime
        self._last_sync_label.setText(f"Last synced: {datetime.now().strftime('%I:%M %p')}")

        # Refresh UI
        self._comms_view.refresh()

        # Kick off summary generation
        self._run_summary()

    @Slot(str)
    def _on_sync_error(self, error_msg: str):
        self._set_sync_buttons_enabled(True)
        self._sync_status_bar.set_syncing(False)
        self._sync_status_bar.set_message(f"Sync error: {error_msg}")

    def _run_summary(self):
        if self._summary_worker and self._summary_worker.isRunning():
            return

        self._summary_worker = SummaryWorker()
        self._summary_worker.finished_signal.connect(self._on_summary_finished)
        self._summary_worker.error_signal.connect(self._on_summary_error)
        self._summary_worker.start()

    @Slot()
    def _on_summary_finished(self):
        self._dashboard.refresh()
        self._sync_status_bar.set_message("Dashboard updated")

    @Slot(str)
    def _on_summary_error(self, error_msg: str):
        self._sync_status_bar.set_message(f"Summary error: {error_msg}")

    def _set_sync_buttons_enabled(self, enabled: bool):
        self._btn_sync_all.setEnabled(enabled)
        self._btn_sync_gmail.setEnabled(enabled)
        self._btn_sync_bw.setEnabled(enabled)
