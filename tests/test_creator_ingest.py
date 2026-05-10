import yaml

from seed.creator_ingest import ingest_creator_videos
from seed.library import save_creator_video_list, save_source_record
from seed.models import CreatorVideo, CreatorVideoList, DownloadResult, Platform, SourceRecord


def test_ingest_creator_videos_records_without_download(tmp_path):
    list_path = save_creator_video_list(
        tmp_path,
        CreatorVideoList(
            platform=Platform.bilibili,
            owner_query="demo",
            owner="demo",
            provider="test",
            videos=[
                CreatorVideo(
                    platform=Platform.bilibili,
                    owner="demo",
                    title="Demo 1",
                    url="https://www.bilibili.com/video/BV1",
                ),
                CreatorVideo(
                    platform=Platform.bilibili,
                    owner="demo",
                    title="Demo 2",
                    url="https://www.bilibili.com/video/BV2",
                ),
            ],
        ),
    )

    result = ingest_creator_videos(
        list_path,
        library_root=tmp_path,
        authorized=False,
        download=False,
        limit=1,
    )

    assert result.selected == 1
    assert result.recorded == 1
    assert result.downloaded == 0
    assert result.items[0].status == "recorded"
    records = list((tmp_path / "notes").glob("*.source.yaml"))
    assert len(records) == 1
    data = yaml.safe_load(records[0].read_text(encoding="utf-8"))
    assert data["url"] == "https://www.bilibili.com/video/BV1"


def test_ingest_creator_videos_skips_existing_source(tmp_path):
    save_source_record(
        tmp_path,
        SourceRecord(
            url="https://www.bilibili.com/video/BV1/",
            platform=Platform.bilibili,
            owner="demo",
            title="Existing",
            authorized=True,
        ),
    )
    list_path = save_creator_video_list(
        tmp_path,
        CreatorVideoList(
            platform=Platform.bilibili,
            owner_query="demo",
            owner="demo",
            provider="test",
            videos=[
                CreatorVideo(
                    platform=Platform.bilibili,
                    owner="demo",
                    title="Existing",
                    url="https://www.bilibili.com/video/BV1",
                )
            ],
        ),
    )

    result = ingest_creator_videos(
        list_path,
        library_root=tmp_path,
        authorized=True,
        download=False,
    )

    assert result.selected == 1
    assert result.skipped == 1
    assert result.recorded == 0


def test_ingest_creator_videos_downloads_and_saves_record(tmp_path, monkeypatch):
    list_path = save_creator_video_list(
        tmp_path,
        CreatorVideoList(
            platform=Platform.bilibili,
            owner_query="demo",
            owner="demo",
            provider="test",
            videos=[
                CreatorVideo(
                    platform=Platform.bilibili,
                    owner="demo",
                    title="List Title",
                    url="https://www.bilibili.com/video/BV1",
                )
            ],
        ),
    )
    media_path = tmp_path / "raw" / "demo.mp4"
    metadata_path = tmp_path / "raw" / "demo.info.json"

    def fake_download_url(url, **kwargs):
        assert url == "https://www.bilibili.com/video/BV1"
        assert kwargs["platform"] == Platform.bilibili
        return DownloadResult(
            title="Downloaded Title",
            owner="downloaded-owner",
            raw_path=media_path,
            metadata_path=metadata_path,
            provider="bilibili-api",
            fallback_used=True,
            notes=["fallback used"],
        )

    monkeypatch.setattr("seed.creator_ingest.download_url", fake_download_url)

    result = ingest_creator_videos(
        list_path,
        library_root=tmp_path,
        authorized=True,
        download=True,
    )

    assert result.downloaded == 1
    assert result.recorded == 1
    assert result.items[0].raw_path == media_path
    assert result.items[0].metadata_path == metadata_path
    record_text = result.items[0].source_record_path.read_text(encoding="utf-8")
    assert "Downloaded Title" in record_text
    assert "downloaded-owner" in record_text
    assert "download_provider: bilibili-api" in record_text
    assert "fallback_used: true" in record_text
    assert "fallback used" in record_text
