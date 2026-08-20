"""Schema.org JSON-LD generators, validation, and extraction."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser

import httpx

from . import ArgSpec, ToolSpec, register
from .generators import _breadcrumbs, _items


def _jsonld(type_name: str, **fields: object) -> str:
    """Serialize a compact Schema.org object with empty fields omitted."""
    data = {"@context": "https://schema.org", "@type": type_name}
    data.update({key: value for key, value in fields.items() if value not in (None, "", [])})
    return json.dumps(data, ensure_ascii=False, indent=2)


def jsonld_article(headline: str, author: str, date_published: str, date_modified: str = "", image: str = "", publisher: str = "") -> str:
    """Generate Article JSON-LD."""
    return _jsonld("Article", headline=headline, author={"@type": "Person", "name": author}, datePublished=date_published, dateModified=date_modified, image=image, publisher={"@type": "Organization", "name": publisher} if publisher else None)


def jsonld_faq(qa: str) -> str:
    """Generate FAQPage JSON-LD from question/answer lines."""
    entities = []
    for line in qa.splitlines() or [qa]:
        question, separator, answer = line.partition("|")
        if line.strip() and (not separator or not question.strip() or not answer.strip()):
            raise ValueError("qa must use Question|Answer, one pair per line")
        if line.strip():
            entities.append({"@type": "Question", "name": question.strip(), "acceptedAnswer": {"@type": "Answer", "text": answer.strip()}})
    if not entities:
        raise ValueError("qa must contain at least one question and answer")
    return _jsonld("FAQPage", mainEntity=entities)


def jsonld_localbusiness(name: str, address: str, phone: str = "", opening_hours: str = "", geo: str = "", price_range: str = "", url: str = "") -> str:
    """Generate LocalBusiness JSON-LD."""
    geo_value = None
    if geo:
        latitude, separator, longitude = geo.partition(",")
        if not separator:
            raise ValueError("geo must use latitude,longitude")
        geo_value = {"@type": "GeoCoordinates", "latitude": latitude.strip(), "longitude": longitude.strip()}
    return _jsonld("LocalBusiness", name=name, address={"@type": "PostalAddress", "streetAddress": address}, telephone=phone, openingHours=_items(opening_hours), geo=geo_value, priceRange=price_range, url=url)


def jsonld_product(name: str, description: str = "", sku: str = "", price: float = 0, currency: str = "EUR", availability: str = "InStock", brand: str = "", rating_value: float = 0, review_count: int = 0) -> str:
    """Generate Product JSON-LD with Offer and optional AggregateRating."""
    if price < 0:
        raise ValueError("price must be non-negative")
    if bool(rating_value) != bool(review_count):
        raise ValueError("rating_value and review_count must be provided together")
    if rating_value and not 0 < rating_value <= 5:
        raise ValueError("rating_value must be between 0 and 5")
    if review_count < 0:
        raise ValueError("review_count must be non-negative")
    offer = {"@type": "Offer", "price": price, "priceCurrency": currency, "availability": availability if availability.startswith("http") else f"https://schema.org/{availability}"}
    rating = {"@type": "AggregateRating", "ratingValue": rating_value, "reviewCount": review_count} if rating_value or review_count else None
    return _jsonld("Product", name=name, description=description, sku=sku, brand={"@type": "Brand", "name": brand} if brand else None, offers=offer, aggregateRating=rating)


def jsonld_breadcrumb(paths: str) -> str:
    """Generate BreadcrumbList JSON-LD."""
    return _jsonld("BreadcrumbList", itemListElement=_breadcrumbs(paths))


def jsonld_review(item_reviewed: str, author: str, rating_value: float, review_body: str = "", date_published: str = "") -> str:
    """Generate Review JSON-LD."""
    if not 1 <= rating_value <= 5:
        raise ValueError("rating_value must be between 1 and 5")
    return _jsonld("Review", itemReviewed={"@type": "Thing", "name": item_reviewed}, author={"@type": "Person", "name": author}, reviewRating={"@type": "Rating", "ratingValue": rating_value}, reviewBody=review_body, datePublished=date_published)


def jsonld_event(name: str, start_date: str, end_date: str = "", location_name: str = "", location_address: str = "", description: str = "", offers_price: float = 0, currency: str = "EUR") -> str:
    """Generate Event JSON-LD."""
    if offers_price < 0:
        raise ValueError("offers_price must be non-negative")
    location = {"@type": "Place", "name": location_name, "address": location_address} if location_name or location_address else None
    offers = {"@type": "Offer", "price": offers_price, "priceCurrency": currency} if offers_price else None
    return _jsonld("Event", name=name, startDate=start_date, endDate=end_date, location=location, description=description, offers=offers)


def jsonld_organization(name: str, url: str = "", logo: str = "", same_as: str = "") -> str:
    """Generate Organization JSON-LD."""
    return _jsonld("Organization", name=name, url=url, logo=logo, sameAs=_items(same_as))


def jsonld_howto(name: str, steps: str, total_time: str = "", tool: str = "") -> str:
    """Generate HowTo JSON-LD."""
    step_values = [line.strip() for line in steps.splitlines() if line.strip()]
    if not step_values:
        raise ValueError("steps must contain at least one step")
    return _jsonld("HowTo", name=name, step=[{"@type": "HowToStep", "position": i, "text": value} for i, value in enumerate(step_values, 1)], totalTime=total_time, tool=[{"@type": "HowToTool", "name": value} for value in _items(tool)])


def jsonld_jobposting(title: str, description: str, hiring_organization: str, employment_type: str = "", date_posted: str = "", valid_through: str = "", salary: float = 0, currency: str = "EUR") -> str:
    """Generate JobPosting JSON-LD."""
    if salary < 0:
        raise ValueError("salary must be non-negative")
    base_salary = {"@type": "MonetaryAmount", "currency": currency, "value": {"@type": "QuantitativeValue", "value": salary}} if salary else None
    return _jsonld("JobPosting", title=title, description=description, hiringOrganization={"@type": "Organization", "name": hiring_organization}, employmentType=employment_type, datePosted=date_posted, validThrough=valid_through, baseSalary=base_salary)


_REQUIRED = {
    "Article": ["headline", "author", "datePublished"], "FAQPage": ["mainEntity"],
    "LocalBusiness": ["name", "address"], "Product": ["name", "offers"],
    "BreadcrumbList": ["itemListElement"], "Review": ["itemReviewed", "author", "reviewRating"],
    "Event": ["name", "startDate"], "Organization": ["name"], "HowTo": ["name", "step"],
    "JobPosting": ["title", "description", "hiringOrganization"],
}


def jsonld_validate(value: str) -> list[dict]:
    """Validate JSON syntax, core JSON-LD keys, and supported required fields."""
    rows = []
    try:
        data = json.loads(value)
        rows.append({"check": "JSON syntax", "ok": True, "message": "Valid JSON"})
    except json.JSONDecodeError as exc:
        return [{"check": "JSON syntax", "ok": False, "message": f"Invalid JSON: {exc.msg}"}, {"check": "verdict", "ok": False, "message": "INVALID"}]
    if not isinstance(data, dict):
        return rows + [{"check": "root object", "ok": False, "message": "JSON-LD root must be an object"}, {"check": "verdict", "ok": False, "message": "INVALID"}]
    for key in ("@context", "@type"):
        rows.append({"check": key, "ok": key in data, "message": "Present" if key in data else "Missing"})
    type_name = data.get("@type")
    if type_name in _REQUIRED:
        missing = [key for key in _REQUIRED[type_name] if key not in data or data[key] in (None, "", [])]
        rows.append({"check": f"required fields ({type_name})", "ok": not missing, "message": "Present" if not missing else "Missing: " + ", ".join(missing)})
    else:
        rows.append({"check": "supported type", "ok": False, "message": f"Unsupported or missing type: {type_name or 'none'}"})
    valid = all(row["ok"] for row in rows)
    rows.append({"check": "verdict", "ok": valid, "message": "VALID" if valid else "INVALID"})
    return rows


class _JSONLDParser(HTMLParser):
    """Collect JSON-LD script contents from an HTML document."""

    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []
        self._active = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "").lower() for key, value in attrs}
        if tag.lower() == "script" and values.get("type", "").split(";")[0].strip() == "application/ld+json":
            self._active, self._parts = True, []

    def handle_data(self, data: str) -> None:
        if self._active:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._active:
            self.blocks.append("".join(self._parts).strip())
            self._active = False


def jsonld_extract(url: str) -> list[dict]:
    """Fetch a URL and extract every JSON-LD script block."""
    if not re.match(r"^https?://", url, re.I):
        raise ValueError("url must be an absolute HTTP(S) URL")
    response = httpx.get(url, timeout=15, follow_redirects=True)
    response.raise_for_status()
    parser = _JSONLDParser()
    parser.feed(response.text)
    rows = []
    for index, block in enumerate(parser.blocks, 1):
        try:
            data = json.loads(block)
            if isinstance(data, dict):
                type_name = data.get("@type", "unknown")
            elif isinstance(data, list):
                type_name = ", ".join(str(item.get("@type", "unknown")) for item in data if isinstance(item, dict)) or "unknown"
            else:
                type_name = "unknown"
        except json.JSONDecodeError:
            type_name = "invalid JSON"
        rows.append({"index": index, "type": type_name, "jsonld": block})
    return rows


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")


register(ToolSpec("jsonld_article", jsonld_article, "Generate Article JSON-LD.", "schema", [A("headline"), A("author"), A("date_published"), A("date_modified", False, ""), A("image", False, ""), A("publisher", False, "")]))
register(ToolSpec("jsonld_faq", jsonld_faq, "Generate FAQPage JSON-LD.", "schema", [A("qa")]))
register(ToolSpec("jsonld_localbusiness", jsonld_localbusiness, "Generate LocalBusiness JSON-LD.", "schema", [A("name"), A("address"), A("phone", False, ""), A("opening_hours", False, ""), A("geo", False, ""), A("price_range", False, ""), A("url", False, "")]))
register(ToolSpec("jsonld_product", jsonld_product, "Generate Product JSON-LD.", "schema", [A("name"), A("description", False, ""), A("sku", False, ""), A("price", False, "0"), A("currency", False, "EUR"), A("availability", False, "InStock"), A("brand", False, ""), A("rating_value", False, "0"), A("review_count", False, "0")]))
register(ToolSpec("jsonld_breadcrumb", jsonld_breadcrumb, "Generate BreadcrumbList JSON-LD.", "schema", [A("paths")]))
register(ToolSpec("jsonld_review", jsonld_review, "Generate Review JSON-LD.", "schema", [A("item_reviewed"), A("author"), A("rating_value"), A("review_body", False, ""), A("date_published", False, "")]))
register(ToolSpec("jsonld_event", jsonld_event, "Generate Event JSON-LD.", "schema", [A("name"), A("start_date"), A("end_date", False, ""), A("location_name", False, ""), A("location_address", False, ""), A("description", False, ""), A("offers_price", False, "0"), A("currency", False, "EUR")]))
register(ToolSpec("jsonld_organization", jsonld_organization, "Generate Organization JSON-LD.", "schema", [A("name"), A("url", False, ""), A("logo", False, ""), A("same_as", False, "")]))
register(ToolSpec("jsonld_howto", jsonld_howto, "Generate HowTo JSON-LD.", "schema", [A("name"), A("steps"), A("total_time", False, ""), A("tool", False, "")]))
register(ToolSpec("jsonld_jobposting", jsonld_jobposting, "Generate JobPosting JSON-LD.", "schema", [A("title"), A("description"), A("hiring_organization"), A("employment_type", False, ""), A("date_posted", False, ""), A("valid_through", False, ""), A("salary", False, "0"), A("currency", False, "EUR")]))
register(ToolSpec("jsonld_validate", jsonld_validate, "Validate JSON-LD syntax and required fields.", "schema", [A("value")], "table"))
register(ToolSpec("jsonld_extract", jsonld_extract, "Extract JSON-LD blocks from a URL.", "schema", [A("url")], "table"))
