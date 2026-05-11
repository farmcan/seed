from seed.creator_ingest import ingest_creator_videos
from seed.library import save_creator_video_list, save_source_record
from seed.models import CreatorVideo, CreatorVideoList, DownloadResult, Platform, SourceRecord


def test_ingest_creator_videos_downloads_when_existing_record_has_no_raw_path(tmp_path, monkeypatch):
    library_root = tmp_path / "library"
    video = CreatorVideo(
        platform=Platform.bilibili,
        owner="demo",
        title="Demo Video",
        url="https://www.bilibili.com/video/BV1",
    )
    list_path = save_creator_video_list(
        library_root,
        CreatorVideoList(
            platform=Platform.bilibili,
            owner_query="demo",
            owner="demo",
            provider="test",
            videos=[video],
        ),
    )
    save_source_record(
        library_root,
        SourceRecord(
            url=video.url,
            platform=Platform.bilibili,
            owner="demo",
            title="Demo Video",
            authorized=True,
        ),
    )

    raw_path = library_root / "raw" / "demo.mp4"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(b"video")
    calls = []

    def fake_download_url(*args, **kwargs):
        calls.append(args[0])
        return DownloadResult(
            title="Demo Video",
            owner="demo",
            raw_path=raw_path,
            provider="test",
        )

    monkeypatch.setattr("seed.creator_ingest.download_url", fake_download_url)

    result = ingest_creator_videos(
        list_path,
        library_root=library_root,
        authorized=True,
        skip_existing=True,
    )

    assert calls == [video.url]
    assert result.downloaded == 1
    assert result.skipped == 0
