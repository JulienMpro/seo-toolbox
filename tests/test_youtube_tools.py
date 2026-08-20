"""Mocked tests for YouTube tools."""

from seotoolbox.tools import youtube_tools as yt


class FakeClient:
    def __init__(self, results): self.results, self.calls = results, []
    def get_result(self, path, payload): self.calls.append((path, payload)); return self.results


def test_youtube_search_info_comments_and_transcript():
    search = yt.youtube_keywords("seo", client=FakeClient([{"items": [{"rank_absolute": 1, "title": "SEO", "views_count": 0}]}]))
    assert search[0]["rank"] == 1 and search[0]["views"] == 0
    info = yt.youtube_video_info("https://youtu.be/abcdefghi", FakeClient([{"title": "Video", "likes_count": 5}]))
    assert info[0]["title"] == "Video" and info[0]["likes"] == 5
    comments = yt.youtube_comments("abcdefghi", client=FakeClient([{"items": [{"author_name": "A", "text": "Useful"}]}]))
    assert comments[0]["text"] == "Useful"
    transcript = yt.youtube_transcript("abcdefghi", client=FakeClient([{"items": [{"text": "SEO tools help SEO teams"}]}]))
    assert "seo tools" in transcript and "Top n-grams" in transcript
