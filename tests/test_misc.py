"""Unit tests for miscellaneous mini-tools."""

from seotoolbox.tools import misc


def test_check_http(monkeypatch):
    class Response:
        url = "https://example.com/"
        status_code = 200
        headers = {"server": "test"}
    monkeypatch.setattr(misc.httpx, "get", lambda *args, **kwargs: Response())
    monkeypatch.setattr(misc.socket, "gethostbyname", lambda host: "192.0.2.1")
    assert misc.check_http("https://example.com")[0]["status"] == 200


def test_extract_emails(): assert misc.extract_emails("b@x.com a@x.com b@x.com") == "a@x.com\nb@x.com"
def test_extract_urls(): assert misc.extract_urls('<a href="https://x.com/a">x</a>') == "https://x.com/a"
def test_text_diff(): assert "+new" in misc.text_diff("old", "new")
def test_count_text(): assert "words: 2" in misc.count_text("Hello world")


def test_lorem_seo():
    result = misc.lorem_seo(2, 5, "audit")
    assert len(result.split("\n\n")) == 2


def test_tz_convert(): assert misc.tz_convert("2026-08-20T12:00", "UTC", "Europe/Paris").startswith("2026-08-20T14:00")
