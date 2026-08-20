"""Local business and technical SEO calculators."""

from __future__ import annotations

import math

from . import ArgSpec, ToolSpec, register


def _positive(value: float, name: str, allow_zero: bool = False) -> None:
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"{name} must be {'zero or greater' if allow_zero else 'greater than zero'}")


def roi_seo(budget: float, basket: float, margin: float, conversion: float, months: int = 12, traffic: float = 1000, growth: float = 5) -> list[dict]:
    """Project cumulative SEO return using explicit initial traffic and monthly growth."""
    for value, name in ((budget, "budget"), (basket, "basket"), (traffic, "traffic")):
        _positive(value, name)
    if not 0 <= margin <= 100 or not 0 <= conversion <= 100:
        raise ValueError("margin and conversion must be percentages between 0 and 100")
    if not 1 <= months <= 24:
        raise ValueError("months must be between 1 and 24")
    rows, cumulative_profit, cumulative_cost = [], 0.0, 0.0
    for month in range(1, months + 1):
        month_traffic = traffic * (1 + growth / 100) ** (month - 1)
        leads = month_traffic * conversion / 100
        revenue = leads * basket
        cumulative_profit += revenue * margin / 100
        cumulative_cost += budget
        roi = (cumulative_profit - cumulative_cost) / cumulative_cost * 100
        rows.append({"month": month, "traffic": round(month_traffic), "leads": round(leads, 2), "revenue": round(revenue, 2), "cost": round(cumulative_cost, 2), "cumulative_roi_pct": round(roi, 2)})
    return rows


def traffic_projection(volume: float, ctr: float, click_rate: float = 100, growth: float = 0) -> list[dict]:
    """Estimate traffic now, after six months, and after twelve months."""
    _positive(volume, "volume", True)
    if not 0 <= ctr <= 100 or not 0 <= click_rate <= 100:
        raise ValueError("ctr and click_rate must be between 0 and 100")
    base = volume * ctr / 100 * click_rate / 100
    return [{"period_months": month, "estimated_traffic": round(base * (1 + growth / 100) ** month, 2)} for month in (0, 6, 12)]


def position_value(volume: float, cpc: float, current_ctr: float, target_ctr: float) -> str:
    """Calculate the monthly paid-search value of an organic CTR improvement."""
    gain = volume * (target_ctr - current_ctr) / 100
    return f"Monthly click gain: {gain:.2f}; monthly value: €{gain * cpc:.2f}"


_CTR = {
    "desktop": [28.5, 15.7, 11.0, 8.0, 7.2, 5.1, 4.0, 3.2, 2.8, 2.5, 2.2, 2.0, 1.8, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0],
    "mobile": [24.0, 14.0, 10.0, 7.5, 6.0, 4.8, 3.8, 3.1, 2.6, 2.2, 2.0, 1.8, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 0.9],
}


def ctr_curve(position: int = 0, device: str = "both") -> list[dict]:
    """Return a documented reference CTR curve for positions 1 through 20."""
    if position and not 1 <= position <= 20:
        raise ValueError("position must be 0 or between 1 and 20")
    if device not in {"desktop", "mobile", "both"}:
        raise ValueError("device must be desktop, mobile, or both")
    positions = [position] if position else range(1, 21)
    return [{"position": pos, **({"desktop_ctr_pct": _CTR["desktop"][pos - 1]} if device in {"desktop", "both"} else {}), **({"mobile_ctr_pct": _CTR["mobile"][pos - 1]} if device in {"mobile", "both"} else {})} for pos in positions]


def ads_equivalent(clicks: float, cpc: float) -> str:
    """Calculate the Ads budget equivalent for a click target."""
    return f"Equivalent monthly Ads budget: €{clicks * cpc:.2f}"


def conversion_rate(visits: int, conversions: int) -> str:
    """Calculate conversion rate and its 95% Wilson score interval."""
    if visits <= 0 or not 0 <= conversions <= visits:
        raise ValueError("visits must be positive and conversions between 0 and visits")
    p, z = conversions / visits, 1.96
    denominator = 1 + z * z / visits
    centre = (p + z * z / (2 * visits)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * visits)) / visits) / denominator
    return f"Conversion rate: {p * 100:.2f}% (95% CI: {(centre-spread)*100:.2f}%–{(centre+spread)*100:.2f}%)"


def implicit_cpc(cost: float, clicks: float) -> str:
    """Calculate organic acquisition cost per click."""
    _positive(clicks, "clicks")
    return f"Implicit CPC: €{cost / clicks:.2f}"


def cac_ltv(cost: float, customers: int, ltv: float, months: int = 1) -> str:
    """Calculate CAC, LTV, and the LTV-to-CAC ratio over a period."""
    _positive(customers, "customers")
    _positive(months, "months")
    cac = cost * months / customers
    return f"CAC: €{cac:.2f}; LTV: €{ltv:.2f}; LTV/CAC ratio: {ltv / cac:.2f}" if cac else "CAC: €0.00; LTV/CAC ratio: infinite"


def crawl_time(pages: int, urls_per_second: float, daily_budget_pct: float = 100) -> str:
    """Estimate crawl duration and calendar days at a daily budget percentage."""
    _positive(urls_per_second, "urls_per_second")
    if not 0 < daily_budget_pct <= 100:
        raise ValueError("daily_budget_pct must be between 0 and 100")
    seconds = pages / urls_per_second
    days = seconds / 86400 / (daily_budget_pct / 100)
    return f"Duration: {seconds:.2f} s ({seconds/60:.2f} min, {seconds/3600:.2f} h); at {daily_budget_pct:g}% daily budget: {days:.3f} days"


def sitemap_split(urls: int) -> str:
    """Calculate sitemap files required under the 50,000 URL limit."""
    if urls < 0:
        raise ValueError("urls must be zero or greater")
    files = math.ceil(urls / 50000) if urls else 0
    return f"Sitemap files: {files}; sitemap index recommended: {'yes' if files > 1 else 'no'}"


def eeat_score(author: bool = False, bio: bool = False, sources: bool = False, mentions: bool = False, evidence: bool = False, dates: bool = False, faq: bool = False, reviews: bool = False, about: bool = False, contact: bool = False) -> str:
    """Score ten transparent E-E-A-T checklist signals equally."""
    score = sum((author, bio, sources, mentions, evidence, dates, faq, reviews, about, contact)) * 10
    verdict = "strong" if score >= 80 else "moderate" if score >= 50 else "weak"
    return f"E-E-A-T score: {score}/100; verdict: {verdict}"


def backlink_value(authority: float, referral_traffic: float, cpc: float) -> str:
    """Estimate monthly link value: traffic value multiplied by 0.5–1.5 authority factor."""
    if not 0 <= authority <= 100:
        raise ValueError("authority must be between 0 and 100")
    # Authority factor ranges linearly from 0.5 at zero to 1.5 at 100.
    value = referral_traffic * cpc * (0.5 + authority / 100)
    return f"Estimated monthly backlink value: €{value:.2f}"


def content_cost(words: int, rate: float, articles: int = 1) -> str:
    """Calculate per-article and monthly content production costs."""
    article = words / 1000 * rate
    return f"Article cost: €{article:.2f}; monthly cost ({articles} article(s)): €{article * articles:.2f}"


def A(name: str, required: bool = True, default: str | None = None, help: str = "", flag: bool = False) -> ArgSpec:
    return ArgSpec(name, required, default, help or name.replace("_", " ").capitalize() + ".", flag)


register(ToolSpec("roi_seo", roi_seo, "Project cumulative SEO ROI by month.", "calculators", [A("budget"), A("basket"), A("margin"), A("conversion"), A("months", False, "12"), A("traffic", False, "1000"), A("growth", False, "5")], "table"))
register(ToolSpec("traffic_projection", traffic_projection, "Project estimated organic traffic over 6 and 12 months.", "calculators", [A("volume"), A("ctr"), A("click_rate", False, "100"), A("growth", False, "0")], "table"))
register(ToolSpec("position_value", position_value, "Estimate the monetary gain from a better CTR position.", "calculators", [A("volume"), A("cpc"), A("current_ctr"), A("target_ctr")]))
register(ToolSpec("ctr_curve", ctr_curve, "Show desktop and mobile CTR reference curves.", "calculators", [A("position", False, "0"), A("device", False, "both")], "table"))
register(ToolSpec("ads_equivalent", ads_equivalent, "Calculate the Ads budget equivalent of organic clicks.", "calculators", [A("clicks"), A("cpc")]))
register(ToolSpec("conversion_rate", conversion_rate, "Calculate conversion rate and a Wilson 95% interval.", "calculators", [A("visits"), A("conversions")]))
register(ToolSpec("implicit_cpc", implicit_cpc, "Calculate the implicit cost of an organic click.", "calculators", [A("cost"), A("clicks")]))
register(ToolSpec("cac_ltv", cac_ltv, "Calculate customer acquisition cost and LTV ratio.", "calculators", [A("cost"), A("customers"), A("ltv"), A("months", False, "1")]))
register(ToolSpec("crawl_time", crawl_time, "Estimate crawl duration and calendar time.", "calculators", [A("pages"), A("urls_per_second"), A("daily_budget_pct", False, "100")]))
register(ToolSpec("sitemap_split", sitemap_split, "Calculate sitemap splitting requirements.", "calculators", [A("urls")]))
register(ToolSpec("eeat_score", eeat_score, "Score ten E-E-A-T checklist signals.", "calculators", [A(n, False, None, f"Set the {n} signal.", True) for n in ("author", "bio", "sources", "mentions", "evidence", "dates", "faq", "reviews", "about", "contact")]))
register(ToolSpec("backlink_value", backlink_value, "Estimate a backlink's monthly market value.", "calculators", [A("authority"), A("referral_traffic"), A("cpc")]))
register(ToolSpec("content_cost", content_cost, "Calculate article and monthly content costs.", "calculators", [A("words"), A("rate"), A("articles", False, "1")]))
