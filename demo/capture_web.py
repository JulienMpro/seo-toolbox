#!/usr/bin/env python3
"""Capture the five pages of the live SEO Toolbox demo.

The script is intentionally small and disposable.  It does not mock API data:
each URL is loaded from the already-running local FastAPI server before a
full-page PNG is written to ``demo/captures``.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:8010"
CAPTURE_DIR = Path(__file__).resolve().parent / "captures"
PLAYWRIGHT_CACHE = Path.home() / ".cache" / "ms-playwright"
PAGES = (
    ("/", "01-dashboard.png"),
    ("/keywords?seed=plombier%20paris&country=FR&limit=10", "02-keywords.png"),
    ("/serp?keyword=plombier%20paris&country=FR&limit=10", "03-serp.png"),
    ("/geo?keyword=geo%20seo&engine=chatgpt&limit=10", "04-geo.png"),
    ("/backlinks?domain=wikipedia.org", "05-backlinks.png"),
)


def chromium_executable() -> str | None:
    """Use an installed cached Chromium when Playwright revisions differ."""
    candidates = sorted(
        PLAYWRIGHT_CACHE.glob("chromium-*/chrome-linux64/chrome"), reverse=True
    )
    return str(candidates[0]) if candidates else None


def main() -> None:
    """Load every demo page and capture it, including rendered error pages."""
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []

    with sync_playwright() as playwright:
        executable = chromium_executable()
        launch_options = {"headless": True}
        if executable:
            # The execution environment can contain a cached browser from a
            # slightly older Playwright revision; it remains suitable here.
            launch_options["executable_path"] = executable
        browser = playwright.chromium.launch(**launch_options)
        context = browser.new_context(viewport={"width": 1280, "height": 900})

        for path, filename in PAGES:
            page = context.new_page()
            url = f"{BASE_URL}{path}"
            destination = CAPTURE_DIR / filename

            try:
                page.goto(url, wait_until="networkidle", timeout=90_000)
            except PlaywrightTimeoutError:
                note = f"{filename}: networkidle timeout; captured current rendering"
                notes.append(note)
                print(f"WARNING: {note}")
            except Exception as exc:  # Capture a browser/server error page too.
                note = f"{filename}: navigation error: {exc}"
                notes.append(note)
                print(f"WARNING: {note}")

            try:
                page.wait_for_selector("main, table, .serp-list, .error", timeout=60_000)
            except PlaywrightTimeoutError:
                note = f"{filename}: content selector timeout; captured current rendering"
                notes.append(note)
                print(f"WARNING: {note}")

            page.screenshot(path=str(destination), full_page=True)
            print(f"Captured {destination} ({destination.stat().st_size} bytes)")
            page.close()

        context.close()
        browser.close()

    if notes:
        print("\nCapture notes:")
        for note in notes:
            print(f"- {note}")
    else:
        print("\nAll pages loaded without timeout or navigation error.")


if __name__ == "__main__":
    main()
