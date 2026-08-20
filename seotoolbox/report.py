"""White-label Markdown to HTML (and optional PDF) reporting."""

from __future__ import annotations

import html
from pathlib import Path


DEFAULT_CSS = """
body{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 24px;color:#1f2937;line-height:1.6}
h1,h2,h3{color:var(--brand);line-height:1.25} a{color:var(--brand)}
table{border-collapse:collapse;width:100%;margin:1rem 0}th{background:var(--brand);color:white}
th,td{border:1px solid #d1d5db;padding:.55rem;text-align:left}tr:nth-child(even){background:#f8fafc}
pre,code{background:#f1f5f9;border-radius:4px}pre{padding:1rem;overflow:auto}code{padding:.15rem .3rem}
""".strip()


def md_to_html(md_text: str, title: str, brand_color: str = "#0ea5e9", css: str | None = None) -> str:
    """Render standalone HTML without scripts or remote resources."""
    import markdown
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    styles = css if css is not None else DEFAULT_CSS
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{html.escape(title)}</title>"
            f"<style>:root{{--brand:{html.escape(brand_color)}}}{styles}</style></head><body>{body}</body></html>")


def build_report(md_path: str | Path, title: str, output_path: str | Path,
                 brand_color: str = "#0ea5e9") -> Path:
    source, destination = Path(md_path), Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(md_to_html(source.read_text(encoding="utf-8"), title, brand_color), encoding="utf-8")
    return destination


def pdf_export(md_path: str | Path, output_path: str | Path) -> Path:
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise RuntimeError("weasyprint not installed — pip install weasyprint") from exc
    destination = Path(output_path)
    HTML(string=md_to_html(Path(md_path).read_text(encoding="utf-8"), Path(md_path).stem)).write_pdf(destination)
    return destination
