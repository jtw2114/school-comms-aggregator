"""Brightwheel API client using extracted session cookies."""

import json
import logging
from datetime import datetime

import requests

from src.config.settings import BW_API_BASE, BW_PAGE_SIZE
from src.services.brightwheel_auth import BrightwheelAuth
from src.utils.date_utils import parse_timestamp

logger = logging.getLogger(__name__)


class BrightwheelService:
    """Fetches data from Brightwheel's internal API."""

    def __init__(self, auth: BrightwheelAuth):
        self._auth = auth
        self._session = requests.Session()
        self._session.cookies.update(auth.get_cookies_dict())
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        if auth.csrf_token:
            self._session.headers["X-CSRF-Token"] = auth.csrf_token

    def get_current_user(self) -> dict:
        """GET /api/v1/users/me -> user info."""
        resp = self._session.get(f"{BW_API_BASE}/users/me")
        resp.raise_for_status()
        return resp.json()

    def get_students(self, guardian_id: str) -> list[dict]:
        """GET /api/v1/guardians/{id}/students -> list of student entries.

        Returns list of dicts, each with a 'student' key containing student info.
        """
        resp = self._session.get(f"{BW_API_BASE}/guardians/{guardian_id}/students")
        resp.raise_for_status()
        data = resp.json()
        return data.get("students", [])

    def get_activities(
        self, student_id: str, page: int = 1, page_size: int = BW_PAGE_SIZE
    ) -> tuple[list[dict], bool]:
        """Fetch paginated activity feed for a student.

        Returns (activities, has_more_pages).
        """
        resp = self._session.get(
            f"{BW_API_BASE}/students/{student_id}/activities",
            params={"page": page, "per_page": page_size},
        )
        resp.raise_for_status()
        data = resp.json()

        activities = data.get("activities", [])
        has_more = len(activities) >= page_size
        return activities, has_more

    def get_messages(
        self, student_id: str, page: int = 1, page_size: int = 25
    ) -> tuple[list[dict], bool]:
        """Fetch paginated messages for a student.

        Returns (messages, has_more).
        """
        resp = self._session.get(
            f"{BW_API_BASE}/students/{student_id}/messages",
            params={"page": page, "page_size": page_size},
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        has_more = data.get("has_more", False)
        return results, has_more

    def fetch_all_activities(
        self, student_id: str, since: datetime | None = None, max_pages: int = 20
    ) -> list[dict]:
        """Fetch all activities for a student, optionally since a given date."""
        all_activities = []
        page = 1

        while page <= max_pages:
            activities, has_more = self.get_activities(student_id, page=page)
            if not activities:
                break

            for activity in activities:
                created = activity.get("created_at") or activity.get("event_date")
                if since and created:
                    try:
                        ts = parse_timestamp(created)
                        if ts < since:
                            return all_activities
                    except (ValueError, TypeError):
                        pass
                all_activities.append(activity)

            if not has_more:
                break
            page += 1

        return all_activities

    def fetch_all_messages(
        self, student_id: str, since: datetime | None = None, max_pages: int = 20
    ) -> list[dict]:
        """Fetch all messages for a student, optionally since a given date."""
        all_messages = []
        page = 1

        while page <= max_pages:
            results, has_more = self.get_messages(student_id, page=page)
            if not results:
                break

            for result in results:
                msg = result.get("message", result)
                created = msg.get("created_at") or msg.get("date")
                if since and created:
                    try:
                        ts = parse_timestamp(created)
                        if ts < since:
                            return all_messages
                    except (ValueError, TypeError):
                        pass
                all_messages.append(result)

            if not has_more:
                break
            page += 1

        return all_messages

    @staticmethod
    def parse_activity(activity: dict, student_name: str = "") -> dict:
        """Parse a Brightwheel activity into a normalized dict."""
        action_type = activity.get("action_type", activity.get("type", "activity"))

        # Actor name from nested object
        actor = activity.get("actor", {})
        if isinstance(actor, dict):
            actor_name = f"{actor.get('first_name', '')} {actor.get('last_name', '')}".strip()
        else:
            actor_name = str(actor)

        # Room name from nested object
        room = activity.get("room", {})
        room_name = room.get("name", "") if isinstance(room, dict) else ""

        # Build title
        title = action_type.replace("_", " ").replace("ac ", "").title()
        if student_name:
            title = f"{student_name}: {title}"

        # Extract text body
        body_parts = []
        if activity.get("note"):
            body_parts.append(activity["note"])
        # Include details_blob info
        details = activity.get("details_blob", {})
        if isinstance(details, dict):
            if details.get("food_type"):
                body_parts.append(f"Food: {details['food_type']}")
            if details.get("amount_type"):
                body_parts.append(f"Amount: {details['amount_type']}")

        # Extract photos from media
        photos = []
        media = activity.get("media")
        if isinstance(media, list):
            for m in media:
                if isinstance(m, dict) and m.get("image_url"):
                    photos.append(m["image_url"])
        elif isinstance(media, dict) and media.get("image_url"):
            photos.append(media["image_url"])

        created = activity.get("created_at") or activity.get("event_date", "")

        return {
            "source_id": f"bw_act_{activity.get('object_id', '')}",
            "timestamp": created,
            "title": title,
            "sender": actor_name,
            "body_plain": "\n".join(body_parts) if body_parts else "",
            "student_name": student_name,
            "room": room_name,
            "action_type": action_type,
            "details": json.dumps(activity, default=str),
            "photos": photos,
        }

    @staticmethod
    def parse_message(result: dict, student_name: str = "") -> dict:
        """Parse a Brightwheel message into a normalized dict."""
        msg = result.get("message", result)

        # Sender info
        sender = msg.get("sender", {})
        if isinstance(sender, dict):
            sender_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
        else:
            sender_name = str(sender) if sender else ""

        body = msg.get("body", "")
        msg_type = msg.get("type", "message")

        title = f"Message: {body[:80]}..." if len(body) > 80 else f"Message: {body}" if body else "Message"
        if student_name:
            title = f"{student_name}: {title}"

        # Extract attachments/media from message
        photos = []
        attachments = msg.get("attachments", [])
        if isinstance(attachments, list):
            for att in attachments:
                if isinstance(att, dict):
                    url = att.get("image_url") or att.get("url", "")
                    if url:
                        photos.append(url)

        created = msg.get("created_at", "")

        return {
            "source_id": f"bw_msg_{msg.get('object_id', '')}",
            "timestamp": created,
            "title": title,
            "sender": sender_name,
            "body_plain": body,
            "student_name": student_name,
            "room": "",
            "action_type": msg_type,
            "details": json.dumps(result, default=str),
            "photos": photos,
        }
