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
from src.ui.theme import COLORS, source_badge_html
from src.ui.widgets.photo_gallery import PhotoGallery


def _themed_html_wrapper(inner_html: str) -> str:
    """Wrap HTML content with themed CSS for the web view."""
    return f"""<!DOCTYPE html>
<html><head><style>
    body {{
        font-family: Helvetica, Arial, sans-serif;
        font-size: 14px;
        color: {COLORS['text_primary']};
        background-color: {COLORS['surface']};
        line-height: 1.5;
        padding: 8px;
        margin: 0;
    }}
    a {{ color: {COLORS['accent']}; }}
    a:hover {{ color: {COLORS['accent_hover']}; }}
    pre {{
        font-family: Helvetica, Arial, sans-serif;
        white-space: pre-wrap;
        word-wrap: break-word;
    }}
    img {{ max-width: 100%; height: auto; }}
</style></head><body>{inner_html}</body></html>"""


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
        sep.setStyleSheet(f"color: {COLORS['border_light']};")
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
                f"{badge}"
                f"<br><h3 style='color:{COLORS['navy']};margin-top:6px;'>{item.title}</h3>"
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
            self._meta_label.setText(
                f"<span style='color:{COLORS['text_secondary']};'>"
                + "<br>".join(meta_parts) + "</span>"
            )

            # Body content
            if item.body_html:
                self._web_view.setHtml(_themed_html_wrapper(item.body_html))
            elif item.body_plain:
                escaped = item.body_plain.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                self._web_view.setHtml(_themed_html_wrapper(f"<pre>{escaped}</pre>"))
            else:
                self._web_view.setHtml(
                    _themed_html_wrapper(f"<p style='color:{COLORS['text_muted']};'>No content</p>")
                )

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
                att_lines = [f"<b style='color:{COLORS['navy']};'>Attachments:</b><br>"]
                for att in other_attachments:
                    status = " (downloaded)" if att.is_downloaded else ""
                    att_lines.append(f"\u2022 {att.filename} ({att.mime_type or 'unknown'}){status}<br>")
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
                            f"<div style='background:{COLORS['surface']};"
                            f"border:1px solid {COLORS['border_light']};"
                            f"border-radius:4px;padding:6px;margin:4px 0 8px 16px;"
                            f"font-size:12px;color:{COLORS['text_secondary']};'>"
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
            f"<h3 style='color:{COLORS['text_muted']};'>Select an item to view details</h3>"
        )
        self._meta_label.setText("")
        self._web_view.setHtml("")
        self._photo_gallery.clear()
        self._attachments_label.setVisible(False)
