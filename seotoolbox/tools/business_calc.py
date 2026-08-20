"""Transparent local business and SEO forecasting calculators."""

from __future__ import annotations

from . import ArgSpec, ToolSpec, register


def time_to_rank(kd: float, authority: float, age: float) -> list[dict]:
    """Estimate months to rank using 3 + KD/8 - authority/12 - min(age,120)/30, clamped to 1–24."""
    if not 0 <= kd <= 100 or not 0 <= authority <= 100 or age < 0:
        raise ValueError("kd and authority must be 0-100; age must be non-negative")
    months = max(1.0, min(24.0, 3 + kd / 8 - authority / 12 - min(age, 120) / 30))
    note = "heuristic, non-predictive estimate; not calibrated data"
    return [{"factor": "KD", "value": kd, "note": note}, {"factor": "domain authority", "value": authority, "note": note},
            {"factor": "domain age (months)", "value": age, "note": note}, {"factor": "estimated months", "value": round(months, 1), "note": note}]


_CTR = {1: .285, 2: .157, 3: .11, 4: .08, 5: .065, 6: .05, 7: .04, 8: .032, 9: .027, 10: .024}


def opportunity_cost(volume: float, cpc: float, position: int, days: int = 30) -> list[dict]:
    """Estimate missed equivalent ad value versus position one using a fixed CTR curve."""
    if volume < 0 or cpc < 0 or position < 1 or days < 0:
        raise ValueError("volume, cpc, and days must be non-negative; position must be positive")
    current_ctr = _CTR.get(position, 0.0)
    lost = max(0.0, (_CTR[1] - current_ctr) * volume * cpc * days / 30)
    return [{"metric": "position 1 CTR", "value": _CTR[1]}, {"metric": "current CTR", "value": current_ctr},
            {"metric": "period (days)", "value": days}, {"metric": "opportunity cost EUR", "value": round(lost, 2)}]


def organic_revenue(traffic: float, conversion: float, basket: float, growth: float = 0) -> list[dict]:
    """Estimate monthly, yearly, and growth-adjusted organic revenue."""
    if traffic < 0 or basket < 0 or not 0 <= conversion <= 100 or growth < -100:
        raise ValueError("traffic and basket must be non-negative, conversion must be 0-100, and growth at least -100")
    monthly = traffic * conversion / 100 * basket
    return [{"metric": "monthly revenue EUR", "value": round(monthly, 2)},
            {"metric": "annual revenue EUR", "value": round(monthly * 12, 2)},
            {"metric": f"monthly with {growth}% growth EUR", "value": round(monthly * (1 + growth / 100), 2)}]


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")


register(ToolSpec("time_to_rank", time_to_rank, "Heuristic, non-predictive estimate of time to rank — not calibrated data.", "calculators", [A("kd"), A("authority"), A("age")], "table"))
register(ToolSpec("opportunity_cost", opportunity_cost, "Estimate missed organic equivalent ad value.", "calculators", [A("volume"), A("cpc"), A("position"), A("days", False, "30")], "table"))
register(ToolSpec("organic_revenue", organic_revenue, "Estimate organic monthly and annual revenue.", "calculators", [A("traffic"), A("conversion"), A("basket"), A("growth", False, "0")], "table"))
