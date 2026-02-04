"""Probe Brightwheel API endpoints to discover the right ones."""

import json
from src.services.brightwheel_auth import BrightwheelAuth
from src.config.settings import BW_API_BASE

auth = BrightwheelAuth()
if not auth.restore_session():
    print("No session found - set up Brightwheel first")
    exit(1)

import requests
session = requests.Session()
session.cookies.update(auth.get_cookies_dict())
session.headers.update({"Accept": "application/json"})
if auth.csrf_token:
    session.headers["X-CSRF-Token"] = auth.csrf_token

# Try various base URLs and endpoints
bases = [
    "https://schools.mybrightwheel.com/api/v1",
    "https://schools.mybrightwheel.com/api/v2",
    "https://app.mybrightwheel.com/api/v1",
    "https://app.mybrightwheel.com/api/v2",
    "https://mybrightwheel.com/api/v1",
]

endpoints = [
    "/users/me",
    "/me",
    "/profile",
    "/messages",
    "/conversations",
    "/inbox",
    "/notifications",
    "/feed",
    "/guardians",
    "/students",
    "/children",
]

print("=== Probing Brightwheel API ===\n")

for base in bases:
    for ep in endpoints:
        url = f"{base}{ep}"
        try:
            resp = session.get(url, timeout=10, allow_redirects=False)
            status = resp.status_code
            if status in (200, 201):
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]
                preview = json.dumps(data, indent=2, default=str)[:500]
                print(f"[{status}] {url}")
                print(f"  {preview}\n")
            elif status in (301, 302):
                print(f"[{status}] {url} -> {resp.headers.get('Location', '?')}")
            elif status != 404:
                print(f"[{status}] {url}")
        except Exception as e:
            print(f"[ERR] {url}: {e}")

print("\n=== Done ===")
