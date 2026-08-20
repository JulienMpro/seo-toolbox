from seotoolbox import monitor
from seotoolbox.models import CrawlResult


def test_monitor_detects_changes_added_and_removed(monkeypatch, tmp_path):
    crawls = [[CrawlResult("https://x/a", 200, title="Old")],
              [CrawlResult("https://x/a", 200, title="New"), CrawlResult("https://x/b", 200)],
              [CrawlResult("https://x/b", 200)]]
    monkeypatch.setattr(monitor, "crawl_site", lambda *args: crawls.pop(0))
    db = tmp_path / "monitor.db"
    assert monitor.init_baseline("https://x", db_path=db) == 1
    report = monitor.check("https://x", db_path=db)
    assert report.added == ["https://x/b"]
    assert any(change.field == "title" for change in report.changes)
    report = monitor.check("https://x", db_path=db)
    assert report.removed == ["https://x/a"]
