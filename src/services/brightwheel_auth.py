"""Brightwheel authentication via Playwright: login, 2FA handling, cookie extraction."""

import json
import logging
from pathlib import Path

from src.config.settings import BW_BASE_URL, BW_LOGIN_TIMEOUT_MS, BW_SESSION_PATH

logger = logging.getLogger(__name__)


class BrightwheelAuth:
    """Handles Brightwheel login via Playwright and session persistence."""

    def __init__(self):
        self._cookies: dict[str, str] = {}
        self._csrf_token: str | None = None

    @property
    def session_cookie(self) -> str | None:
        return self._cookies.get("_brightwheel_v2")

    @property
    def csrf_token(self) -> str | None:
        return self._csrf_token

    @property
    def has_valid_session(self) -> bool:
        return bool(self.session_cookie)

    def login(self, email: str, password: str, headless: bool = False) -> bool:
        """Perform login via Playwright. Uses headed mode by default for 2FA.

        Args:
            email: Brightwheel account email.
            password: Brightwheel account password.
            headless: If False, shows browser so user can handle 2FA.

        Returns True on success.
        """
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # Try restoring saved session first
            browser_args = {}
            if BW_SESSION_PATH.exists():
                browser_args["storage_state"] = str(BW_SESSION_PATH)
                logger.info("Restoring saved Playwright session")

            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(**browser_args)
            page = context.new_page()

            try:
                # Navigate to login
                page.goto(f"{BW_BASE_URL}/sign-in", wait_until="networkidle")

                # Check if already logged in (session restored)
                if "/sign-in" not in page.url:
                    logger.info("Session restored, already logged in")
                    self._extract_cookies(context)
                    self._save_session(context)
                    return True

                # Fill login form
                page.fill('input[name="user[email]"]', email)
                page.fill('input[name="user[password]"]', password)
                page.click('button[type="submit"]')

                # Wait for navigation away from sign-in (handles 2FA wait)
                page.wait_for_url(
                    lambda url: "/sign-in" not in url,
                    timeout=BW_LOGIN_TIMEOUT_MS,
                )

                logger.info("Login successful, extracting cookies")
                self._extract_cookies(context)
                self._save_session(context)
                return True

            except Exception as e:
                logger.error(f"Brightwheel login failed: {e}")
                raise
            finally:
                browser.close()

    def restore_session(self) -> bool:
        """Try to restore session from saved storage state without opening browser."""
        if not BW_SESSION_PATH.exists():
            return False

        try:
            with open(BW_SESSION_PATH, "r") as f:
                state = json.load(f)

            for cookie in state.get("cookies", []):
                self._cookies[cookie["name"]] = cookie["value"]
                if cookie["name"] == "csrf-token":
                    self._csrf_token = cookie["value"]

            return self.has_valid_session
        except Exception as e:
            logger.warning(f"Failed to restore session: {e}")
            return False

    def get_request_headers(self) -> dict[str, str]:
        """Return headers needed for direct API requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.session_cookie:
            headers["Cookie"] = f"_brightwheel_v2={self.session_cookie}"
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token
        return headers

    def get_cookies_dict(self) -> dict[str, str]:
        """Return cookies for use with requests library."""
        return dict(self._cookies)

    def set_manual_cookie(self, cookie_value: str):
        """Manual cookie paste fallback."""
        self._cookies["_brightwheel_v2"] = cookie_value

    def _extract_cookies(self, context):
        """Extract cookies from the Playwright browser context."""
        cookies = context.cookies()
        for cookie in cookies:
            self._cookies[cookie["name"]] = cookie["value"]
            if cookie["name"] == "csrf-token":
                self._csrf_token = cookie["value"]

    def _save_session(self, context):
        """Save Playwright storage state for session reuse."""
        try:
            context.storage_state(path=str(BW_SESSION_PATH))
            logger.info(f"Session saved to {BW_SESSION_PATH}")
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")
