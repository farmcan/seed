from seed.creator_pipeline import (
    CreatorPipelineOptions,
    creator_pipeline_manifest_path,
    run_creator_pipeline,
)
from seed.models import CreatorVideo, CreatorVideoIngestItem, CreatorVideoIngestResult, CreatorVideoList, Platform


def test_creator_pipeline_manifest_path(tmp_path):
    assert creator_pipeline_manifest_path(library_root=tmp_path, owner="某 UP") == (
        tmp_path / "runs" / "某-up.creator-pipeline.yaml"
    )


def test_run_creator_pipeline_records_video_runs(tmp_path, monkeypatch):
    video_list = CreatorVideoList(
        platform=Platform.bilibili,
        owner_query="demo",
        owner="demo",
        provider="test",
        videos=[
            CreatorVideo(
                platform=Platform.bilibili,
                owner="demo",
                title="Demo Video",
                url="https://www.bilibili.com/video/BV1",
            )
        ],
    )

    def fake_fetch_creator_video_list(**kwargs):
        return video_list

    def fake_ingest_creator_videos(*args, **kwargs):
        raw_path = tmp_path / "library" / "raw" / "demo.mp4"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(b"video")
        return CreatorVideoIngestResult(
            selected=1,
            downloaded=1,
            recorded=1,
            items=[
                CreatorVideoIngestItem(
                    url="https://www.bilibili.com/video/BV1",
                    title="Demo Video",
                    status="downloaded",
                    raw_path=raw_path,
                )
            ],
        )

    def fake_run_video_pipeline(options):
        manifest = tmp_path / "library" / "runs" / "demo.video-pipeline.yaml"
        html = tmp_path / "library" / "graphs" / "demo.video-dag.html"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        html.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("steps: []", encoding="utf-8")
        html.write_text("<html></html>", encoding="utf-8")
        context = type("Context", (), {"html_path": html})()
        return context, manifest

    monkeypatch.setattr("seed.creator_pipeline.fetch_creator_video_list", fake_fetch_creator_video_list)
    monkeypatch.setattr("seed.creator_pipeline.ingest_creator_videos", fake_ingest_creator_videos)
    monkeypatch.setattr("seed.creator_pipeline.run_video_pipeline", fake_run_video_pipeline)

    manifest, manifest_path = run_creator_pipeline(
        CreatorPipelineOptions(
            owner_name="demo",
            platform=Platform.bilibili,
            library_root=tmp_path / "library",
            authorized=True,
            vision=False,
        )
    )

    assert manifest_path.exists()
    assert manifest["video_runs"][0]["status"] == "completed"
    assert manifest["video_runs"][0]["html_path"].endswith("demo.video-dag.html")
