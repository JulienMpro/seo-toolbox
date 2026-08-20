import pytest

from seotoolbox.report import build_report, md_to_html


def test_markdown_report_is_standalone(tmp_path):
    html = md_to_html("# Hello\n\n| A |\n|---|\n| B |", "Client <Report>", "#123456")
    assert "<h1>Hello</h1>" in html and "#123456" in html
    assert "Client &lt;Report&gt;" in html and "http" not in html
    source, output = tmp_path / "in.md", tmp_path / "out.html"
    source.write_text("# Test")
    assert build_report(source, "Test", output) == output and output.exists()
