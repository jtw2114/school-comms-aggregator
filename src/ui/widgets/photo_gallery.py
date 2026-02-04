"""Thumbnail gallery for Brightwheel photo attachments."""

import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class PhotoGallery(QWidget):
    """Horizontal scrollable gallery of photo thumbnails."""

    THUMB_SIZE = 120

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        self._title = QLabel("<b>Photos</b>")
        self._title.setVisible(False)
        layout.addWidget(self._title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFixedHeight(self.THUMB_SIZE + 20)
        layout.addWidget(scroll)

        self._container = QWidget()
        self._gallery_layout = QHBoxLayout(self._container)
        self._gallery_layout.setContentsMargins(0, 0, 0, 0)
        self._gallery_layout.setSpacing(8)
        self._gallery_layout.addStretch()
        scroll.setWidget(self._container)

        self.setVisible(False)

    def set_photos(self, photo_paths: list[str]):
        """Display photos from local file paths. Skips missing files."""
        # Clear existing
        while self._gallery_layout.count():
            child = self._gallery_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        loaded = 0
        for path in photo_paths:
            if not path or not os.path.exists(path):
                # Show placeholder for remote URLs
                thumb = QLabel(f"[Photo]")
                thumb.setFixedSize(QSize(self.THUMB_SIZE, self.THUMB_SIZE))
                thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb.setStyleSheet("""
                    background-color: #f0f0f0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    color: #999;
                """)
                self._gallery_layout.addWidget(thumb)
                loaded += 1
                continue

            pixmap = QPixmap(path)
            if pixmap.isNull():
                continue

            scaled = pixmap.scaled(
                QSize(self.THUMB_SIZE, self.THUMB_SIZE),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            thumb = QLabel()
            thumb.setPixmap(scaled)
            thumb.setFixedSize(QSize(self.THUMB_SIZE, self.THUMB_SIZE))
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb.setStyleSheet("border: 1px solid #ddd; border-radius: 4px;")
            self._gallery_layout.addWidget(thumb)
            loaded += 1

        self._gallery_layout.addStretch()
        self._title.setVisible(loaded > 0)
        self.setVisible(loaded > 0)

    def clear(self):
        self.set_photos([])
