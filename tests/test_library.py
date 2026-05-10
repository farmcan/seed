import yaml

from seed.library import init_library, save_creator_video_list, save_methodology, slugify
from seed.models import CreatorVideo, CreatorVideoList, Methodology, Platform, SourceRecord


def test_init_library_creates_expected_dirs(tmp_path):
    created = init_library(tmp_path)

    assert {path.name for path in created} == {
        "raw",
        "transcripts",
        "notes",
        "semantics",
        "timelines",
        "graphs",
        "distilled",
        "skills",
        "checks",
    }


def test_save_methodology(tmp_path):
    path = save_methodology(
        tmp_path,
        Methodology(id="creator-topic", title="Title", owner="creator", topic="topic"),
    )

    assert path.exists()
    assert "creator" in path.read_text(encoding="utf-8")


def test_slugify_keeps_chinese_words():
    assert slugify("某 UP / 增长 方法论") == "某-up-增长-方法论"


def test_source_record_can_include_download_paths(tmp_path):
    media_path = tmp_path / "raw" / "demo.mp4"
    metadata_path = tmp_path / "raw" / "demo.info.json"
    record = SourceRecord(
        url="https://www.bilibili.com/video/BV1xx411c7mD/",
        platform=Platform.bilibili,
        owner="demo",
        authorized=True,
        raw_path=media_path,
        metadata_path=metadata_path,
        download_provider="yt-dlp",
        fallback_used=True,
        download_notes=["used fallback"],
    )

    assert record.raw_path == media_path
    assert record.metadata_path == metadata_path
    assert record.download_provider == "yt-dlp"
    assert record.fallback_used
    assert record.download_notes == ["used fallback"]


def test_save_creator_video_list(tmp_path):
    path = save_creator_video_list(
        tmp_path,
        CreatorVideoList(
            platform=Platform.bilibili,
            owner_query="demo",
            owner="demo",
            owner_id="123",
            owner_url="https://space.bilibili.com/123/video",
            provider="test",
            videos=[
                CreatorVideo(
                    platform=Platform.bilibili,
                    owner="demo",
                    owner_id="123",
                    video_id="BV1xx411c7mD",
                    title="Demo Video",
                    url="https://www.bilibili.com/video/BV1xx411c7mD",
                )
            ],
        ),
    )

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert path.name == "bilibili-demo-creator-videos.creator-videos.yaml"
    assert data["owner"] == "demo"
    assert data["videos"][0]["video_id"] == "BV1xx411c7mD"
