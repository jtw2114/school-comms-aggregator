"""WhatsApp Web authentication and message scraping via Playwright.

WhatsApp Web has no REST API, so Playwright is used for both authentication
(QR code scanning) and message scraping (DOM interaction). The browser must
run in headed mode because WhatsApp Web actively detects headless browsers.

Uses a persistent browser profile (user data dir) instead of storage_state
because WhatsApp Web relies on IndexedDB for session management, which
storage_state does not capture.
"""

import hashlib
import logging
import re
from datetime import datetime

from src.config.settings import WA_LOGIN_TIMEOUT_MS, WA_PROFILE_DIR

logger = logging.getLogger(__name__)

# WhatsApp Web URL
WA_URL = "https://web.whatsapp.com"

# --- DOM Selectors ---
# WhatsApp Web uses data-testid attributes. These may change when WhatsApp
# updates their UI — keep them here as constants for easy maintenance.
SEL_SIDE_PANEL = 'div[data-testid="chat-list"]'
SEL_SEARCH_INPUT = 'div[data-testid="chat-list-search-input"]'
SEL_SEARCH_RESULT_TITLE = 'span[data-testid="cell-frame-title"] span[dir]'
SEL_CONVERSATION_PANEL = 'div[data-testid="conversation-panel-messages"], div[data-testid="conversation-panel-wrapper"]'
SEL_MSG_ROW = 'div[data-testid="msg-container"]'
SEL_MSG_TEXT = 'span[data-testid="msg-text"]'
SEL_MSG_META = 'div[data-testid="msg-meta"]'

# Fallback selectors (ARIA-based) in case data-testid changes
SEL_SIDE_PANEL_FALLBACK = '#pane-side'
SEL_SEARCH_INPUT_FALLBACK = 'div[role="textbox"][data-tab="3"]'
SEL_CONVERSATION_PANEL_FALLBACK = '#main div[role="application"]'


def _launch_persistent_context(playwright):
    """Launch a Chromium browser with a persistent user data directory.

    This preserves IndexedDB, Service Workers, and all browser state
    that WhatsApp Web needs to maintain a session.
    """
    WA_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(WA_PROFILE_DIR),
        headless=False,
        viewport={"width": 1280, "height": 900},
    )
    return context


class WhatsAppService:
    """Handles WhatsApp Web QR code auth and DOM-based message scraping."""

    def setup(self) -> bool:
        """Open WhatsApp Web in a visible browser for QR code scanning.

        The user must scan the QR code with their phone. Once the chat list
        appears, the session is persisted in the browser profile directory.

        Returns True on success.
        """
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            context = _launch_persistent_context(p)
            page = context.pages[0] if context.pages else context.new_page()

            try:
                page.goto(WA_URL, wait_until="domcontentloaded")
                logger.info("Waiting for user to scan QR code...")

                # Wait for the chat list / side panel to appear
                page.wait_for_selector(
                    f"{SEL_SIDE_PANEL}, {SEL_SIDE_PANEL_FALLBACK}",
                    timeout=WA_LOGIN_TIMEOUT_MS,
                )
                logger.info("QR code scanned, chat list visible")
                return True

            except Exception as e:
                logger.error(f"WhatsApp setup failed: {e}")
                raise
            finally:
                context.close()

    def has_session(self) -> bool:
        """Check if a persistent browser profile directory exists with data."""
        return WA_PROFILE_DIR.exists() and any(WA_PROFILE_DIR.iterdir())

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
            context = _launch_persistent_context(p)
            page = context.pages[0] if context.pages else context.new_page()

            try:
                page.goto(WA_URL, wait_until="domcontentloaded")

                # Wait for chat list to load (session restored)
                page.wait_for_selector(
                    f"{SEL_SIDE_PANEL}, {SEL_SIDE_PANEL_FALLBACK}",
                    timeout=60_000,
                )
                logger.info("Chat list loaded, searching for group...")

                # Search for the group
                self._open_group(page, group_name)

                # Scrape messages
                messages = self._scrape_messages(page, group_name, since)

                return messages

            except Exception as e:
                logger.error(f"WhatsApp scrape failed for '{group_name}': {e}")
                raise
            finally:
                context.close()

    def _open_group(self, page, group_name: str):
        """Search for and open a group chat by name."""
        # Give WhatsApp Web a moment to finish rendering after chat list appears
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        search_input = self._find_search_input(page)
        if not search_input:
            raise RuntimeError("Could not find WhatsApp search input")

        logger.info(f"Found search input, typing '{group_name}'...")
        search_input.click()
        page.wait_for_timeout(500)

        # Use fill() for <input> elements, keyboard.type() for contenteditable divs
        tag = search_input.evaluate("el => el.tagName")
        if tag == "INPUT":
            search_input.fill(group_name)
        else:
            page.keyboard.type(group_name, delay=50)

        # Wait for search results to populate
        page.wait_for_timeout(2000)

        # Log what we find for debugging
        results = page.query_selector_all(SEL_SEARCH_RESULT_TITLE)
        logger.info(f"Search results found: {len(results)} elements matching SEL_SEARCH_RESULT_TITLE")

        if not results:
            # Try broader selectors for search results
            results = page.query_selector_all('span[title]')
            logger.info(f"Fallback span[title] results: {len(results)}")
            for r in results[:10]:
                title = r.get_attribute("title") or ""
                logger.debug(f"  Result title attr: '{title}'")

        # Try to match by data-testid selector first
        matched = False
        results = page.query_selector_all(SEL_SEARCH_RESULT_TITLE)
        for result in results:
            title = (result.inner_text() or "").strip()
            if title.lower() == group_name.lower():
                result.click()
                matched = True
                logger.info(f"Exact match found: '{title}'")
                break

        if not matched:
            for result in results:
                title = (result.inner_text() or "").strip()
                if group_name.lower() in title.lower():
                    result.click()
                    matched = True
                    logger.info(f"Partial match found: '{title}'")
                    break

        # Fallback: try span[title] matching
        if not matched:
            spans = page.query_selector_all('span[title]')
            for span in spans:
                title = span.get_attribute("title") or ""
                if title.lower() == group_name.lower():
                    span.click()
                    matched = True
                    logger.info(f"Matched via span[title]: '{title}'")
                    break

        if not matched:
            # Last resort: try partial match on span[title]
            for span in spans:
                title = span.get_attribute("title") or ""
                if group_name.lower() in title.lower():
                    span.click()
                    matched = True
                    logger.info(f"Partial matched via span[title]: '{title}'")
                    break

        if not matched:
            raise RuntimeError(f"Group '{group_name}' not found in WhatsApp search results")

        # Wait for conversation panel to load
        page.wait_for_selector(
            f"{SEL_CONVERSATION_PANEL}, {SEL_CONVERSATION_PANEL_FALLBACK}, #main",
            timeout=10_000,
        )
        page.wait_for_timeout(1500)
        logger.info(f"Opened group: {group_name}")

        # Clear the search to reset the side panel
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

    def _find_search_input(self, page, timeout_ms: int = 15_000):
        """Locate the search input, retrying with multiple strategies."""
        # Broad set of selectors for the search input in various WA Web versions.
        # WhatsApp Web now uses a plain <input> with data-tab="3" for search.
        all_selectors = (
            'input[data-tab="3"], '
            f"{SEL_SEARCH_INPUT}, {SEL_SEARCH_INPUT_FALLBACK}, "
            'p.selectable-text[data-tab], div[contenteditable="true"][data-tab="3"], '
            'div[contenteditable="true"][role="textbox"]'
        )

        # Strategy 1: search input is already visible in the DOM
        try:
            return page.wait_for_selector(all_selectors, timeout=timeout_ms)
        except Exception:
            logger.debug("Direct wait for search input failed, trying activation")

        # Strategy 2: click known search bar containers to activate it
        click_targets = [
            'div[data-testid="chat-list-search"]',
            'button[data-testid="search-btn"]',
            'span[data-testid="search"]',
            'div[data-testid="chat-list-header"] span[data-icon]',
            '#pane-side header button',
        ]
        for target in click_targets:
            try:
                page.click(target, timeout=3_000)
                return page.wait_for_selector(all_selectors, timeout=5_000)
            except Exception:
                continue

        # Strategy 3: use Ctrl+/ keyboard shortcut (WhatsApp Web search hotkey)
        try:
            logger.debug("Trying Ctrl+/ keyboard shortcut for search")
            page.keyboard.press("Control+/")
            return page.wait_for_selector(all_selectors, timeout=5_000)
        except Exception:
            pass

        # Strategy 4: click the top of the side panel where search usually lives
        try:
            side_panel = page.query_selector(
                f"{SEL_SIDE_PANEL}, {SEL_SIDE_PANEL_FALLBACK}"
            )
            if side_panel:
                logger.debug("Clicking top of side panel to activate search")
                box = side_panel.bounding_box()
                if box:
                    # Click near the top center of the side panel
                    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 30)
                    page.wait_for_timeout(1000)
                    return page.wait_for_selector(all_selectors, timeout=5_000)
        except Exception:
            pass

        return None

    def _scrape_messages(self, page, group_name: str, since: datetime | None) -> list[dict]:
        """Extract messages from the currently open chat panel."""
        messages = []

        # Wait for messages to render
        page.wait_for_timeout(3000)

        # Scroll up to load older messages if we have a since date
        if since:
            self._scroll_to_load(page, since)

        msg_elements = page.query_selector_all('div[role="row"]')
        logger.info(f"Found {len(msg_elements)} div[role='row'] elements in '{group_name}'")

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
        # Extract message text — try multiple selectors
        text_el = None
        for sel in [
            SEL_MSG_TEXT,                    # data-testid="msg-text"
            'span.selectable-text',          # class-based
            'span[dir="ltr"]',               # text direction attribute
            'div.copyable-text span',        # copyable text container
        ]:
            text_el = el.query_selector(sel)
            if text_el:
                break

        if not text_el:
            # Last resort: get all text from the element, skip if too short
            full_text = el.inner_text().strip()
            if len(full_text) > 5:
                # Use the full element text but try to clean it
                body = full_text
            else:
                return None
        else:
            body = text_el.inner_text().strip()

        if not body:
            return None

        # Extract sender — in group chats, sender is shown above the message
        sender = "Unknown"

        # Try data-pre-plain-text attribute first (most reliable)
        pre_plain_el = el.query_selector('div[data-pre-plain-text]')
        if pre_plain_el:
            pre_text = pre_plain_el.get_attribute("data-pre-plain-text") or ""
            match = re.search(r'\]\s*(.+?):\s*$', pre_text)
            if match:
                sender = match.group(1).strip()

        # Fallback: try data-testid for sender
        if sender == "Unknown":
            sender_el = el.query_selector('span[data-testid="msg-author"]')
            if sender_el:
                sender = sender_el.inner_text().strip()

        # Fallback: try aria-label or any span that looks like a contact name
        if sender == "Unknown":
            sender_el = el.query_selector('span[aria-label]')
            if sender_el:
                label = sender_el.get_attribute("aria-label") or ""
                if label and ":" not in label and len(label) < 100:
                    sender = label

        # Extract timestamp
        timestamp = datetime.now()

        # Try data-pre-plain-text for full date+time (most accurate)
        if pre_plain_el:
            pre_text = pre_plain_el.get_attribute("data-pre-plain-text") or ""
            parsed_ts = self._parse_pre_plain_text_timestamp(pre_text)
            if parsed_ts:
                timestamp = parsed_ts

        # Fallback: try msg-meta time display
        if not pre_plain_el or timestamp == datetime.now():
            meta_el = el.query_selector(SEL_MSG_META)
            if not meta_el:
                # Try any small span that looks like a time
                meta_el = el.query_selector('span[dir="auto"]')
            if meta_el:
                time_el = meta_el.query_selector("span") or meta_el
                if time_el:
                    time_text = time_el.inner_text().strip()
                    timestamp = self._parse_wa_time(time_text)

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
        """Scroll up in the chat to load messages back to the `since` date.

        Uses keyboard-based scrolling (Home/PageUp) which works regardless
        of the DOM container structure.
        """
        # Click on a message row to ensure the conversation area has focus
        first_row = page.query_selector('div[role="row"]')
        if first_row:
            first_row.click()
            page.wait_for_timeout(500)
        else:
            logger.warning("No message rows found to focus for scrolling")
            return

        max_scrolls = 80
        prev_count = 0
        for i in range(max_scrolls):
            # Check the oldest visible message's timestamp
            rows = page.query_selector_all('div[role="row"]')
            if rows:
                pre_plain = rows[0].query_selector('div[data-pre-plain-text]')
                if pre_plain:
                    pre_text = pre_plain.get_attribute("data-pre-plain-text") or ""
                    ts = self._parse_pre_plain_text_timestamp(pre_text)
                    if ts and ts <= since:
                        logger.info(f"Scrolled back to {ts}, reached target {since}")
                        break

            # Check if we've stopped loading new messages (hit the top)
            current_count = len(rows)
            if i > 3 and current_count == prev_count:
                logger.info(f"No new messages loaded after scroll {i}, stopping")
                break
            prev_count = current_count

            # Scroll up using keyboard — works without knowing the container
            page.keyboard.press("PageUp")
            page.wait_for_timeout(1500)

        total = len(page.query_selector_all('div[role="row"]'))
        logger.info(f"After scrolling: {total} message rows loaded")

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
