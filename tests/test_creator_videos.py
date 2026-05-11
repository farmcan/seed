from seed.models import CreatorVideo, Platform
from seed.sources.creator_videos import fetch_bilibili_creator_video_list


def test_fetch_bilibili_creator_video_list_uses_provided_owner_id(monkeypatch):
    calls = {}

    def fake_space_videos(**kwargs):
        calls.update(kwargs)
        return [
            CreatorVideo(
                platform=Platform.bilibili,
                owner=kwargs["owner"],
                owner_id=kwargs["owner_id"],
                title="Demo",
                url="https://www.bilibili.com/video/BV1",
            )
        ]

    def blocked_search(owner_name):
        raise AssertionError("user search should be skipped when owner_id is provided")

    monkeypatch.setattr("seed.sources.creator_videos._find_bilibili_user", blocked_search)
    monkeypatch.setattr(
        "seed.sources.creator_videos._fetch_bilibili_space_videos_with_ytdlp",
        fake_space_videos,
    )

    video_list = fetch_bilibili_creator_video_list(
        owner_name="Demo UP",
        owner_id="12345",
        limit=1,
    )

    assert video_list.owner == "Demo UP"
    assert video_list.owner_id == "12345"
    assert video_list.provider == "yt-dlp:bilibili-space"
    assert video_list.videos[0].owner_id == "12345"
    assert calls["owner_url"] == "https://space.bilibili.com/12345/video"
    assert "skipped user-name search" in video_list.notes[0]
