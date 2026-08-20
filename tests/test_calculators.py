"""Unit tests for local SEO calculators."""

import pytest

from seotoolbox.tools import calculators as c


def test_roi_seo():
    rows = c.roi_seo(2000, 300, 40, 2, 12)
    assert len(rows) == 12 and rows[0]["month"] == 1


def test_traffic_projection():
    assert c.traffic_projection(10000, 10)[0]["estimated_traffic"] == 1000


def test_position_value():
    assert "€500.00" in c.position_value(10000, 1, 5, 10)


def test_ctr_curve():
    assert len(c.ctr_curve()) == 20
    assert c.ctr_curve(1)[0]["desktop_ctr_pct"] == 28.5


def test_ads_equivalent(): assert "€1000.00" in c.ads_equivalent(500, 2)
def test_conversion_rate(): assert "10.00%" in c.conversion_rate(100, 10)
def test_implicit_cpc(): assert "€2.00" in c.implicit_cpc(1000, 500)
def test_cac_ltv(): assert "5.00" in c.cac_ltv(1000, 10, 500)
def test_crawl_time(): assert "100.00 s" in c.crawl_time(1000, 10)
def test_sitemap_split(): assert "Sitemap files: 3" in c.sitemap_split(100001)
def test_eeat_score(): assert "20/100" in c.eeat_score(author=True, bio=True)
def test_backlink_value(): assert "€100.00" in c.backlink_value(50, 100, 1)
def test_content_cost(): assert "€200.00" in c.content_cost(1000, 100, 2)


def test_calculator_validation():
    with pytest.raises(ValueError): c.conversion_rate(0, 0)
