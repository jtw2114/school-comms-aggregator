"""Database models for communications, attachments, sync state, and daily summaries."""

import json
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class CommunicationItem(Base):
    __tablename__ = "communication_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    sender: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    body_plain: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # "gmail" or "brightwheel"
    source_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    # Gmail-specific
    gmail_thread_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gmail_label_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    gmail_snippet: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Brightwheel-specific
    bw_student_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bw_room: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bw_action_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bw_details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="communication", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_comm_source_timestamp", "source", "timestamp"),
    )

    @property
    def gmail_label_list(self) -> list[str]:
        if self.gmail_label_ids:
            return json.loads(self.gmail_label_ids)
        return []

    @property
    def bw_details_dict(self) -> dict:
        if self.bw_details:
            return json.loads(self.bw_details)
        return {}


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    communication_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("communication_items.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remote_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    communication: Mapped["CommunicationItem"] = relationship(back_populates="attachments")


class SyncState(Base):
    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)  # "gmail" or "brightwheel"
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    page_cursor: Mapped[str | None] = mapped_column(String(500), nullable=True)  # page token / cursor
    extra: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON for any extra state


class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)  # YYYY-MM-DD
    key_dates: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    deadlines: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    curriculum_updates: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    action_items: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    raw_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_item_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list of IDs
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def key_dates_list(self) -> list:
        return json.loads(self.key_dates) if self.key_dates else []

    @property
    def deadlines_list(self) -> list:
        return json.loads(self.deadlines) if self.deadlines else []

    @property
    def curriculum_updates_list(self) -> list:
        return json.loads(self.curriculum_updates) if self.curriculum_updates else []

    @property
    def action_items_list(self) -> list:
        return json.loads(self.action_items) if self.action_items else []

    @property
    def source_item_id_list(self) -> list[int]:
        return json.loads(self.source_item_ids) if self.source_item_ids else []


class ChecklistItem(Base):
    """Persistent checklist item for action items and key dates."""

    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "action_items" or "key_dates"
    item_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
