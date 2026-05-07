from __future__ import annotations

from datetime import datetime
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
    transcript_path: Path | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
