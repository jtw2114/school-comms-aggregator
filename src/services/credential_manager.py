"""Secure credential storage using Windows Credential Locker via keyring."""

import json

import keyring

from src.config.settings import KEYRING_SERVICE

# Key names within the keyring service
_BW_EMAIL_KEY = "brightwheel_email"
_BW_PASSWORD_KEY = "brightwheel_password"
_CLAUDE_API_KEY = "claude_api_key"


def get_bw_email() -> str | None:
    return keyring.get_password(KEYRING_SERVICE, _BW_EMAIL_KEY)


def set_bw_email(email: str):
    keyring.set_password(KEYRING_SERVICE, _BW_EMAIL_KEY, email)


def get_bw_password() -> str | None:
    return keyring.get_password(KEYRING_SERVICE, _BW_PASSWORD_KEY)


def set_bw_password(password: str):
    keyring.set_password(KEYRING_SERVICE, _BW_PASSWORD_KEY, password)


def get_claude_api_key() -> str | None:
    return keyring.get_password(KEYRING_SERVICE, _CLAUDE_API_KEY)


def set_claude_api_key(api_key: str):
    keyring.set_password(KEYRING_SERVICE, _CLAUDE_API_KEY, api_key)


def delete_bw_credentials():
    try:
        keyring.delete_password(KEYRING_SERVICE, _BW_EMAIL_KEY)
    except keyring.errors.PasswordDeleteError:
        pass
    try:
        keyring.delete_password(KEYRING_SERVICE, _BW_PASSWORD_KEY)
    except keyring.errors.PasswordDeleteError:
        pass


def delete_claude_api_key():
    try:
        keyring.delete_password(KEYRING_SERVICE, _CLAUDE_API_KEY)
    except keyring.errors.PasswordDeleteError:
        pass


def get_wa_groups() -> list[str]:
    """Get configured WhatsApp group names."""
    raw = keyring.get_password(KEYRING_SERVICE, "whatsapp_groups")
    return json.loads(raw) if raw else []


def set_wa_groups(groups: list[str]):
    """Save configured WhatsApp group names."""
    keyring.set_password(KEYRING_SERVICE, "whatsapp_groups", json.dumps(groups))
