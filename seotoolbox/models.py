"""Data models returned by keyword research operations."""

from dataclasses import asdict, dataclass
from typing import Any


class SerializableModel:
    """Provide a predictable dictionary representation for CLI output."""

    def to_dict(self) -> dict[str, Any]:
        """Return all dataclass fields as a dictionary."""
        return asdict(self)  # type: ignore[arg-type]


@dataclass
class KeywordIdea(SerializableModel):
    keyword: str
    volume: int | None = None
    difficulty: float | None = None
    cpc: float | None = None
    competition: float | None = None
    search_intent: str | None = None
    serp_features: list[str] | None = None


@dataclass
class KeywordOverview(SerializableModel):
    keyword: str
    volume: int | None = None
    cpc: float | None = None
    competition: float | None = None
    difficulty: float | None = None
    serp_features: list[str] | None = None
    search_intent: str | None = None


@dataclass
class IntentInfo(SerializableModel):
    keyword: str
    intent: str | None = None


@dataclass
class KeywordRanked(SerializableModel):
    keyword: str
    position: int | None = None
    volume: int | None = None
    difficulty: float | None = None
    cpc: float | None = None
    url: str | None = None
    search_intent: str | None = None
