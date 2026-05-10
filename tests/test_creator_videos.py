from datetime import UTC, datetime

from seed.models import Platform
from seed.sources.creator_videos import (
    _bilibili_arc_item_to_video,
    _duration_to_seconds,
    _get_json,
    _parse_duckduckgo_links,
    _wbi_mixin_key,
    fetch_bilibili_creator_video_list,
)


def test_bilibili_arc_item_to_video():
    video = _bilibili_arc_item_to_video(
        {
            "aid": 11,
            "bvid": "BV1xx411c7mD",
            "title": "Demo",
            "created": 1_700_000_000,
            "length": "03:21",
            "play": 1234,
            "comment": 56,
            "description": "desc",
            "pic": "https://example.com/cover.jpg",
        },
        owner="demo",
        owner_id="42",
    )

    assert video.platform == Platform.bilibili
    assert video.owner == "demo"
    assert video.owner_id == "42"
    assert video.video_id == "BV1xx411c7mD"
    assert video.url == "https://www.bilibili.com/video/BV1xx411c7mD"
    assert video.published_at == datetime.fromtimestamp(1_700_000_000, tz=UTC)
    assert video.duration_seconds == 201
    assert video.metrics["play"] == 1234


def test_wbi_mixin_key_uses_bilibili_permutation():
    raw = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"

    assert _wbi_mixin_key(raw) == "UVsc1ixGpYkF6dTJBRfXHjQtDCoNmMPn"


def test_duration_to_seconds():
    assert _duration_to_seconds("01:02") == 62
    assert _duration_to_seconds("01:02:03") == 3723
    assert _duration_to_seconds("bad") is None


def test_parse_duckduckgo_links_extracts_xiaohongshu_results():
    content = """
    <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.xiaohongshu.com%2Fuser%2Fprofile%2Fabc%3Fxsec_token%3D1">profile</a>
    <a class="result__a" href="https://www.xiaohongshu.com/explore/123?xsec_token=2">note</a>
    <a class="result__a" href="https://example.com/skip">skip</a>
    """

    assert _parse_duckduckgo_links(content) == [
        "https://www.xiaohongshu.com/user/profile/abc",
        "https://www.xiaohongshu.com/explore/123",
    ]


def test_bilibili_fetch_records_blocked_listing(monkeypatch):
    monkeypatch.setattr(
        "seed.sources.creator_videos._find_bilibili_user",
        lambda owner_name: {"uname": "demo", "mid": 42, "fans": 10},
    )

    def fail_ytdlp(**kwargs):
        from yt_dlp import DownloadError

        raise DownloadError("blocked")

    monkeypatch.setattr(
        "seed.sources.creator_videos._fetch_bilibili_space_videos_with_ytdlp",
        fail_ytdlp,
    )
    monkeypatch.setattr(
        "seed.sources.creator_videos._fetch_bilibili_space_videos_with_api",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("blocked again")),
    )

    result = fetch_bilibili_creator_video_list(owner_name="demo", limit=3)

    assert result.provider == "bilibili-discovery-blocked"
    assert result.owner_url == "https://space.bilibili.com/42/video"
    assert result.videos == []
    assert "BILIBILI_COOKIES_FILE" in result.notes[-1]


def test_bilibili_fetch_records_blocked_user_search(monkeypatch):
    monkeypatch.setattr(
        "seed.sources.creator_videos._find_bilibili_user",
        lambda owner_name: (_ for _ in ()).throw(RuntimeError("blocked")),
    )

    result = fetch_bilibili_creator_video_list(owner_name="demo", limit=3)

    assert result.provider == "bilibili-user-search-blocked"
    assert result.owner == "demo"
    assert result.videos == []
    assert "BILIBILI_COOKIES_FILE" in result.notes[-1]


def test_get_json_can_allow_expected_nonzero_code(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self):
            return b'{"code": -101, "message": "not logged in", "data": {"ok": true}}'

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response())

    payload = _get_json("https://example.com", allowed_codes=(0, -101, None))

    assert payload["data"]["ok"] is True
