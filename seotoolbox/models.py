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


@dataclass
class RankPosition(SerializableModel):
    keyword: str
    position: int | None = None
    url: str | None = None
    se_type: str | None = None
    volume: int | None = None
    difficulty: float | None = None


@dataclass
class RankHistory(SerializableModel):
    keyword: str
    date: str | None = None
    position: int | None = None


@dataclass
class SerpCompetitor(SerializableModel):
    domain: str
    avg_position: float | None = None
    median_position: float | None = None
    keywords_count: int | None = None
    visibility: float | None = None


@dataclass
class AiMention(SerializableModel):
    keyword: str
    engine: str | None = None
    domain: str | None = None
    rank: int | None = None
    mention_count: int | None = None


@dataclass
class AiTopPage(SerializableModel):
    keyword: str
    engine: str | None = None
    page_url: str | None = None
    rank: int | None = None
    mention_count: int | None = None


@dataclass
class BacklinkSummary(SerializableModel):
    backlinks: int | None = None
    referring_domains: int | None = None
    rank: int | None = None
    spam_score: float | None = None
    broken_backlinks: int | None = None
    crawled_pages: int | None = None
    first_seen: str | None = None
    lost_date: str | None = None
    external_links_count: int | None = None
    internal_links_count: int | None = None
    referring_pages: int | None = None


@dataclass
class Backlink(SerializableModel):
    url_from: str | None = None
    url_to: str | None = None
    anchor: str | None = None
    domain_from: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    is_new: bool | None = None
    is_lost: bool | None = None
    spam_score: float | None = None


@dataclass
class ReferringDomain(SerializableModel):
    domain: str
    referring_links: int | None = None
    external_links: int | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    rank: int | None = None
    spam_score: float | None = None


@dataclass
class Anchor(SerializableModel):
    anchor: str
    referring_domains: int | None = None
    backlinks: int | None = None
    external_links: int | None = None


@dataclass
class NewLost(SerializableModel):
    date: str
    new_backlinks: int | None = None
    lost_backlinks: int | None = None
    new_referring_domains: int | None = None
    lost_referring_domains: int | None = None


@dataclass
class BacklinkCompetitor(SerializableModel):
    domain: str
    backlinks: int | None = None
    referring_domains: int | None = None
    rank: int | None = None


@dataclass
class SerpResult(SerializableModel):
    rank: int | None = None
    url: str | None = None
    domain: str | None = None
    title: str | None = None
    description: str | None = None
    position_type: str | None = None


@dataclass
class SerpFeatures(SerializableModel):
    keyword: str
    features: list[str] | None = None
