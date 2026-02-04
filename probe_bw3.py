"""Probe activities and messages for known students."""

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

# First get full student list
r = s.get(f"{BASE}/guardians/{USER_ID}/students")
students_data = r.json()
print(f"=== {students_data['count']} Students ===")
for entry in students_data["students"]:
    st = entry["student"]
    print(f"  {st['first_name']} {st['last_name']} - ID: {st['object_id']}")

# Try activities for first student
first_student_id = students_data["students"][0]["student"]["object_id"]
print(f"\n=== Activities for {students_data['students'][0]['student']['first_name']} ===")
r = s.get(f"{BASE}/students/{first_student_id}/activities", params={"page": 1, "per_page": 5})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
    print(json.dumps(data, indent=2, default=str)[:3000])

# Try messages endpoints with school IDs
school_ids = ["e5c26129-81e0-4709-9907-3816f1b03b61", "77df3db9-4874-44cb-9226-f2ba8c0b8c79"]
msg_endpoints = [
    "/messages",
    "/conversations",
    "/inbox",
    "/messaging/threads",
    "/messaging/conversations",
]

print("\n\n=== Message Endpoints ===")
for school_id in school_ids:
    print(f"\n--- School: {school_id} ---")
    for ep in msg_endpoints:
        for url in [
            f"{BASE}/schools/{school_id}{ep}",
            f"{BASE}{ep}?school_id={school_id}",
        ]:
            try:
                r = s.get(url, timeout=10, allow_redirects=False)
                if r.status_code == 200:
                    preview = json.dumps(r.json(), indent=2, default=str)[:500]
                    print(f"\n[200] {url}")
                    print(f"  {preview}")
                elif r.status_code not in (404, 301, 302):
                    print(f"[{r.status_code}] {url}")
            except Exception as e:
                print(f"[ERR] {url}: {e}")

# Also try student-level messages
print("\n\n=== Student Message Endpoints ===")
for entry in students_data["students"]:
    st = entry["student"]
    sid = st["object_id"]
    print(f"\n--- {st['first_name']} ({sid}) ---")
    for ep in ["/messages", "/conversations", "/inbox", "/feed"]:
        url = f"{BASE}/students/{sid}{ep}"
        try:
            r = s.get(url, timeout=10, allow_redirects=False)
            if r.status_code == 200:
                preview = json.dumps(r.json(), indent=2, default=str)[:500]
                print(f"[200] {ep}: {preview}")
            elif r.status_code not in (404, 301, 302):
                print(f"[{r.status_code}] {ep}")
        except Exception as e:
            print(f"[ERR] {ep}: {e}")

print("\n=== Done ===")
