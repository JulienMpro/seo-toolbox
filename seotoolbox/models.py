"""Data models returned by SEO Toolbox operations."""

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
    referring_links_types: dict[str, int] | None = None
    referring_pages_nofollow: int | None = None


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


@dataclass
class CrawlResult(SerializableModel):
    url: str
    status: int | None = None
    redirect_url: str | None = None
    title: str | None = None
    meta_description: str | None = None
    h1: str | None = None
    canonical: str | None = None
    noindex: bool = False
    content_length: int | None = None
    content_type: str | None = None


@dataclass
class Issue(SerializableModel):
    url: str
    type: str
    severity: str
    message: str


@dataclass
class AuditReport(SerializableModel):
    total_urls: int
    issues: list[Issue]
    stats: dict[str, Any]


@dataclass
class CruxMetric(SerializableModel):
    url: str
    overall_category: str | None = None
    lcp: dict[str, Any] | None = None
    cls: dict[str, Any] | None = None
    inp: dict[str, Any] | None = None
    performance_score: int | None = None


@dataclass
class GscRow(SerializableModel):
    keys: list[str]
    clicks: float | None = None
    impressions: float | None = None
    ctr: float | None = None
    position: float | None = None


@dataclass
class Ga4Row(SerializableModel):
    dimensions: list[str]
    metrics: list[float]


@dataclass
class LocalListing(SerializableModel):
    title: str | None = None
    address: str | None = None
    phone: str | None = None
    category: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    place_id: str | None = None
    lat: float | None = None
    lng: float | None = None


@dataclass
class LocalRank(SerializableModel):
    keyword: str
    city: str
    rank: int | None = None
    title: str | None = None
    address: str | None = None
    rating: float | None = None
    reviews_count: int | None = None


@dataclass
class LogEntry(SerializableModel):
    ip: str
    date: str
    method: str
    path: str
    status: int
    ua: str


@dataclass
class LogReport(SerializableModel):
    entries_count: int
    status_stats: dict[int, int]
    top_urls: list[tuple[str, int]]
    top_ips: list[tuple[str, int]]
    bot_hits: list[tuple[str, int]]
    problem_urls: list[tuple[int, str, int]]


@dataclass
class MonitorChange(SerializableModel):
    url: str
    field: str
    old_value: Any = None
    new_value: Any = None


@dataclass
class MonitorReport(SerializableModel):
    changes: list[MonitorChange]
    added: list[str]
    removed: list[str]
    checked: int


@dataclass
class TermFreq(SerializableModel):
    term: str
    frequency: int


@dataclass
class ContentScore(SerializableModel):
    url: str
    score: int
    checks: list[tuple[str, bool, int]]
