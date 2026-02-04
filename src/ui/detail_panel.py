"""Detail panel showing full content of a selected communication item."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from src.models.base import get_session
from src.models.communication import Attachment, CommunicationItem
from src.ui.widgets.photo_gallery import PhotoGallery


class DetailPanel(QWidget):
    """Right-side panel showing full details of a selected communication."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header area
        self._title_label = QLabel()
        self._title_label.setWordWrap(True)
        self._title_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._title_label)

        self._meta_label = QLabel()
        self._meta_label.setWordWrap(True)
        self._meta_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._meta_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Body content (HTML via QWebEngineView)
        self._web_view = QWebEngineView()
        self._web_view.setMinimumHeight(200)
        layout.addWidget(self._web_view, 1)

        # Photo gallery
        self._photo_gallery = PhotoGallery()
        layout.addWidget(self._photo_gallery)

        # Attachments list
        self._attachments_label = QLabel()
        self._attachments_label.setWordWrap(True)
        self._attachments_label.setVisible(False)
        layout.addWidget(self._attachments_label)

        self._show_empty()

    def show_item(self, item_id: int):
        """Load and display a communication item by ID."""
        session = get_session()
        try:
            item = session.query(CommunicationItem).get(item_id)
            if not item:
                self._show_empty()
                return

            # Title with source badge
            source_color = "#4285f4" if item.source == "gmail" else "#ff9800"
            self._title_label.setText(
                f"<span style='background-color:{source_color};color:white;"
                f"padding:2px 8px;border-radius:3px;font-size:11px;'>"
                f"{item.source.upper()}</span>"
                f"<br><h3>{item.title}</h3>"
            )

            # Meta info
            meta_parts = [f"<b>From:</b> {item.sender}"]
            meta_parts.append(f"<b>Date:</b> {item.timestamp.strftime('%B %d, %Y %I:%M %p')}")
            if item.bw_student_name:
                meta_parts.append(f"<b>Student:</b> {item.bw_student_name}")
            if item.bw_room:
                meta_parts.append(f"<b>Room:</b> {item.bw_room}")
            if item.bw_action_type:
                meta_parts.append(f"<b>Type:</b> {item.bw_action_type}")
            self._meta_label.setText("<br>".join(meta_parts))

            # Body content
            if item.body_html:
                self._web_view.setHtml(item.body_html)
            elif item.body_plain:
                # Wrap plain text in basic HTML
                escaped = item.body_plain.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                self._web_view.setHtml(f"<pre style='font-family:sans-serif;white-space:pre-wrap;'>{escaped}</pre>")
            else:
                self._web_view.setHtml("<p style='color:#999;'>No content</p>")

            # Attachments
            attachments = session.query(Attachment).filter_by(communication_id=item.id).all()
            photo_paths = []
            other_attachments = []

            for att in attachments:
                if att.mime_type and att.mime_type.startswith("image/"):
                    photo_paths.append(att.local_path or att.remote_url or "")
                else:
                    other_attachments.append(att)

            self._photo_gallery.set_photos(photo_paths)

            if other_attachments:
                att_lines = ["<b>Attachments:</b><br>"]
                for att in other_attachments:
                    status = " (downloaded)" if att.is_downloaded else ""
                    att_lines.append(f"\u2022 {att.filename} ({att.mime_type or 'unknown'}){status}<br>")
                self._attachments_label.setText("".join(att_lines))
                self._attachments_label.setVisible(True)
            else:
                self._attachments_label.setVisible(False)

        finally:
            session.close()

    def _show_empty(self):
        self._title_label.setText("<h3 style='color:#999;'>Select an item to view details</h3>")
        self._meta_label.setText("")
        self._web_view.setHtml("")
        self._photo_gallery.clear()
        self._attachments_label.setVisible(False)
