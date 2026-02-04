"""Gmail API client: OAuth2 flow, message fetching, and attachment download."""

import base64
import email.utils
import logging
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.config.settings import (
    ATTACHMENTS_DIR,
    GMAIL_MAX_RESULTS,
    GMAIL_SCOPES,
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_TOKEN_PATH,
)
from src.config.gmail_query import build_gmail_query

logger = logging.getLogger(__name__)


class GmailService:
    """Handles Gmail OAuth2 and message retrieval."""

    def __init__(self):
        self._service = None
        self._creds = None

    @property
    def is_authenticated(self) -> bool:
        return self._creds is not None and self._creds.valid

    def authenticate(self, force_new: bool = False) -> bool:
        """Run OAuth2 flow. Returns True on success."""
        self._creds = None

        # Try loading existing token
        if not force_new and GOOGLE_TOKEN_PATH.exists():
            self._creds = Credentials.from_authorized_user_file(
                str(GOOGLE_TOKEN_PATH), GMAIL_SCOPES
            )

        # Refresh if expired
        if self._creds and self._creds.expired and self._creds.refresh_token:
            try:
                self._creds.refresh(Request())
            except Exception:
                logger.warning("Token refresh failed, will re-authenticate")
                self._creds = None

        # Need new auth flow
        if not self._creds or not self._creds.valid:
            if not GOOGLE_CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Google credentials.json not found at {GOOGLE_CREDENTIALS_PATH}. "
                    "Download it from Google Cloud Console and place it there, "
                    "or use Settings to browse to it."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GOOGLE_CREDENTIALS_PATH), GMAIL_SCOPES
            )
            self._creds = flow.run_local_server(port=0)

            # Save token for next time
            GOOGLE_TOKEN_PATH.write_text(self._creds.to_json())

        self._service = build("gmail", "v1", credentials=self._creds)
        return True

    def _ensure_service(self):
        if self._service is None:
            self.authenticate()

    def fetch_messages(
        self, page_token: str | None = None, max_results: int = GMAIL_MAX_RESULTS
    ) -> tuple[list[dict], str | None]:
        """Fetch messages matching the school query.

        Returns (messages, next_page_token). Each message is a full message resource dict.
        """
        self._ensure_service()
        query = build_gmail_query()

        result = (
            self._service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results, pageToken=page_token)
            .execute()
        )

        message_ids = result.get("messages", [])
        next_token = result.get("nextPageToken")

        messages = []
        for msg_stub in message_ids:
            msg = (
                self._service.users()
                .messages()
                .get(userId="me", id=msg_stub["id"], format="full")
                .execute()
            )
            messages.append(msg)

        return messages, next_token

    def download_attachment(self, message_id: str, attachment_id: str, filename: str) -> Path:
        """Download an attachment and return the local file path."""
        self._ensure_service()

        att = (
            self._service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )

        data = base64.urlsafe_b64decode(att["data"])
        local_path = ATTACHMENTS_DIR / f"{message_id}_{filename}"
        local_path.write_bytes(data)
        return local_path

    @staticmethod
    def parse_message(msg: dict) -> dict:
        """Parse a Gmail API message resource into a flat dict.

        Returns dict with keys: message_id, thread_id, timestamp, subject, sender,
        body_plain, body_html, label_ids, snippet, attachments.
        """
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}

        # Parse timestamp
        internal_date = int(msg.get("internalDate", 0))
        timestamp = datetime.fromtimestamp(internal_date / 1000) if internal_date else datetime.now()

        # Extract body parts and attachments
        parts_store: dict[str, list[str]] = {"plain": [], "html": []}
        attachments: list[dict] = []
        GmailService._extract_parts(msg["payload"], body_parts=parts_store, attachments=attachments)
        body_plain = "\n".join(parts_store["plain"])
        body_html = "\n".join(parts_store["html"])

        return {
            "message_id": msg["id"],
            "thread_id": msg.get("threadId", ""),
            "timestamp": timestamp,
            "subject": headers.get("subject", "(no subject)"),
            "sender": headers.get("from", ""),
            "body_plain": body_plain,
            "body_html": body_html,
            "label_ids": msg.get("labelIds", []),
            "snippet": msg.get("snippet", ""),
            "attachments": attachments,
        }

    @staticmethod
    def _extract_parts(payload: dict, body_parts: dict[str, list[str]], attachments: list[dict]):
        """Recursively extract body text and attachment info from message payload."""
        mime_type = payload.get("mimeType", "")
        body = payload.get("body", {})

        if mime_type == "text/plain" and body.get("data"):
            body_parts["plain"].append(
                base64.urlsafe_b64decode(body["data"]).decode("utf-8", errors="replace")
            )
        elif mime_type == "text/html" and body.get("data"):
            body_parts["html"].append(
                base64.urlsafe_b64decode(body["data"]).decode("utf-8", errors="replace")
            )
        elif body.get("attachmentId"):
            attachments.append({
                "attachment_id": body["attachmentId"],
                "filename": payload.get("filename", "attachment"),
                "mime_type": mime_type,
                "size": body.get("size", 0),
            })

        for part in payload.get("parts", []):
            GmailService._extract_parts(part, body_parts, attachments)
