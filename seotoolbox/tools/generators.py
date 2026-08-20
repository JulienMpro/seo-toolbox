"""Local SEO markup and content generators."""

from __future__ import annotations

import csv
import io
import json
import re
from html import escape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.sax.saxutils import escape as xml_escape

from . import ArgSpec, ToolSpec, register


def _items(value: str) -> list[str]:
    """Split newline- or comma-separated input while preserving order."""
    return [item.strip() for item in re.split(r"[\n,]+", value) if item.strip()]


def _pixel_width(value: str) -> int:
    """Estimate Google title width using coarse character classes."""
    return sum(9 if char.isupper() else 4 if char in " ilI.,:;'|!" else 7 for char in value)


def redirect_generator(old: str, new: str) -> str:
    """Generate Apache, nginx, and CSV permanent redirect rules."""
    olds, news = _items(old), _items(new)
    if len(news) == 1 and news[0].startswith("pattern:"):
        replacement = news[0][8:].strip()
        if len(olds) != 1 or not replacement:
            raise ValueError("pattern redirects require one old pattern and pattern:replacement")
        pairs = [(olds[0], replacement)]
    else:
        if not olds or len(olds) != len(news):
            raise ValueError("old and new must contain the same number of URLs")
        pairs = list(zip(olds, news))
    apache = [f"Redirect 301 {source} {target}" for source, target in pairs]
    nginx = [f"rewrite ^{source}$ {target} permanent;" for source, target in pairs]
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["old", "new", "code"])
    writer.writerows((source, target, 301) for source, target in pairs)
    return "# .htaccess\n" + "\n".join(apache) + "\n\n# nginx\n" + "\n".join(nginx) + "\n\n# CSV\n" + output.getvalue().rstrip()


def robots_generator(user_agent: str = "*", disallow: str = "", allow: str = "", sitemap: str = "") -> str:
    """Generate a valid robots.txt file."""
    lines = [f"User-agent: {user_agent or '*'}"]
    lines += [f"Disallow: {path}" for path in _items(disallow)]
    lines += [f"Allow: {path}" for path in _items(allow)]
    if sitemap:
        lines += ["", f"Sitemap: {sitemap.strip()}"]
    return "\n".join(lines)


def sitemap_generator(urls: str, lastmod: str = "", priority: float = 0.5) -> str:
    """Generate an escaped XML sitemap from URLs."""
    if not 0 <= priority <= 1:
        raise ValueError("priority must be between 0 and 1")
    values = _items(urls)
    if not values:
        raise ValueError("urls must contain at least one URL")
    nodes = []
    for url in values:
        fields = [f"    <loc>{xml_escape(url)}</loc>"]
        if lastmod:
            fields.append(f"    <lastmod>{xml_escape(lastmod)}</lastmod>")
        fields.append(f"    <priority>{priority:g}</priority>")
        nodes.append("  <url>\n" + "\n".join(fields) + "\n  </url>")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(nodes) + "\n</urlset>"


def meta_generator(keyword: str, template: str, description: str = "{kw}", brand: str = "") -> list[dict]:
    """Render title and description templates and report their fit."""
    try:
        title = template.format(kw=keyword, brand=brand)
        meta = description.format(kw=keyword, brand=brand)
    except KeyError as exc:
        raise ValueError(f"unknown template placeholder: {exc.args[0]}") from exc
    title_px = _pixel_width(title)
    return [
        {"field": "title", "value": title, "length": f"{title_px}px", "status": "ok" if title_px <= 600 else "truncated"},
        {"field": "description", "value": meta, "length": len(meta), "status": "ok" if len(meta) <= 155 else "truncated"},
    ]


def _language_urls(value: str) -> list[tuple[str, str]]:
    pairs = []
    for item in _items(value):
        separator = "|" if "|" in item else ":"
        language, found, url = item.partition(separator)
        if not found or not language or not url:
            raise ValueError("urls must use lang:url or lang|url")
        pairs.append((language.strip(), url.strip()))
    if not pairs:
        raise ValueError("urls must contain at least one language URL")
    return pairs


def hreflang_generator(urls: str, x_default: str = "") -> str:
    """Generate escaped hreflang link elements and an x-default."""
    pairs = _language_urls(urls)
    default = x_default.strip() or pairs[0][1]
    lines = [f'<link rel="alternate" hreflang="{escape(lang, quote=True)}" href="{escape(url, quote=True)}">' for lang, url in pairs]
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{escape(default, quote=True)}">')
    return "\n".join(lines)


def anchor_generator(keywords: str, brand: str = "", url: str = "") -> list[dict]:
    """Create deterministic natural anchor variants for target keywords."""
    rows = []
    for keyword in _items(keywords):
        partial = " ".join(keyword.split()[:-1]) or keyword
        variants = [("exact", keyword), ("partial", f"guide {partial}"), ("generic", "voir plus")]
        if brand:
            variants.append(("brand", brand))
        if url:
            variants.append(("naked", url))
        rows += [{"keyword": keyword, "type": kind, "anchor": anchor} for kind, anchor in variants]
    return rows


def title_variants(title: str, count: int = 8) -> list[dict]:
    """Generate up to eight structurally distinct title variants."""
    if count <= 0:
        raise ValueError("count must be positive")
    candidates = [f"Pourquoi choisir {title} ?", f"7 conseils : {title}", f"{title} (Guide complet)", f"Guide : {title}", f"{title} — Mode d'emploi", f"Les 10 clés de {title}", f"{title} : agissez maintenant", f"{title} à [Ville]"]
    return [{"n": i, "title": value, "length_px": _pixel_width(value)} for i, value in enumerate((candidates * ((count + 7) // 8))[:count], 1)]


def meta_variants(description: str, count: int = 5) -> list[dict]:
    """Generate deterministic meta-description variants."""
    if count <= 0:
        raise ValueError("count must be positive")
    candidates = [f"Découvrez {description}", f"{description} En savoir plus.", f"Vous cherchez une solution ? {description}", f"{description} Contactez-nous dès aujourd'hui.", f"5 raisons de choisir notre solution : {description}"]
    values = (candidates * ((count + 4) // 5))[:count]
    return [{"n": i, "description": value, "length": len(value)} for i, value in enumerate(values, 1)]


def internal_link_generator(pages: str, keywords: str) -> list[dict]:
    """Suggest source pages for targets whose title contains a keyword."""
    parsed = []
    for line in pages.splitlines():
        title, separator, url = line.partition("|")
        if line.strip() and (not separator or not title.strip() or not url.strip()):
            raise ValueError("pages must use title|url, one page per line")
        if line.strip():
            parsed.append((title.strip(), url.strip()))
    rows = []
    for keyword in _items(keywords):
        target = next(((title, url) for title, url in parsed if keyword.casefold() in title.casefold()), None)
        if target:
            sources = [url for title, url in parsed if url != target[1]]
            rows.append({"keyword": keyword, "target_page": target[1], "proposed_source_pages": ", ".join(sources), "suggested_anchor": keyword})
    return rows


def _breadcrumbs(paths: str) -> list[dict]:
    lines = [line.strip() for line in paths.splitlines() if line.strip()]
    if not lines:
        raise ValueError("paths must contain at least one breadcrumb")
    names = [part.strip() for part in lines[0].split(">") if part.strip()]
    return [{"@type": "ListItem", "position": i, "name": name} for i, name in enumerate(names, 1)]


def breadcrumb_generator(paths: str) -> str:
    """Generate BreadcrumbList JSON-LD and a simple visual HTML trail."""
    items = _breadcrumbs(paths)
    data = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}
    visual = " &gt; ".join(escape(item["name"]) for item in items)
    return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2) + f'\n</script>\n<nav aria-label="Breadcrumb">{visual}</nav>'


def snippet_generator(content: str, type: str = "paragraph") -> str:
    """Format supplied content as a paragraph, list, or key/value table snippet."""
    lines = [line.strip(" -\t") for line in content.splitlines() if line.strip()]
    if type == "paragraph":
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())
        return " ".join(sentences[:3])
    if type == "list":
        return "\n".join(f"{index}. {line}" for index, line in enumerate(lines, 1))
    if type == "table":
        rows = [line.split(":", 1) for line in lines if ":" in line]
        if not rows:
            raise ValueError("table content must contain key: value lines")
        return "| Key | Value |\n| --- | --- |\n" + "\n".join(f"| {key.strip()} | {value.strip()} |" for key, value in rows)
    raise ValueError("type must be paragraph, list, or table")


def canonical_generator(url: str, force_https: bool = False, remove_www: bool = False, remove_trailing_slash: bool = False, remove_params: str = "") -> list[dict]:
    """Normalize a canonical URL and list each transformation."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url must be an absolute HTTP(S) URL")
    variants = [("input", url)]
    scheme = "https" if force_https else parsed.scheme
    host = parsed.netloc[4:] if remove_www and parsed.netloc.lower().startswith("www.") else parsed.netloc
    path = parsed.path.rstrip("/") if remove_trailing_slash and parsed.path != "/" else parsed.path
    removed = set(_items(remove_params))
    query = urlencode([(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key not in removed])
    canonical = urlunsplit((scheme, host, path, query, ""))
    if canonical != url:
        variants.append(("normalized", canonical))
    return [{"variant": name, "url": value, "canonical?": value == canonical} for name, value in variants]


def og_generator(title: str, description: str, image: str, type: str = "website", url: str = "", site_name: str = "", twitter: str = "") -> str:
    """Generate complete Open Graph and Twitter Card meta elements."""
    values = [("og:title", title), ("og:description", description), ("og:image", image), ("og:type", type), ("og:url", url), ("og:site_name", site_name)]
    lines = [f'<meta property="{key}" content="{escape(value, quote=True)}">' for key, value in values if value]
    lines += ['<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:title" content="{escape(title, quote=True)}">', f'<meta name="twitter:description" content="{escape(description, quote=True)}">', f'<meta name="twitter:image" content="{escape(image, quote=True)}">']
    if twitter:
        handle = twitter if twitter.startswith("@") else "@" + twitter
        lines.append(f'<meta name="twitter:site" content="{escape(handle, quote=True)}">')
    return "\n".join(lines)


def A(name: str, required: bool = True, default: str | None = None, flag: bool = False) -> ArgSpec:
    return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".", flag)


register(ToolSpec("redirect_generator", redirect_generator, "Generate Apache, nginx, and CSV redirects.", "generators", [A("old"), A("new")]))
register(ToolSpec("robots_generator", robots_generator, "Generate a robots.txt file.", "generators", [A("user_agent", False, "*"), A("disallow", False, ""), A("allow", False, ""), A("sitemap", False, "")]))
register(ToolSpec("sitemap_generator", sitemap_generator, "Generate an XML sitemap.", "generators", [A("urls"), A("lastmod", False, ""), A("priority", False, "0.5")]))
register(ToolSpec("meta_generator", meta_generator, "Generate title and meta-description content.", "generators", [A("keyword"), A("template"), A("description", False, "{kw}"), A("brand", False, "")], "table"))
register(ToolSpec("hreflang_generator", hreflang_generator, "Generate hreflang and x-default links.", "generators", [A("urls"), A("x_default", False, "")]))
register(ToolSpec("anchor_generator", anchor_generator, "Generate anchor-text variants.", "generators", [A("keywords"), A("brand", False, ""), A("url", False, "")], "table"))
register(ToolSpec("title_variants", title_variants, "Generate title variants for testing.", "generators", [A("title"), A("count", False, "8")], "table"))
register(ToolSpec("meta_variants", meta_variants, "Generate meta-description variants.", "generators", [A("description"), A("count", False, "5")], "table"))
register(ToolSpec("internal_link_generator", internal_link_generator, "Suggest internal links from a page set.", "generators", [A("pages"), A("keywords")], "table"))
register(ToolSpec("breadcrumb_generator", breadcrumb_generator, "Generate JSON-LD and HTML breadcrumbs.", "generators", [A("paths")]))
register(ToolSpec("snippet_generator", snippet_generator, "Format content for a featured snippet.", "generators", [A("content"), A("type", False, "paragraph")]))
register(ToolSpec("canonical_generator", canonical_generator, "Normalize and identify a canonical URL.", "generators", [A("url"), A("force_https", False, flag=True), A("remove_www", False, flag=True), A("remove_trailing_slash", False, flag=True), A("remove_params", False, "")], "table"))
register(ToolSpec("og_generator", og_generator, "Generate Open Graph and Twitter Card markup.", "generators", [A("title"), A("description"), A("image"), A("type", False, "website"), A("url", False, ""), A("site_name", False, ""), A("twitter", False, "")]))
