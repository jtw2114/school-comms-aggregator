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
from src.ui.theme import COLORS, get_webview_css, source_badge_html
from src.ui.widgets.photo_gallery import PhotoGallery


def _themed_html_wrapper(inner_html: str) -> str:
    """Wrap HTML content with themed CSS for the web view."""
    css = get_webview_css()
    return f"""<!DOCTYPE html>
<html><head><style>
{css}
pre {{
    font-family: inherit;
    white-space: pre-wrap;
    word-wrap: break-word;
}}
</style></head><body>{inner_html}</body></html>"""


class DetailPanel(QWidget):
    """Right-side panel showing full details of a selected communication."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header area
        self._title_label = QLabel()
        self._title_label.setWordWrap(True)
        self._title_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._title_label)

        self._meta_label = QLabel()
        self._meta_label.setObjectName("caption")
        self._meta_label.setWordWrap(True)
        layout.addWidget(self._meta_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setLineWidth(1)
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
            badge = source_badge_html(item.source)
            self._title_label.setText(
                f"{badge}<br><span style='font-size:18px;font-weight:600;'>{item.title}</span>"
            )

            # Meta info
            meta_parts = [f"From: {item.sender}"]
            meta_parts.append(f"Date: {item.timestamp.strftime('%B %d, %Y %I:%M %p')}")
            if item.bw_student_name:
                meta_parts.append(f"Student: {item.bw_student_name}")
            if item.bw_room:
                meta_parts.append(f"Room: {item.bw_room}")
            if item.bw_action_type:
                meta_parts.append(f"Type: {item.bw_action_type}")
            self._meta_label.setText(" • ".join(meta_parts))

            # Body content
            if item.body_html:
                self._web_view.setHtml(_themed_html_wrapper(item.body_html))
            elif item.body_plain:
                escaped = item.body_plain.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                self._web_view.setHtml(_themed_html_wrapper(f"<pre>{escaped}</pre>"))
            else:
                self._web_view.setHtml(_themed_html_wrapper("<p style='color:#86868B;'>No content</p>"))

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
                att_lines = ["<b>Attachments</b><br>"]
                for att in other_attachments:
                    status = " (downloaded)" if att.is_downloaded else ""
                    att_lines.append(f"• {att.filename} ({att.mime_type or 'unknown'}){status}<br>")
                    # Show extracted text preview for PDFs
                    if att.extracted_text:
                        preview = att.extracted_text[:500]
                        if len(att.extracted_text) > 500:
                            preview += "..."
                        escaped_preview = (
                            preview.replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;")
                            .replace("\n", "<br>")
                        )
                        att_lines.append(
                            f"<div style='background:#F5F5F7;"
                            f"border:1px solid #E5E5EA;"
                            f"border-radius:8px;padding:10px;margin:8px 0 12px 16px;"
                            f"font-size:12px;color:#86868B;'>"
                            f"<b>Extracted text:</b><br>{escaped_preview}</div>"
                        )
                self._attachments_label.setText("".join(att_lines))
                self._attachments_label.setVisible(True)
            else:
                self._attachments_label.setVisible(False)

        finally:
            session.close()

    def _show_empty(self):
        self._title_label.setText(
            "<span style='font-size:16px;color:#86868B;'>Select an item to view details</span>"
        )
        self._meta_label.setText("")
        self._web_view.setHtml("")
        self._photo_gallery.clear()
        self._attachments_label.setVisible(False)
