from datetime import UTC, datetime

from seed.creator_pipeline import (
    CreatorPipelineOptions,
    creator_pipeline_manifest_path,
    filter_creator_video_list_by_date,
    run_creator_pipeline,
)
from seed.models import CreatorVideo, CreatorVideoIngestItem, CreatorVideoIngestResult, CreatorVideoList, Platform


def test_creator_pipeline_manifest_path(tmp_path):
    assert creator_pipeline_manifest_path(library_root=tmp_path, owner="某 UP") == (
        tmp_path / "runs" / "某-up.creator-pipeline.yaml"
    )


def test_filter_creator_video_list_by_published_window():
    video_list = CreatorVideoList(
        platform=Platform.bilibili,
        owner_query="demo",
        owner="demo",
        provider="test",
        videos=[
            CreatorVideo(
                platform=Platform.bilibili,
                owner="demo",
                title="Old",
                url="https://bili/old",
                published_at=datetime(2026, 5, 1, tzinfo=UTC),
            ),
            CreatorVideo(
                platform=Platform.bilibili,
                owner="demo",
                title="Fresh",
                url="https://bili/fresh",
                published_at=datetime(2026, 5, 12, tzinfo=UTC),
            ),
            CreatorVideo(platform=Platform.bilibili, owner="demo", title="Unknown", url="https://bili/unknown"),
        ],
    )

    filtered = filter_creator_video_list_by_date(
        video_list,
        CreatorPipelineOptions(
            owner_name="demo",
            platform=Platform.bilibili,
            published_after=datetime(2026, 5, 10, tzinfo=UTC),
            published_before=datetime(2026, 5, 14, tzinfo=UTC),
        ),
    )

    assert [video.title for video in filtered.videos] == ["Fresh"]
    assert "missing_dates_excluded=1" in filtered.notes[-1]


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

    fetch_calls = []

    def fake_fetch_creator_video_list(**kwargs):
        fetch_calls.append(kwargs)
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
        cost = tmp_path / "library" / "costs" / "demo.ledger.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        html.parent.mkdir(parents=True, exist_ok=True)
        cost.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("steps: []", encoding="utf-8")
        html.write_text("<html></html>", encoding="utf-8")
        cost.write_text(
            '{"kind":"cost_ledger","items":[{"kind":"qwen_vl","estimated_cost":{"amount":0.5,"currency":"USD"}}],"totals":{"USD":0.5}}',
            encoding="utf-8",
        )
        context = type("Context", (), {"html_path": html, "cost_ledger_path": cost})()
        return context, manifest

    monkeypatch.setattr("seed.creator_pipeline.fetch_creator_video_list", fake_fetch_creator_video_list)
    monkeypatch.setattr("seed.creator_pipeline.ingest_creator_videos", fake_ingest_creator_videos)
    monkeypatch.setattr("seed.creator_pipeline.run_video_pipeline", fake_run_video_pipeline)

    manifest, manifest_path = run_creator_pipeline(
        CreatorPipelineOptions(
            owner_name="demo",
            platform=Platform.bilibili,
            library_root=tmp_path / "library",
            owner_id="123",
            authorized=True,
            vision=False,
        )
    )

    assert manifest_path.exists()
    assert video_list.owner_query == "demo"
    assert fetch_calls[0]["owner_id"] == "123"
    assert manifest["video_runs"][0]["status"] == "completed"
    assert manifest["video_runs"][0]["html_path"].endswith("demo.video-dag.html")
    assert manifest["cost_ledger_path"].endswith("demo-creator.ledger.json")


def test_run_creator_pipeline_stops_when_budget_is_reached(tmp_path, monkeypatch):
    video_list = CreatorVideoList(
        platform=Platform.bilibili,
        owner_query="demo",
        owner="demo",
        provider="test",
        videos=[
            CreatorVideo(platform=Platform.bilibili, owner="demo", title="One", url="https://bili/1"),
            CreatorVideo(platform=Platform.bilibili, owner="demo", title="Two", url="https://bili/2"),
        ],
    )

    def fake_fetch_creator_video_list(**kwargs):
        return video_list

    def fake_ingest_creator_videos(*args, **kwargs):
        raw_dir = tmp_path / "library" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        first = raw_dir / "one.mp4"
        second = raw_dir / "two.mp4"
        first.write_bytes(b"one")
        second.write_bytes(b"two")
        return CreatorVideoIngestResult(
            selected=2,
            downloaded=2,
            recorded=2,
            items=[
                CreatorVideoIngestItem(url="https://bili/1", title="One", status="downloaded", raw_path=first),
                CreatorVideoIngestItem(url="https://bili/2", title="Two", status="downloaded", raw_path=second),
            ],
        )

    calls = []

    def fake_run_video_pipeline(options):
        calls.append(options.title)
        cost = tmp_path / "library" / "costs" / f"{options.title}.ledger.json"
        manifest = tmp_path / "library" / "runs" / f"{options.title}.video-pipeline.yaml"
        cost.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        cost.write_text(
            '{"kind":"cost_ledger","items":[{"kind":"qwen_vl","estimated_cost":{"amount":1.0,"currency":"USD"}}],"totals":{"USD":1.0}}',
            encoding="utf-8",
        )
        manifest.write_text("steps: []", encoding="utf-8")
        return type("Context", (), {"html_path": None, "cost_ledger_path": cost})(), manifest

    monkeypatch.setattr("seed.creator_pipeline.fetch_creator_video_list", fake_fetch_creator_video_list)
    monkeypatch.setattr("seed.creator_pipeline.ingest_creator_videos", fake_ingest_creator_videos)
    monkeypatch.setattr("seed.creator_pipeline.run_video_pipeline", fake_run_video_pipeline)

    manifest, _ = run_creator_pipeline(
        CreatorPipelineOptions(
            owner_name="demo",
            platform=Platform.bilibili,
            library_root=tmp_path / "library",
            authorized=True,
            max_estimated_cost=1.0,
        )
    )

    assert calls == ["One"]
    assert [run["status"] for run in manifest["video_runs"]] == ["completed", "skipped"]
    assert manifest["video_runs"][1]["reason"] == "budget_exceeded"


def test_run_creator_pipeline_builds_creator_outputs(tmp_path, monkeypatch):
    videos = [
        CreatorVideo(platform=Platform.bilibili, owner="demo", title=f"Video {index}", url=f"https://bili/{index}")
        for index in range(1, 4)
    ]
    video_list = CreatorVideoList(
        platform=Platform.bilibili,
        owner_query="demo",
        owner="demo",
        provider="test",
        videos=videos,
    )

    def fake_fetch_creator_video_list(**kwargs):
        return video_list

    def fake_ingest_creator_videos(*args, **kwargs):
        raw_dir = tmp_path / "library" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        items = []
        for index in range(1, 4):
            raw_path = raw_dir / f"video-{index}.mp4"
            raw_path.write_bytes(b"video")
            items.append(
                CreatorVideoIngestItem(
                    url=f"https://bili/{index}",
                    title=f"Video {index}",
                    status="downloaded",
                    raw_path=raw_path,
                )
            )
        return CreatorVideoIngestResult(selected=3, downloaded=3, recorded=3, items=items)

    def fake_run_video_pipeline(options):
        library = tmp_path / "library"
        semantics_path = library / "semantics" / f"{options.title}.video-semantics.md"
        manifest_path = library / "runs" / f"{options.title}.video-pipeline.yaml"
        html_path = library / "graphs" / f"{options.title}.video-dag.html"
        cost_path = library / "costs" / f"{options.title}.ledger.json"
        semantics_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        cost_path.parent.mkdir(parents=True, exist_ok=True)
        semantics_path.write_text(
            f"""## Metadata

- Title: {options.title}
- Platform: bilibili
- Owner: demo

## Semantic Summary

{options.title} summary.
""",
            encoding="utf-8",
        )
        manifest_path.write_text("steps: []", encoding="utf-8")
        html_path.write_text("<html></html>", encoding="utf-8")
        cost_path.write_text(
            '{"kind":"cost_ledger","items":[{"kind":"qwen_vl","estimated_cost":{"amount":0.1,"currency":"USD"}}],"totals":{"USD":0.1}}',
            encoding="utf-8",
        )
        return type("Context", (), {"html_path": html_path, "cost_ledger_path": cost_path})(), manifest_path

    def fake_run_creator_profile_aggregation(**kwargs):
        output_path = kwargs["output_path"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            """## Metadata

- Owner: demo
- Platform: bilibili
- Videos analyzed: 3
- Confidence: test

## Creator Summary

Demo creator profile.

## Agent Skills

- Skill name: demo-skill
- Trigger: demo trigger
- Procedure: demo procedure
- Inputs: demo inputs
- Outputs: demo outputs

## Pre-Checks

- Demo pre-check.

## Post-Task Reflection

- Demo reflection.
""",
            encoding="utf-8",
        )
        return output_path

    monkeypatch.setattr("seed.creator_pipeline.fetch_creator_video_list", fake_fetch_creator_video_list)
    monkeypatch.setattr("seed.creator_pipeline.ingest_creator_videos", fake_ingest_creator_videos)
    monkeypatch.setattr("seed.creator_pipeline.run_video_pipeline", fake_run_video_pipeline)
    monkeypatch.setattr(
        "seed.creator_pipeline.run_creator_profile_aggregation",
        fake_run_creator_profile_aggregation,
    )

    manifest, _ = run_creator_pipeline(
        CreatorPipelineOptions(
            owner_name="demo",
            platform=Platform.bilibili,
            library_root=tmp_path / "library",
            authorized=True,
            vision=False,
        )
    )

    assert [step["status"] for step in manifest["creator_steps"]] == ["completed", "completed", "completed"]
    assert (tmp_path / "library" / "distilled" / "demo.creator-profile.md").exists()
    assert (tmp_path / "library" / "checks" / "demo.agent-assets.review.json").exists()
    assert (tmp_path / "library" / "graphs" / "demo.creator-dag.html").exists()
