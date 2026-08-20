"""Text, URL, date, and data format converters."""

from __future__ import annotations

import csv
import html
import io
import json
import re
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import quote, unquote

import markdown

from . import ArgSpec, ToolSpec, register


def url_encode(value: str) -> str:
    """Percent-encode a complete URL while preserving no reserved characters."""
    return quote(value, safe="")


def url_decode(value: str) -> str:
    """Decode percent escapes in a URL."""
    return unquote(value)


def strip_accents(value: str) -> str:
    """Remove Unicode combining diacritics."""
    return "".join(char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char))


def text_to_slug(value: str) -> str:
    """Create a lowercase ASCII URL slug."""
    value = strip_accents(value).lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value)).strip("-")


def list_to_urls(value: str, prefix: str = "", suffix: str = "") -> str:
    """Turn one keyword per line into one clean URL per line."""
    return "\n".join(f"{prefix}{text_to_slug(line.strip())}{suffix}" for line in value.splitlines() if line.strip())


def md_to_html(value: str) -> str:
    """Convert Markdown text to HTML."""
    return markdown.markdown(value)


class _MarkdownParser(HTMLParser):
    """Small deterministic HTML-to-Markdown converter for common content tags."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.href: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if re.fullmatch(r"h[1-6]", tag): self.parts.append("\n" + "#" * int(tag[1]) + " ")
        elif tag in {"p", "div"}: self.parts.append("\n")
        elif tag == "br": self.parts.append("  \n")
        elif tag in {"strong", "b"}: self.parts.append("**")
        elif tag in {"em", "i"}: self.parts.append("*")
        elif tag == "li": self.parts.append("\n- ")
        elif tag == "a": self.parts.append("["); self.href.append(attrs_dict.get("href") or "")
        elif tag == "code": self.parts.append("`")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"strong", "b"}: self.parts.append("**")
        elif tag in {"em", "i"}: self.parts.append("*")
        elif tag == "a": self.parts.append(f"]({self.href.pop()})")
        elif tag == "code": self.parts.append("`")
        elif tag in {"p", "div"} or re.fullmatch(r"h[1-6]", tag): self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_md(value: str) -> str:
    """Convert common semantic HTML elements to Markdown."""
    parser = _MarkdownParser()
    parser.feed(value)
    return re.sub(r"\n{3,}", "\n\n", "".join(parser.parts)).strip()


def csv_json(value: str, mode: str = "csv2json") -> str:
    """Convert CSV records to JSON or a JSON object array to CSV."""
    if mode == "csv2json":
        return json.dumps(list(csv.DictReader(io.StringIO(value))), ensure_ascii=False, indent=2)
    if mode == "json2csv":
        records = json.loads(value)
        if isinstance(records, dict): records = [records]
        if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
            raise ValueError("JSON input must be an object or an array of objects")
        if not records: return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
        return output.getvalue().rstrip("\r\n")
    raise ValueError("mode must be csv2json or json2csv")


def case_convert(value: str, mode: str) -> str:
    """Convert text to upper, lower, title, or sentence case."""
    modes = {"upper": str.upper, "lower": str.lower, "title": str.title, "sentence": lambda text: text[:1].upper() + text[1:].lower()}
    if mode.lower() not in modes: raise ValueError("mode must be upper, lower, title, or sentence")
    return modes[mode.lower()](value)


_DATE_FORMATS = {"iso": "%Y-%m-%d", "fr": "%d/%m/%Y", "lastmod": "%Y-%m-%dT%H:%M:%SZ"}


def date_convert(value: str, input_format: str, output_format: str) -> str:
    """Convert dates between ISO, French, epoch timestamp, and sitemap lastmod."""
    if input_format == "timestamp": dt = datetime.fromtimestamp(float(value), timezone.utc)
    elif input_format in _DATE_FORMATS: dt = datetime.strptime(value, _DATE_FORMATS[input_format]).replace(tzinfo=timezone.utc)
    else: raise ValueError("input_format must be iso, fr, timestamp, or lastmod")
    if output_format == "timestamp": return str(int(dt.timestamp()))
    if output_format not in _DATE_FORMATS: raise ValueError("output_format must be iso, fr, timestamp, or lastmod")
    return dt.strftime(_DATE_FORMATS[output_format])


_UNITS = {"b": 1, "o": 1, "kb": 1024, "ko": 1024, "mb": 1024**2, "mo": 1024**2, "gb": 1024**3, "go": 1024**3}


def bytes_human(value: str) -> str:
    """Parse bytes or a localized unit and render a binary human-readable size."""
    match = re.fullmatch(r"\s*([0-9]+(?:[.,][0-9]+)?)\s*([a-zA-Z]*)\s*", str(value))
    if not match: raise ValueError("value must look like 1024 or '5 Mo'")
    number, unit = float(match.group(1).replace(",", ".")), (match.group(2) or "b").lower()
    if unit not in _UNITS: raise ValueError("supported units: B/o, KB/Ko, MB/Mo, GB/Go")
    size = number * _UNITS[unit]
    labels = ((1024**3, "Go"), (1024**2, "Mo"), (1024, "Ko"), (1, "octets"))
    divisor, label = next((divisor, label) for divisor, label in labels if size >= divisor or divisor == 1)
    return f"{size/divisor:.2f} {label} ({int(size)} octets)"


_STOPWORDS = set("a an and are as at be by for from in is it of on or that the this to was with et le la les un une des de du en est pour par sur ou ce cette dans au aux".split())


def tokenize(value: str) -> str:
    """Return sorted unique terms after removing a small French/English stopword list."""
    terms = {strip_accents(term).lower() for term in re.findall(r"[^\W_]+", value, re.UNICODE)}
    return "\n".join(sorted(term for term in terms if term not in _STOPWORDS))


def dedupe_list(value: str) -> str:
    """Trim, sort, and deduplicate non-empty lines."""
    return "\n".join(sorted({line.strip() for line in value.splitlines() if line.strip()}, key=str.casefold))


def html_entities(value: str, mode: str = "encode") -> str:
    """Encode or decode HTML entities."""
    if mode == "encode": return html.escape(value, quote=True)
    if mode == "decode": return html.unescape(value)
    raise ValueError("mode must be encode or decode")


def jsonld_minify(value: str, mode: str = "minify") -> str:
    """Validate and minify or pretty-print JSON-LD."""
    data = json.loads(value)
    if mode == "minify": return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if mode == "beautify": return json.dumps(data, ensure_ascii=False, indent=2)
    raise ValueError("mode must be minify or beautify")


def A(name: str, required: bool = True, default: str | None = None) -> ArgSpec: return ArgSpec(name, required, default, name.replace("_", " ").capitalize() + ".")
register(ToolSpec("url_encode", url_encode, "Percent-encode a URL.", "converters", [A("value")]))
register(ToolSpec("url_decode", url_decode, "Decode percent escapes in a URL.", "converters", [A("value")]))
register(ToolSpec("text_to_slug", text_to_slug, "Convert text to a clean URL slug.", "converters", [A("value")]))
register(ToolSpec("list_to_urls", list_to_urls, "Convert a keyword list to URLs.", "converters", [A("value"), A("prefix", False, ""), A("suffix", False, "")]))
register(ToolSpec("md_to_html", md_to_html, "Convert Markdown to HTML.", "converters", [A("value")]))
register(ToolSpec("html_to_md", html_to_md, "Convert common HTML to Markdown.", "converters", [A("value")]))
register(ToolSpec("csv_json", csv_json, "Convert CSV and JSON bidirectionally.", "converters", [A("value"), A("mode", False, "csv2json")]))
register(ToolSpec("case_convert", case_convert, "Convert text casing.", "converters", [A("value"), A("mode")]))
register(ToolSpec("strip_accents", strip_accents, "Remove text diacritics.", "converters", [A("value")]))
register(ToolSpec("date_convert", date_convert, "Convert ISO, French, epoch, and sitemap dates.", "converters", [A("value"), A("input_format"), A("output_format")]))
register(ToolSpec("bytes_human", bytes_human, "Convert byte sizes to readable units.", "converters", [A("value")]))
register(ToolSpec("tokenize", tokenize, "Extract unique terms without common stopwords.", "converters", [A("value")]))
register(ToolSpec("dedupe_list", dedupe_list, "Clean, sort, and deduplicate lines.", "converters", [A("value")]))
register(ToolSpec("html_entities", html_entities, "Encode or decode HTML entities.", "converters", [A("value"), A("mode", False, "encode")]))
register(ToolSpec("jsonld_minify", jsonld_minify, "Minify or beautify JSON-LD.", "converters", [A("value"), A("mode", False, "minify")]))
