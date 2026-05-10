from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl


class Platform(StrEnum):
    bilibili = "bilibili"
    xiaohongshu = "xiaohongshu"
    youtube = "youtube"
    book = "book"
    manual = "manual"


class SourceRecord(BaseModel):
    url: HttpUrl | None = None
    platform: Platform
    owner: str
    title: str | None = None
    authorized: bool = False
    raw_path: Path | None = None
    metadata_path: Path | None = None
    transcript_path: Path | None = None
    download_provider: str | None = None
    fallback_used: bool = False
    download_notes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DownloadResult(BaseModel):
    title: str | None = None
    owner: str | None = None
    webpage_url: str | None = None
    raw_path: Path | None = None
    metadata_path: Path | None = None
    provider: str | None = None
    fallback_used: bool = False
    notes: list[str] = Field(default_factory=list)


class CreatorVideo(BaseModel):
    platform: Platform
    owner: str
    owner_id: str | None = None
    video_id: str | None = None
    title: str | None = None
    url: str
    published_at: datetime | None = None
    duration_seconds: int | None = None
    metrics: dict[str, int | float | str | None] = Field(default_factory=dict)
    metadata: dict[str, int | float | str | bool | None] = Field(default_factory=dict)


class CreatorVideoList(BaseModel):
    platform: Platform
    owner_query: str
    owner: str
    owner_id: str | None = None
    owner_url: str | None = None
    provider: str
    videos: list[CreatorVideo] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CreatorVideoIngestItem(BaseModel):
    url: str
    title: str | None = None
    status: str
    source_record_path: Path | None = None
    raw_path: Path | None = None
    metadata_path: Path | None = None
    error: str | None = None


class CreatorVideoIngestResult(BaseModel):
    selected: int = 0
    downloaded: int = 0
    recorded: int = 0
    skipped: int = 0
    failed: int = 0
    items: list[CreatorVideoIngestItem] = Field(default_factory=list)


class Methodology(BaseModel):
    id: str
    title: str
    owner: str
    topic: str
    source_urls: list[str] = Field(default_factory=list)
    core_ideas: list[str] = Field(default_factory=list)
    repeatable_methods: list[str] = Field(default_factory=list)
    decision_rules: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    agent_checks: list[str] = Field(default_factory=list)
    reflection_questions: list[str] = Field(default_factory=list)
