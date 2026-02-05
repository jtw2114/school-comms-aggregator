"""Orchestrates fetching from Gmail, Brightwheel, and WhatsApp, mapping to CommunicationItem."""

import json
import logging
import os
from datetime import datetime
from urllib.parse import unquote, urlparse

from sqlalchemy.exc import IntegrityError

from src.config.settings import ATTACHMENTS_DIR
from src.models.base import get_session
from src.models.communication import Attachment, CommunicationItem, SyncState
from src.services.gmail_service import GmailService
from src.services.brightwheel_auth import BrightwheelAuth
from src.services.brightwheel_service import BrightwheelService
from src.services.whatsapp_service import WhatsAppService
from src.services.credential_manager import get_wa_groups
from src.utils.date_utils import parse_timestamp

logger = logging.getLogger(__name__)

# Mime type mapping by file extension
_EXT_MIME_MAP = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

PDF_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


class SyncService:
    """Fetches data from sources and stores as CommunicationItems."""

    def __init__(self, progress_callback=None):
        self._progress = progress_callback or (lambda msg: None)

    def sync_gmail(self):
        """Fetch Gmail messages and store them."""
        self._progress("Connecting to Gmail...")
        gmail = GmailService()
        gmail.authenticate()

        session = get_session()
        try:
            # Get sync state
            state = session.query(SyncState).filter_by(source="gmail").first()
            page_token = state.page_cursor if state else None

            total_new = 0
            pages_fetched = 0
            max_pages = 10  # Safety limit

            while pages_fetched < max_pages:
                self._progress(f"Fetching Gmail page {pages_fetched + 1}...")
                messages, next_token = gmail.fetch_messages(page_token=page_token)

                if not messages:
                    break

                for msg in messages:
                    parsed = GmailService.parse_message(msg)
                    source_id = f"gmail_{parsed['message_id']}"

                    # Skip duplicates
                    existing = session.query(CommunicationItem).filter_by(source_id=source_id).first()
                    if existing:
                        continue

                    item = CommunicationItem(
                        timestamp=parsed["timestamp"],
                        title=parsed["subject"],
                        sender=parsed["sender"],
                        body_plain=parsed["body_plain"],
                        body_html=parsed["body_html"],
                        source="gmail",
                        source_id=source_id,
                        gmail_thread_id=parsed["thread_id"],
                        gmail_label_ids=json.dumps(parsed["label_ids"]),
                        gmail_snippet=parsed["snippet"],
                    )
                    session.add(item)
                    session.flush()

                    # Add attachments
                    for att_info in parsed["attachments"]:
                        att = Attachment(
                            communication_id=item.id,
                            filename=att_info["filename"],
                            mime_type=att_info["mime_type"],
                            remote_url=att_info.get("attachment_id", ""),
                            is_downloaded=False,
                        )
                        session.add(att)

                    total_new += 1

                pages_fetched += 1
                page_token = next_token
                if not next_token:
                    break

            # Update sync state
            if not state:
                state = SyncState(source="gmail")
                session.add(state)
            state.last_sync_at = datetime.now()
            # Store the next page token for future incremental syncs
            state.page_cursor = next_token

            session.commit()
            self._progress(f"Gmail sync complete: {total_new} new messages")
            logger.info(f"Gmail sync: {total_new} new messages, {pages_fetched} pages")

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def sync_brightwheel(self):
        """Fetch Brightwheel activities and store them."""
        self._progress("Connecting to Brightwheel...")

        auth = BrightwheelAuth()
        if not auth.restore_session():
            raise RuntimeError(
                "No Brightwheel session found. Use Accounts > Setup Brightwheel to login first."
            )

        bw = BrightwheelService(auth)

        # Get user info
        self._progress("Fetching Brightwheel user info...")
        user_data = bw.get_current_user()

        # Find guardian ID - search through various possible response structures
        logger.info(f"Brightwheel user data keys: {list(user_data.keys())}")
        logger.info(f"Brightwheel user data: {json.dumps(user_data, indent=2, default=str)[:2000]}")

        guardian_id = None
        user = user_data.get("user", user_data)

        # Try direct fields
        for key in ("guardian_id", "id", "object_id", "guardian_object_id"):
            val = user.get(key)
            if val:
                guardian_id = str(val)
                logger.info(f"Found guardian_id via user['{key}']: {guardian_id}")
                break

        # Try nested in roles
        if not guardian_id:
            for role in user.get("roles", []):
                if isinstance(role, dict) and role.get("type") in ("guardian", "parent"):
                    guardian_id = str(role.get("id", role.get("object_id", "")))
                    if guardian_id:
                        logger.info(f"Found guardian_id via roles: {guardian_id}")
                        break

        # Try guardians list
        if not guardian_id:
            guardians = user.get("guardians", user_data.get("guardians", []))
            if guardians and isinstance(guardians, list):
                guardian_id = str(guardians[0].get("id", guardians[0].get("object_id", "")))
                logger.info(f"Found guardian_id via guardians list: {guardian_id}")

        if not guardian_id:
            raise RuntimeError(
                f"Could not determine guardian ID from Brightwheel user data. "
                f"Response keys: {list(user_data.keys())}. "
                f"User keys: {list(user.keys()) if isinstance(user, dict) else 'N/A'}. "
                f"Please check the logs or try the manual cookie fallback."
            )

        # Get students - each entry has a nested "student" key
        self._progress("Fetching student list...")
        student_entries = bw.get_students(guardian_id)
        self._progress(f"Found {len(student_entries)} students")

        session = get_session()
        try:
            # Get sync state for cutoff date
            state = session.query(SyncState).filter_by(source="brightwheel").first()
            since = state.last_sync_at if state else None

            total_new = 0

            for entry in student_entries:
                # Student info is nested under "student" key
                student = entry.get("student", entry)
                student_name = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip()
                student_id = student.get("object_id", student.get("id", ""))
                logger.info(f"Student: {student_name}, ID: {student_id}")
                if not student_id:
                    logger.warning(f"Skipping student with no ID: {entry}")
                    continue

                # Fetch activities
                self._progress(f"Fetching activities for {student_name}...")
                activities = bw.fetch_all_activities(student_id, since=since)
                self._progress(f"Got {len(activities)} activities for {student_name}")

                for activity in activities:
                    parsed = BrightwheelService.parse_activity(activity, student_name=student_name)
                    total_new += self._store_bw_item(session, parsed)

                # Fetch messages
                self._progress(f"Fetching messages for {student_name}...")
                messages = bw.fetch_all_messages(student_id, since=since)
                self._progress(f"Got {len(messages)} messages for {student_name}")

                for msg_result in messages:
                    parsed = BrightwheelService.parse_message(msg_result, student_name=student_name)
                    total_new += self._store_bw_item(session, parsed)

            # Update sync state
            if not state:
                state = SyncState(source="brightwheel")
                session.add(state)
            state.last_sync_at = datetime.now()

            session.commit()
            self._progress(f"Brightwheel sync complete: {total_new} new items")
            logger.info(f"Brightwheel sync: {total_new} new items")

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        # Download and extract text from PDF attachments (separate transaction)
        try:
            self._download_and_extract_pdfs(auth)
        except Exception:
            logger.warning("PDF download/extraction failed", exc_info=True)

    def _download_and_extract_pdfs(self, auth: BrightwheelAuth):
        """Download PDF attachments from Brightwheel and extract text with pdfplumber."""
        import pdfplumber
        import requests

        session = get_session()
        try:
            pending_pdfs = (
                session.query(Attachment)
                .join(CommunicationItem)
                .filter(
                    CommunicationItem.source == "brightwheel",
                    Attachment.mime_type == "application/pdf",
                    Attachment.is_downloaded == False,  # noqa: E712
                )
                .all()
            )

            if not pending_pdfs:
                return

            self._progress(f"Downloading {len(pending_pdfs)} PDF attachment(s)...")
            logger.info(f"Downloading {len(pending_pdfs)} PDF attachment(s)")

            http_session = requests.Session()
            http_session.cookies.update(auth.get_cookies_dict())

            ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

            for att in pending_pdfs:
                try:
                    if not att.remote_url:
                        continue

                    # Download with size limit
                    resp = http_session.get(att.remote_url, stream=True, timeout=30)
                    resp.raise_for_status()

                    content_length = int(resp.headers.get("content-length", 0))
                    if content_length > PDF_MAX_SIZE:
                        logger.warning(f"PDF too large ({content_length} bytes), skipping: {att.filename}")
                        continue

                    # Read content with size guard
                    chunks = []
                    total_bytes = 0
                    for chunk in resp.iter_content(chunk_size=8192):
                        total_bytes += len(chunk)
                        if total_bytes > PDF_MAX_SIZE:
                            logger.warning(f"PDF exceeded size limit during download, skipping: {att.filename}")
                            break
                        chunks.append(chunk)
                    else:
                        # Only process if download completed (no break)
                        pdf_data = b"".join(chunks)

                        # Save to disk
                        safe_filename = att.filename.replace("/", "_").replace("\\", "_")
                        local_filename = f"{att.communication_id}_{att.id}_{safe_filename}"
                        local_path = ATTACHMENTS_DIR / local_filename
                        local_path.write_bytes(pdf_data)

                        # Extract text
                        extracted_pages = []
                        with pdfplumber.open(local_path) as pdf:
                            for page in pdf.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    extracted_pages.append(page_text)

                        extracted_text = "\n\n".join(extracted_pages) if extracted_pages else ""

                        # Update record
                        att.local_path = str(local_path)
                        att.is_downloaded = True
                        att.extracted_text = extracted_text if extracted_text else None

                        logger.info(
                            f"Extracted {len(extracted_text)} chars from PDF: {att.filename}"
                        )

                except Exception:
                    logger.warning(f"Failed to download/extract PDF: {att.filename}", exc_info=True)

            session.commit()

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _store_bw_item(self, session, parsed: dict) -> int:
        """Store a parsed Brightwheel item. Returns 1 if new, 0 if duplicate."""
        source_id = parsed.get("source_id", "")
        if not source_id or source_id in ("bw_act_", "bw_msg_"):
            return 0

        existing = session.query(CommunicationItem).filter_by(source_id=source_id).first()
        if existing:
            return 0

        try:
            ts = parse_timestamp(parsed["timestamp"])
        except (ValueError, TypeError):
            ts = datetime.now()

        item = CommunicationItem(
            timestamp=ts,
            title=parsed["title"],
            sender=parsed["sender"],
            body_plain=parsed["body_plain"],
            source="brightwheel",
            source_id=source_id,
            bw_student_name=parsed["student_name"],
            bw_room=parsed["room"],
            bw_action_type=parsed["action_type"],
            bw_details=parsed["details"],
        )
        session.add(item)
        session.flush()

        # Use structured attachment_list if available, fall back to photos list
        attachment_list = parsed.get("attachment_list", [])
        if attachment_list:
            for att_info in attachment_list:
                url = att_info["url"]
                filename = att_info.get("filename", "attachment")
                # Determine mime type: use API content_type, then URL extension, then default
                mime_type = att_info.get("content_type", "")
                if not mime_type:
                    ext = os.path.splitext(urlparse(url).path)[1].lower()
                    mime_type = _EXT_MIME_MAP.get(ext, "image/jpeg")
                att = Attachment(
                    communication_id=item.id,
                    filename=filename,
                    mime_type=mime_type,
                    remote_url=url,
                    is_downloaded=False,
                )
                session.add(att)
        else:
            # Backward compat: fall back to plain photos list
            for photo_url in parsed.get("photos", []):
                ext = os.path.splitext(urlparse(photo_url).path)[1].lower()
                mime_type = _EXT_MIME_MAP.get(ext, "image/jpeg")
                att = Attachment(
                    communication_id=item.id,
                    filename=unquote(urlparse(photo_url).path.rsplit("/", 1)[-1]) or "photo.jpg",
                    mime_type=mime_type,
                    remote_url=photo_url,
                    is_downloaded=False,
                )
                session.add(att)

        return 1

    def sync_whatsapp(self):
        """Fetch WhatsApp group messages and store them."""
        groups = get_wa_groups()
        if not groups:
            self._progress("No WhatsApp groups configured. Set them in Settings.")
            return

        svc = WhatsAppService()
        if not svc.has_session():
            raise RuntimeError(
                "WhatsApp not set up. Use Accounts > Setup WhatsApp first."
            )

        session = get_session()
        try:
            state = session.query(SyncState).filter_by(source="whatsapp").first()
            since = state.last_sync_at if state else None

            total_new = 0

            for group_name in groups:
                self._progress(f"Scraping WhatsApp group: {group_name}...")
                messages = svc.scrape_group(group_name, since=since)
                self._progress(f"Got {len(messages)} messages from {group_name}")

                for msg in messages:
                    source_id = msg["source_id"]

                    existing = session.query(CommunicationItem).filter_by(
                        source_id=source_id
                    ).first()
                    if existing:
                        continue

                    item = CommunicationItem(
                        timestamp=msg["timestamp"],
                        title=msg["title"],
                        sender=msg["sender"],
                        body_plain=msg["body_plain"],
                        source="whatsapp",
                        source_id=source_id,
                    )
                    session.add(item)
                    session.flush()
                    total_new += 1

            # Update sync state
            if not state:
                state = SyncState(source="whatsapp")
                session.add(state)
            state.last_sync_at = datetime.now()

            session.commit()
            self._progress(f"WhatsApp sync complete: {total_new} new messages")
            logger.info(f"WhatsApp sync: {total_new} new messages")

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
