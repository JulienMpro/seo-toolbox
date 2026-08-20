"""Unit tests for converters and encoders."""

from seotoolbox.tools import converters as c


def test_url_encode_decode():
    encoded = c.url_encode("https://example.com/a b")
    assert "%3A%2F%2F" in encoded and c.url_decode(encoded) == "https://example.com/a b"


def test_text_to_slug(): assert c.text_to_slug("Été à Paris !") == "ete-a-paris"
def test_list_to_urls(): assert c.list_to_urls("Hello World\nSEO", "/", "/") == "/hello-world/\n/seo/"
def test_md_to_html(): assert "<strong>bold</strong>" in c.md_to_html("**bold**")
def test_html_to_md(): assert c.html_to_md("<h1>Title</h1><p><strong>Bold</strong></p>") == "# Title\n\n**Bold**"


def test_csv_json():
    result = c.csv_json("name,age\nAda,30")
    assert '"Ada"' in result
    assert "name,age" in c.csv_json(result, "json2csv")


def test_case_convert(): assert c.case_convert("hELLO", "sentence") == "Hello"
def test_strip_accents(): assert c.strip_accents("Crème brûlée") == "Creme brulee"
def test_date_convert(): assert c.date_convert("20/08/2026", "fr", "iso") == "2026-08-20"
def test_bytes_human(): assert c.bytes_human("5 Mo") == "5.00 Mo (5242880 octets)"
def test_tokenize(): assert c.tokenize("Le SEO et the Content") == "content\nseo"
def test_dedupe_list(): assert c.dedupe_list("b\na\na\n") == "a\nb"
def test_html_entities(): assert c.html_entities("&lt;b&gt;", "decode") == "<b>"
def test_jsonld_minify(): assert c.jsonld_minify('{"@type": "Article"}') == '{"@type":"Article"}'
