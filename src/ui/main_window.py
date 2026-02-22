"""Main application window with tabbed interface."""

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.ui.landing_page import LandingPage
from src.ui.dashboard_view import DashboardView
from src.ui.communications_view import CommunicationsView
from src.ui.archive_view import ArchiveView
from src.ui.settings_dialog import SettingsDialog
from src.ui.gmail_auth_dialog import GmailAuthDialog
from src.ui.brightwheel_auth_dialog import BrightwheelAuthDialog
from src.ui.whatsapp_setup_dialog import WhatsAppSetupDialog
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
        self._build_shortcuts()

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
        accounts_menu.addAction("Setup &WhatsApp...", self._setup_whatsapp)

        sync_menu = menu_bar.addMenu("S&ync")
        sync_menu.addAction("Sync &All", self._sync_all)
        sync_menu.addAction("Sync &Gmail Only", lambda: self._sync_source("gmail"))
        sync_menu.addAction("Sync &Brightwheel Only", lambda: self._sync_source("brightwheel"))
        sync_menu.addAction("Sync &WhatsApp Only", lambda: self._sync_source("whatsapp"))

    # ---- Toolbar ----
    def _build_toolbar(self):
        toolbar = QToolBar("Sync")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._btn_home = QPushButton("🏠 Home")
        self._btn_home.setObjectName("toolbar_btn")
        self._btn_home.clicked.connect(self._go_home)
        toolbar.addWidget(self._btn_home)

        spacer1 = QWidget()
        spacer1.setFixedWidth(20)
        toolbar.addWidget(spacer1)

        self._btn_sync_all = QPushButton("Sync All")
        self._btn_sync_all.setObjectName("toolbar_btn")
        self._btn_sync_all.clicked.connect(self._sync_all)
        toolbar.addWidget(self._btn_sync_all)

        self._btn_sync_gmail = QPushButton("Sync Gmail")
        self._btn_sync_gmail.setObjectName("toolbar_btn")
        self._btn_sync_gmail.clicked.connect(lambda: self._sync_source("gmail"))
        toolbar.addWidget(self._btn_sync_gmail)

        self._btn_sync_bw = QPushButton("Sync BW")
        self._btn_sync_bw.setObjectName("toolbar_btn")
        self._btn_sync_bw.clicked.connect(lambda: self._sync_source("brightwheel"))
        toolbar.addWidget(self._btn_sync_bw)

        self._btn_sync_wa = QPushButton("Sync WhatsApp")
        self._btn_sync_wa.setObjectName("toolbar_btn")
        self._btn_sync_wa.clicked.connect(lambda: self._sync_source("whatsapp"))
        toolbar.addWidget(self._btn_sync_wa)

        spacer = QWidget()
        spacer.setFixedWidth(20)
        toolbar.addWidget(spacer)

        self._last_sync_label = QLabel("Last synced: never")
        toolbar.addWidget(self._last_sync_label)

    # ---- Central widget with landing page and tabs ----
    def _build_central(self):
        self._stack = QStackedWidget()

        # Page 0: Landing page
        self._landing = LandingPage()
        self._landing.navigate_to_tab.connect(self._on_navigate_to_tab)
        self._stack.addWidget(self._landing)

        # Page 1: Tab widget with Dashboard, Communications, Archive
        self._tabs = QTabWidget()

        self._dashboard = DashboardView()
        self._dashboard.regenerate_requested.connect(lambda: self._run_summary(force=True))
        self._dashboard.checklist_changed.connect(self._on_checklist_changed)
        self._tabs.addTab(self._dashboard, "Dashboard")

        self._comms_view = CommunicationsView()
        self._tabs.addTab(self._comms_view, "All Communications")

        self._archive = ArchiveView()
        self._archive.checklist_changed.connect(self._on_checklist_changed)
        self._tabs.addTab(self._archive, "Archive")

        self._stack.addWidget(self._tabs)

        self.setCentralWidget(self._stack)

    @Slot(int)
    def _on_navigate_to_tab(self, tab_index: int):
        """Navigate from landing page to a specific tab."""
        self._stack.setCurrentIndex(1)  # Switch to tabs page
        self._tabs.setCurrentIndex(tab_index)

    @Slot()
    def _go_home(self):
        """Return to the landing page."""
        self._stack.setCurrentIndex(0)

    @Slot()
    def _on_checklist_changed(self):
        """Refresh both Dashboard and Archive when a checklist item changes."""
        self._dashboard.refresh()
        self._archive.refresh()

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
    def _setup_whatsapp(self):
        dlg = WhatsAppSetupDialog(self)
        dlg.exec()

    @Slot()
    def _sync_all(self):
        self._run_sync(sources=["gmail", "brightwheel", "whatsapp"])

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

    def _run_summary(self, force: bool = False):
        if self._summary_worker and self._summary_worker.isRunning():
            return

        self._summary_worker = SummaryWorker(force=force)
        self._summary_worker.finished_signal.connect(self._on_summary_finished)
        self._summary_worker.error_signal.connect(self._on_summary_error)
        self._summary_worker.start()

    @Slot()
    def _on_summary_finished(self):
        self._dashboard.refresh()
        self._dashboard.set_regenerate_enabled(True)
        self._sync_status_bar.set_message("Dashboard updated")

    @Slot(str)
    def _on_summary_error(self, error_msg: str):
        self._dashboard.set_regenerate_enabled(True)
        self._dashboard.set_error(f"Summary generation failed: {error_msg}")
        self._sync_status_bar.set_message(f"Summary error: {error_msg}")

    # ---- Keyboard shortcuts ----
    def _build_shortcuts(self):
        find_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        find_shortcut.activated.connect(self._on_find)

    @Slot()
    def _on_find(self):
        """Toggle find bar on the currently active tab."""
        if self._stack.currentIndex() != 1:
            return  # Only works on tab pages, not landing page
        current = self._tabs.currentWidget()
        if hasattr(current, "_find_bar"):
            current._find_bar.toggle()

    def _set_sync_buttons_enabled(self, enabled: bool):
        self._btn_sync_all.setEnabled(enabled)
        self._btn_sync_gmail.setEnabled(enabled)
        self._btn_sync_bw.setEnabled(enabled)
        self._btn_sync_wa.setEnabled(enabled)
