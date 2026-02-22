"""Entry point for the School Communications Aggregator."""

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.config.settings import ensure_dirs
from src.models.base import init_db
from src.ui.main_window import MainWindow
from src.ui.theme import get_app_stylesheet


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stdout,
    )

    ensure_dirs()
    init_db()

    # Enable high-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("School Comms Aggregator")
    app.setOrganizationName("SchoolComms")
    app.setStyleSheet(get_app_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
