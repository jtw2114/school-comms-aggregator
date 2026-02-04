"""WhatsApp Web authentication and message scraping via Playwright.

WhatsApp Web has no REST API, so Playwright is used for both authentication
(QR code scanning) and message scraping (DOM interaction). The browser must
run in headed mode because WhatsApp Web actively detects headless browsers.
"""

import hashlib
import json
import logging
import re
from datetime import datetime

from src.config.settings import WA_LOGIN_TIMEOUT_MS, WA_SESSION_PATH

logger = logging.getLogger(__name__)

# WhatsApp Web URL
WA_URL = "https://web.whatsapp.com"

# --- DOM Selectors ---
# WhatsApp Web uses data-testid attributes. These may change when WhatsApp
# updates their UI — keep them here as constants for easy maintenance.
SEL_SIDE_PANEL = 'div[data-testid="chat-list"]'
SEL_SEARCH_INPUT = 'div[data-testid="chat-list-search-input"]'
SEL_SEARCH_RESULT_TITLE = 'span[data-testid="cell-frame-title"] span[dir]'
SEL_CONVERSATION_PANEL = 'div[data-testid="conversation-panel-messages"]'
SEL_MSG_ROW = 'div[data-testid="msg-container"]'
SEL_MSG_TEXT = 'span[data-testid="msg-text"]'
SEL_MSG_META = 'div[data-testid="msg-meta"]'

# Fallback selectors (ARIA-based) in case data-testid changes
SEL_SIDE_PANEL_FALLBACK = '#pane-side'
SEL_SEARCH_INPUT_FALLBACK = 'div[role="textbox"][data-tab="3"]'
SEL_CONVERSATION_PANEL_FALLBACK = '#main div[role="application"]'


class WhatsAppService:
    """Handles WhatsApp Web QR code auth and DOM-based message scraping."""

    def __init__(self):
        self._session_path = WA_SESSION_PATH

    def setup(self) -> bool:
        """Open WhatsApp Web in a visible browser for QR code scanning.

        The user must scan the QR code with their phone. Once the chat list
        appears, the session state is saved for future scraping.

        Returns True on success.
        """
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            try:
                page.goto(WA_URL, wait_until="domcontentloaded")
                logger.info("Waiting for user to scan QR code...")

                # Wait for the chat list / side panel to appear
                page.wait_for_selector(
                    f"{SEL_SIDE_PANEL}, {SEL_SIDE_PANEL_FALLBACK}",
                    timeout=WA_LOGIN_TIMEOUT_MS,
                )
                logger.info("QR code scanned, chat list visible")

                # Save session state
                self._session_path.parent.mkdir(parents=True, exist_ok=True)
                context.storage_state(path=str(self._session_path))
                logger.info(f"Session saved to {self._session_path}")
                return True

            except Exception as e:
                logger.error(f"WhatsApp setup failed: {e}")
                raise
            finally:
                browser.close()

    def has_session(self) -> bool:
        """Check if a saved session file exists."""
        return self._session_path.exists()

    def scrape_group(self, group_name: str, since: datetime | None) -> list[dict]:
        """Open WhatsApp Web with saved session, navigate to a group, and scrape messages.

        Args:
            group_name: The exact name of the WhatsApp group to scrape.
            since: Only return messages after this timestamp. If None, scrape all visible.

        Returns:
            List of normalized dicts ready for CommunicationItem storage.
        """
        from playwright.sync_api import sync_playwright

        if not self.has_session():
            raise RuntimeError("No WhatsApp session found. Run setup first.")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                storage_state=str(self._session_path),
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            try:
                page.goto(WA_URL, wait_until="domcontentloaded")

                # Wait for chat list to load (session restored)
                page.wait_for_selector(
                    f"{SEL_SIDE_PANEL}, {SEL_SIDE_PANEL_FALLBACK}",
                    timeout=30_000,
                )
                logger.info("Chat list loaded, searching for group...")

                # Search for the group
                self._open_group(page, group_name)

                # Scrape messages
                messages = self._scrape_messages(page, group_name, since)

                # Re-save session to keep it fresh
                context.storage_state(path=str(self._session_path))

                return messages

            except Exception as e:
                logger.error(f"WhatsApp scrape failed for '{group_name}': {e}")
                raise
            finally:
                browser.close()

    def _open_group(self, page, group_name: str):
        """Search for and open a group chat by name."""
        # Click the search input
        search_input = page.query_selector(SEL_SEARCH_INPUT)
        if not search_input:
            search_input = page.query_selector(SEL_SEARCH_INPUT_FALLBACK)
        if not search_input:
            # Try clicking the search bar area first
            page.click('div[data-testid="chat-list-search"]', timeout=5_000)
            search_input = page.wait_for_selector(
                f"{SEL_SEARCH_INPUT}, {SEL_SEARCH_INPUT_FALLBACK}",
                timeout=5_000,
            )

        search_input.click()
        search_input.fill(group_name)

        # Wait for search results to populate
        page.wait_for_timeout(1500)

        # Find the matching group in search results
        results = page.query_selector_all(SEL_SEARCH_RESULT_TITLE)
        matched = False
        for result in results:
            title = (result.inner_text() or "").strip()
            if title.lower() == group_name.lower():
                result.click()
                matched = True
                break

        if not matched:
            # Fallback: click the first result that contains the group name
            for result in results:
                title = (result.inner_text() or "").strip()
                if group_name.lower() in title.lower():
                    result.click()
                    matched = True
                    break

        if not matched:
            raise RuntimeError(f"Group '{group_name}' not found in WhatsApp search results")

        # Wait for conversation panel to load
        page.wait_for_selector(
            f"{SEL_CONVERSATION_PANEL}, {SEL_CONVERSATION_PANEL_FALLBACK}",
            timeout=10_000,
        )
        page.wait_for_timeout(1000)
        logger.info(f"Opened group: {group_name}")

    def _scrape_messages(self, page, group_name: str, since: datetime | None) -> list[dict]:
        """Extract messages from the currently open chat panel."""
        messages = []

        # Scroll up to load older messages if we have a since date
        if since:
            self._scroll_to_load(page, since)

        # Get all message containers
        msg_elements = page.query_selector_all(SEL_MSG_ROW)
        logger.info(f"Found {len(msg_elements)} message elements in '{group_name}'")

        for el in msg_elements:
            try:
                msg = self._parse_message_element(el, group_name)
                if msg is None:
                    continue

                # Filter by date if needed
                if since and msg["timestamp"] < since:
                    continue

                messages.append(msg)
            except Exception as e:
                logger.debug(f"Skipping unparseable message element: {e}")
                continue

        logger.info(f"Parsed {len(messages)} messages from '{group_name}'")
        return messages

    def _parse_message_element(self, el, group_name: str) -> dict | None:
        """Parse a single message element into a normalized dict."""
        # Extract message text
        text_el = el.query_selector(SEL_MSG_TEXT)
        if not text_el:
            return None
        body = text_el.inner_text().strip()
        if not body:
            return None

        # Extract sender — in group chats, sender is shown above the message
        sender = "Unknown"
        # Try data-testid for sender
        sender_el = el.query_selector('span[data-testid="msg-author"]')
        if not sender_el:
            # Fallback: look for the sender span by aria-label or class patterns
            sender_el = el.query_selector('div[data-pre-plain-text]')
            if sender_el:
                pre_text = sender_el.get_attribute("data-pre-plain-text") or ""
                # Format is typically "[HH:MM, DD/MM/YYYY] Sender Name: "
                match = re.search(r'\]\s*(.+?):\s*$', pre_text)
                if match:
                    sender = match.group(1).strip()
        if sender_el and sender == "Unknown":
            sender = sender_el.inner_text().strip()

        # Extract timestamp
        timestamp = datetime.now()
        meta_el = el.query_selector(SEL_MSG_META)
        if meta_el:
            time_el = meta_el.query_selector("span")
            if time_el:
                time_text = time_el.inner_text().strip()
                timestamp = self._parse_wa_time(time_text)

        # Also try data-pre-plain-text attribute for more accurate timestamps
        pre_plain = el.query_selector('div[data-pre-plain-text]')
        if pre_plain:
            pre_text = pre_plain.get_attribute("data-pre-plain-text") or ""
            parsed_ts = self._parse_pre_plain_text_timestamp(pre_text)
            if parsed_ts:
                timestamp = parsed_ts

        source_id = self.generate_source_id(timestamp, sender, body)

        return {
            "timestamp": timestamp,
            "title": f"[{group_name}] {sender}",
            "sender": sender,
            "body_plain": body,
            "source": "whatsapp",
            "source_id": source_id,
            "group_name": group_name,
        }

    def _scroll_to_load(self, page, since: datetime):
        """Scroll up in the chat to load messages back to the `since` date."""
        conversation = page.query_selector(
            f"{SEL_CONVERSATION_PANEL}, {SEL_CONVERSATION_PANEL_FALLBACK}"
        )
        if not conversation:
            return

        max_scrolls = 20
        for _ in range(max_scrolls):
            # Check if we've reached far enough back
            first_msg = page.query_selector(SEL_MSG_ROW)
            if first_msg:
                pre_plain = first_msg.query_selector('div[data-pre-plain-text]')
                if pre_plain:
                    pre_text = pre_plain.get_attribute("data-pre-plain-text") or ""
                    ts = self._parse_pre_plain_text_timestamp(pre_text)
                    if ts and ts <= since:
                        break

            # Scroll up
            conversation.evaluate("el => el.scrollTop = 0")
            page.wait_for_timeout(1000)

    @staticmethod
    def _parse_wa_time(time_text: str) -> datetime:
        """Parse a WhatsApp time string like '10:30 AM' into today's datetime."""
        today = datetime.now()
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                t = datetime.strptime(time_text, fmt)
                return today.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            except ValueError:
                continue
        return today

    @staticmethod
    def _parse_pre_plain_text_timestamp(pre_text: str) -> datetime | None:
        """Parse timestamp from data-pre-plain-text attribute.

        Format examples:
            [10:30 AM, 1/15/2025] Sender:
            [10:30, 15/01/2025] Sender:
        """
        match = re.search(r'\[(.+?),\s*(.+?)\]', pre_text)
        if not match:
            return None

        time_part = match.group(1).strip()
        date_part = match.group(2).strip()

        for time_fmt in ("%I:%M %p", "%H:%M"):
            for date_fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(f"{time_part} {date_part}", f"{time_fmt} {date_fmt}")
                except ValueError:
                    continue

        return None

    @staticmethod
    def generate_source_id(timestamp: datetime, sender: str, body: str) -> str:
        """Deterministic hash for deduplication."""
        raw = f"{timestamp.isoformat()}|{sender}|{body}"
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return f"wa_{h}"
