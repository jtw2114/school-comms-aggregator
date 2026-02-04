"""Deeper probe using known user ID to find students, messages, activities."""

import json
from src.services.brightwheel_auth import BrightwheelAuth

auth = BrightwheelAuth()
auth.restore_session()

import requests
s = requests.Session()
s.cookies.update(auth.get_cookies_dict())
s.headers.update({"Accept": "application/json"})
if auth.csrf_token:
    s.headers["X-CSRF-Token"] = auth.csrf_token

BASE = "https://schools.mybrightwheel.com/api/v1"
USER_ID = "a3c3d5ed-c7f5-4d02-a8e2-2f6ec282e45d"

# Get full user profile
print("=== Full User Profile ===")
r = s.get(f"{BASE}/users/{USER_ID}")
if r.status_code == 200:
    data = r.json()
    print(json.dumps(data, indent=2, default=str)[:3000])
else:
    print(f"[{r.status_code}]")

# Try to find students/children
endpoints = [
    f"/users/{USER_ID}/students",
    f"/users/{USER_ID}/children",
    f"/guardians/{USER_ID}/students",
    f"/guardians/{USER_ID}/children",
    f"/users/{USER_ID}/managed_students",
    "/students",
    "/children",
    # Messages
    f"/users/{USER_ID}/messages",
    f"/users/{USER_ID}/conversations",
    f"/users/{USER_ID}/inbox",
    "/messages",
    "/conversations",
    "/inbox",
    # Feed
    f"/users/{USER_ID}/feed",
    f"/users/{USER_ID}/activities",
    f"/users/{USER_ID}/notifications",
]

for ep in endpoints:
    url = f"{BASE}{ep}"
    try:
        r = s.get(url, timeout=10, allow_redirects=False)
        if r.status_code == 200:
            try:
                data = r.json()
                preview = json.dumps(data, indent=2, default=str)[:800]
            except Exception:
                preview = r.text[:300]
            print(f"\n[200] {ep}")
            print(f"  {preview}")
        elif r.status_code not in (404, 301, 302):
            print(f"\n[{r.status_code}] {ep}")
    except Exception as e:
        print(f"\n[ERR] {ep}: {e}")

# Also try v2
print("\n\n=== V2 Endpoints ===")
BASE2 = "https://schools.mybrightwheel.com/api/v2"
v2_endpoints = [
    f"/users/{USER_ID}/students",
    f"/users/{USER_ID}/messages",
    f"/users/{USER_ID}/conversations",
    "/messages",
    "/conversations",
    "/feed",
    "/students",
]
for ep in v2_endpoints:
    url = f"{BASE2}{ep}"
    try:
        r = s.get(url, timeout=10, allow_redirects=False)
        if r.status_code == 200:
            try:
                data = r.json()
                preview = json.dumps(data, indent=2, default=str)[:800]
            except Exception:
                preview = r.text[:300]
            print(f"\n[200] {ep}")
            print(f"  {preview}")
        elif r.status_code not in (404, 301, 302):
            print(f"\n[{r.status_code}] {ep}")
    except Exception as e:
        print(f"\n[ERR] {ep}: {e}")

print("\n=== Done ===")
