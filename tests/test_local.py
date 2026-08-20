from seotoolbox import local


class FakeClient:
    def __init__(self, values): self.values, self.calls = values, []
    def get_result(self, path, payload): self.calls.append((path, payload)); return self.values


def test_listings_normalizes_nested_rating_and_coordinates():
    client = FakeClient([{"items": [{"title": "Plomberie A", "address": "1 rue A", "phone": "01",
        "category": "Plumber", "rating": {"value": 4.8, "votes_count": 12}, "place_id": "p1",
        "coordinates": {"latitude": 48.8, "longitude": 2.3}}]}])
    values = local.listings("plombier", "paris", "FR", 5, client)
    assert values[0].rating == 4.8 and values[0].reviews_count == 12
    assert client.calls[0][1]["title"] == "plombier"
    assert client.calls[0][1]["filters"][0] == ["address_info.city", "=", "Paris"]


def test_local_rank_extracts_pack(monkeypatch):
    monkeypatch.setattr(local.serp, "_raw", lambda *args: [{"items": [{"type": "local_pack", "items": [
        {"rank_group": 1, "title": "A", "rating": {"value": 4.5, "votes_count": 9}}]}]}])
    assert local.local_rank("plombier", "paris")[0].title == "A"


def test_location_mapping_rejects_unknown_country():
    assert local.map_country_location("GB") == "United Kingdom"
