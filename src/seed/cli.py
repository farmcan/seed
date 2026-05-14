from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table

from seed.costs import (
    build_cost_ledger,
    build_qwen_vl_cost_item,
    cost_ledger_output_path,
    reserved_cost_item,
    reserved_codex_cost_item,
    video_cost_output_path,
    write_cost_ledger,
    write_video_cost_report,
)
from seed.asr.providers import (
    DEFAULT_ASR_PROVIDER,
    default_max_upload_mb_for_provider,
    default_model_for_provider,
)
from seed.agent_assets import (
    agent_asset_review_output_path,
    build_agent_asset_review,
    build_agent_assets_from_creator_profile,
    update_agent_asset_review,
    write_agent_asset_review,
    write_agent_assets,
)
from seed.asr.chunked import transcribe_audio_with_optional_chunks
from seed.books import (
    book_note_output_path,
    book_semantics_output_path,
    topic_profile_output_path,
    write_book_note,
    write_book_semantics,
    write_topic_profile,
)
from seed.claim_verification import (
    build_verified_claims_artifact,
    verified_claims_output_path,
    write_verified_claims_artifact,
)
from seed.creator_ingest import ingest_creator_videos as ingest_creator_videos_from_list
from seed.creator_pipeline import CreatorPipelineOptions, run_creator_pipeline
from seed.dag_export import (
    export_video_dag_html,
    relative_asset_base,
    video_dag_html_output_path,
)
from seed.dag_server import serve_video_dag
from seed.domains.finance import (
    build_finance_digest_artifact,
    enrich_finance_digest_with_prices,
    finance_digest_output_path,
    finance_signals_output_path,
    find_finance_signal_files,
    priced_finance_digest_output_path,
    run_finance_signals_extraction,
    write_finance_digest_artifact,
)
from seed.factcheck import build_claims_artifact, claims_output_path, write_claims_artifact
from seed.graphs.video_dag import (
    build_video_dag_graph,
    resolve_video_dag_artifacts,
    video_dag_output_path,
    write_video_dag_graph,
)
from seed.graphs.creator_dag import (
    build_creator_dag_graph,
    creator_dag_html_output_path,
    creator_dag_output_path,
    find_creator_asset_paths,
    write_creator_dag_graph,
)
from seed.library import (
    init_library,
    save_creator_video_list,
    save_methodology,
    save_source_record,
    slugify,
)
from seed.media import extract_audio
from seed.models import Methodology, Platform, SourceRecord
from seed.pipeline import VideoPipelineOptions, run_video_pipeline
from seed.reflections import ReflectionRecord, append_reflection_record, write_revision_suggestions
from seed.semantics.analyzer import (
    DEFAULT_VIDEO_SEMANTICS_SKILL_PATH,
    run_video_semantics_analysis,
    video_semantics_output_path,
)
from seed.semantics.aggregator import (
    DEFAULT_CREATOR_PROFILE_SKILL_PATH,
    DEFAULT_MIN_CREATOR_PROFILE_VIDEOS,
    creator_profile_output_path,
    find_video_semantics_files,
    run_creator_profile_aggregation,
    validate_creator_profile_video_count,
)
from seed.semantics.validation import (
    creator_profile_validation_output_path,
    validate_creator_profile,
    write_creator_profile_validation,
)
from seed.sources.creator_videos import fetch_creator_video_list
from seed.sources.yt_dlp_adapter import download_url
from seed.shorts import (
    DEFAULT_SCENE_THRESHOLD,
    DEFAULT_SHORT_MAX_SECONDS,
    build_frame_notes,
    build_motion_relations_artifact,
    build_short_video_profile,
    build_shots_artifact,
    frame_notes_output_path,
    load_frame_notes,
    motion_relations_output_path,
    short_profile_output_path,
    shots_output_path,
    write_frame_notes,
    write_motion_relations_artifact,
    write_short_video_profile,
    write_shots_artifact,
)
from seed.summarizers.codex_runner import (
    DEFAULT_SKILL_PATH,
    run_codex_summary,
    summary_output_path,
)
from seed.timeline import build_timeline_artifact, timeline_output_path, write_timeline_artifact
from seed.transcripts import transcript_output_path, write_transcript_markdown
from seed.vision.frames import extract_frames, load_frame_paths
from seed.vision.notes import visual_notes_output_path, write_visual_notes_markdown
from seed.vision.qwen_vl_provider import DEFAULT_QWEN_VL_MODEL, analyze_frames_with_qwen_vl_result


app = typer.Typer(help="Personal content-to-methodology distillation toolkit.")
console = Console()


@app.command("init-library")
def init_library_cmd(
    root: Annotated[Path, typer.Option("--root", help="Knowledge library root.")] = Path("library"),
) -> None:
    paths = init_library(root)
    for path in paths:
        console.print(f"created {path}")


@app.command("ingest-url")
def ingest_url(
    url: Annotated[str, typer.Argument(help="Content URL to record or ingest.")],
    platform: Annotated[Platform, typer.Option("--platform")],
    owner: Annotated[str, typer.Option("--owner")] = "unknown",
    title: Annotated[str | None, typer.Option("--title")] = None,
    authorized: Annotated[bool, typer.Option("--authorized")] = False,
    download: Annotated[bool, typer.Option("--download/--no-download")] = False,
    max_height: Annotated[int, typer.Option("--max-height", help="Maximum video height.")] = 360,
    max_filesize_mb: Annotated[
        int | None,
        typer.Option("--max-filesize-mb", help="Skip downloads larger than this size."),
    ] = 100,
    cookies_from_browser: Annotated[
        str | None,
        typer.Option(
            "--cookies-from-browser",
            help="Explicitly load cookies from a browser such as chrome, safari, or firefox.",
        ),
    ] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    if download and not authorized:
        raise typer.BadParameter("--download requires --authorized")

    result = None
    if download:
        result = download_url(
            url,
            platform=platform,
            library_root=root,
            max_height=max_height,
            max_filesize_mb=max_filesize_mb,
            cookies_from_browser=cookies_from_browser,
        )
        if result.owner and owner == "unknown":
            owner = result.owner
        if result.title and title is None:
            title = result.title

    record = SourceRecord(
        url=url,
        platform=platform,
        owner=owner,
        title=title,
        authorized=authorized,
        raw_path=result.raw_path if result else None,
        metadata_path=result.metadata_path if result else None,
        download_provider=result.provider if result else None,
        fallback_used=result.fallback_used if result else False,
        download_notes=result.notes if result else [],
    )
    path = save_source_record(root, record)
    console.print(f"recorded source at {path}")
    if result and result.raw_path:
        console.print(f"downloaded media at {result.raw_path}")
    if result and result.metadata_path:
        console.print(f"saved metadata at {result.metadata_path}")
    if result and result.fallback_used:
        console.print("download fallback was used")
    if result and result.notes:
        for note in result.notes:
            console.print(f"download note: {note}")


@app.command("fetch-creator-videos")
def fetch_creator_videos(
    owner_name: Annotated[str, typer.Argument(help="Creator, UP, or author name to search.")],
    platform: Annotated[Platform, typer.Option("--platform")],
    limit: Annotated[int, typer.Option("--limit", min=1, max=50)] = 20,
    owner_id: Annotated[
        str | None,
        typer.Option("--owner-id", help="Known platform owner id, e.g. Bilibili mid."),
    ] = None,
    cookies_from_browser: Annotated[
        str | None,
        typer.Option(
            "--cookies-from-browser",
            help="Explicitly load cookies from a browser such as chrome, safari, or firefox.",
        ),
    ] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    video_list = fetch_creator_video_list(
        platform=platform,
        owner_name=owner_name,
        limit=limit,
        owner_id=owner_id,
        cookies_from_browser=cookies_from_browser,
    )
    path = save_creator_video_list(root, video_list)
    console.print(f"found creator: {video_list.owner} ({video_list.owner_id or 'unknown id'})")
    console.print(f"collected {len(video_list.videos)} video candidates via {video_list.provider}")
    console.print(f"saved creator video list at {path}")
    if video_list.owner_url:
        console.print(f"creator URL: {video_list.owner_url}")
    for video in video_list.videos[:5]:
        title = video.title or video.video_id or video.url
        console.print(f"- {title}: {video.url}")


@app.command("ingest-creator-videos")
def ingest_creator_videos(
    list_path: Annotated[Path, typer.Argument(help="Path to *.creator-videos.yaml.")],
    authorized: Annotated[bool, typer.Option("--authorized")] = False,
    limit: Annotated[int | None, typer.Option("--limit", min=1)] = None,
    start_index: Annotated[int, typer.Option("--start-index", min=1)] = 1,
    skip_existing: Annotated[bool, typer.Option("--skip-existing/--no-skip-existing")] = True,
    download: Annotated[bool, typer.Option("--download/--no-download")] = True,
    max_height: Annotated[int, typer.Option("--max-height", help="Maximum video height.")] = 360,
    max_filesize_mb: Annotated[
        int | None,
        typer.Option("--max-filesize-mb", help="Skip downloads larger than this size."),
    ] = 100,
    cookies_from_browser: Annotated[
        str | None,
        typer.Option(
            "--cookies-from-browser",
            help="Explicitly load cookies from a browser such as chrome, safari, or firefox.",
        ),
    ] = None,
    keep_going: Annotated[bool, typer.Option("--keep-going/--stop-on-error")] = True,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    try:
        result = ingest_creator_videos_from_list(
            list_path,
            library_root=root,
            authorized=authorized,
            limit=limit,
            start_index=start_index,
            skip_existing=skip_existing,
            download=download,
            max_height=max_height,
            max_filesize_mb=max_filesize_mb,
            cookies_from_browser=cookies_from_browser,
            keep_going=keep_going,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

    console.print(
        "creator video ingest: "
        f"selected={result.selected}, downloaded={result.downloaded}, "
        f"recorded={result.recorded}, skipped={result.skipped}, failed={result.failed}"
    )
    for item in result.items:
        title = item.title or item.url
        console.print(f"- {item.status}: {title}")
        if item.raw_path:
            console.print(f"  media: {item.raw_path}")
        if item.source_record_path:
            console.print(f"  source: {item.source_record_path}")
        if item.error:
            console.print(f"  error: {item.error}")


@app.command("run-creator-pipeline")
def run_creator_pipeline_cmd(
    owner_name: Annotated[str, typer.Argument(help="Creator, UP, or author name to search.")],
    platform: Annotated[Platform, typer.Option("--platform")],
    limit: Annotated[int, typer.Option("--limit", min=1, max=50)] = 5,
    owner_id: Annotated[
        str | None,
        typer.Option("--owner-id", help="Known platform owner id, e.g. Bilibili mid."),
    ] = None,
    start_index: Annotated[int, typer.Option("--start-index", min=1)] = 1,
    published_after: Annotated[
        datetime | None,
        typer.Option("--published-after", help="Only keep creator videos published at or after this date."),
    ] = None,
    published_before: Annotated[
        datetime | None,
        typer.Option("--published-before", help="Only keep creator videos published before this date."),
    ] = None,
    authorized: Annotated[bool, typer.Option("--authorized")] = False,
    download: Annotated[bool, typer.Option("--download/--no-download")] = True,
    skip_existing: Annotated[bool, typer.Option("--skip-existing/--no-skip-existing")] = True,
    keep_going: Annotated[bool, typer.Option("--keep-going/--stop-on-error")] = True,
    max_height: Annotated[int, typer.Option("--max-height")] = 360,
    max_filesize_mb: Annotated[int | None, typer.Option("--max-filesize-mb")] = 100,
    cookies_from_browser: Annotated[str | None, typer.Option("--cookies-from-browser")] = None,
    vision: Annotated[bool, typer.Option("--vision/--no-vision")] = True,
    domain: Annotated[str | None, typer.Option("--domain", help="Optional domain lens, e.g. finance.")] = None,
    force: Annotated[bool, typer.Option("--force/--reuse-existing")] = False,
    max_estimated_cost: Annotated[
        float | None,
        typer.Option("--max-estimated-cost", help="Stop before the next video once this budget is reached."),
    ] = None,
    cost_currency: Annotated[str, typer.Option("--cost-currency")] = "USD",
    aggregate_profile: Annotated[
        bool,
        typer.Option("--aggregate-profile/--no-aggregate-profile"),
    ] = True,
    min_profile_videos: Annotated[int, typer.Option("--min-profile-videos", min=1)] = 3,
    generate_assets: Annotated[
        bool,
        typer.Option("--generate-assets/--no-generate-assets"),
    ] = True,
    build_creator_dag: Annotated[
        bool,
        typer.Option("--build-creator-dag/--no-build-creator-dag"),
    ] = True,
    export_creator_dag_html: Annotated[
        bool,
        typer.Option("--export-creator-dag-html/--no-export-creator-dag-html"),
    ] = True,
    codex_model: Annotated[str | None, typer.Option("--codex-model")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    manifest, manifest_path = run_creator_pipeline(
        CreatorPipelineOptions(
            owner_name=owner_name,
            platform=platform,
            library_root=root,
            owner_id=owner_id,
            limit=limit,
            start_index=start_index,
            published_after=published_after,
            published_before=published_before,
            authorized=authorized,
            download=download,
            skip_existing=skip_existing,
            keep_going=keep_going,
            max_height=max_height,
            max_filesize_mb=max_filesize_mb,
            cookies_from_browser=cookies_from_browser,
            vision=vision,
            domain=domain,
            force=force,
            max_estimated_cost=max_estimated_cost,
            cost_currency=cost_currency,
            aggregate_profile=aggregate_profile,
            min_profile_videos=min_profile_videos,
            generate_assets=generate_assets,
            build_creator_dag=build_creator_dag,
            export_creator_dag_html=export_creator_dag_html,
            codex_model=codex_model,
        )
    )
    console.print(f"created creator pipeline manifest at {manifest_path}")
    console.print(f"video runs: {len(manifest['video_runs'])}")
    for step in manifest.get("creator_steps", []):
        console.print(f"{step['name']}: {step['status']}")
        if step.get("reason"):
            console.print(f"  reason: {step['reason']}")
        for key in (
            "profile_path",
            "validation_path",
            "review_path",
            "graph_path",
            "html_path",
            "digest_path",
        ):
            if step.get(key):
                console.print(f"  {key}: {step[key]}")
    if manifest.get("cost_ledger_path"):
        console.print(f"created creator cost ledger at {manifest['cost_ledger_path']}")


@app.command("run-video-pipeline")
def run_video_pipeline_cmd(
    source: Annotated[str, typer.Argument(help="Video URL or local media path.")],
    platform: Annotated[Platform | None, typer.Option("--platform")] = None,
    owner: Annotated[str, typer.Option("--owner")] = "unknown",
    title: Annotated[str | None, typer.Option("--title")] = None,
    authorized: Annotated[bool, typer.Option("--authorized")] = False,
    download: Annotated[bool, typer.Option("--download/--no-download")] = True,
    force: Annotated[bool, typer.Option("--force/--skip-existing")] = False,
    max_height: Annotated[int, typer.Option("--max-height")] = 360,
    max_filesize_mb: Annotated[int | None, typer.Option("--max-filesize-mb")] = 100,
    cookies_from_browser: Annotated[str | None, typer.Option("--cookies-from-browser")] = None,
    asr_provider: Annotated[str, typer.Option("--asr-provider")] = DEFAULT_ASR_PROVIDER,
    asr_model: Annotated[str | None, typer.Option("--asr-model")] = None,
    language: Annotated[str | None, typer.Option("--language")] = None,
    max_upload_mb: Annotated[int | None, typer.Option("--max-upload-mb")] = None,
    chunk_audio: Annotated[bool, typer.Option("--chunk/--no-chunk")] = True,
    chunk_seconds: Annotated[int | None, typer.Option("--chunk-seconds", min=60)] = None,
    every_seconds: Annotated[int, typer.Option("--every-seconds", min=1)] = 5,
    max_frames: Annotated[int, typer.Option("--max-frames", min=1)] = 12,
    vision: Annotated[bool, typer.Option("--vision/--no-vision")] = True,
    vision_model: Annotated[str, typer.Option("--vision-model")] = DEFAULT_QWEN_VL_MODEL,
    short_form: Annotated[
        bool | None,
        typer.Option("--short-form/--long-form", help="Override automatic <=60s short-form detection."),
    ] = None,
    short_max_seconds: Annotated[float, typer.Option("--short-max-seconds", min=1)] = DEFAULT_SHORT_MAX_SECONDS,
    shot_detection: Annotated[bool, typer.Option("--shot-detection/--no-shot-detection")] = True,
    shot_threshold: Annotated[float, typer.Option("--shot-threshold", min=0.01, max=1.0)] = DEFAULT_SCENE_THRESHOLD,
    frame_notes: Annotated[bool, typer.Option("--frame-notes/--no-frame-notes")] = True,
    frame_mode: Annotated[str, typer.Option("--frame-mode", help="shot-keyframes, fps, or every-frame.")] = "shot-keyframes",
    frame_notes_fps: Annotated[float, typer.Option("--frame-notes-fps", min=0.1)] = 1.0,
    motion_relations: Annotated[bool, typer.Option("--motion-relations/--no-motion-relations")] = True,
    domain: Annotated[str | None, typer.Option("--domain", help="Optional domain lens, e.g. finance.")] = None,
    show_progress: Annotated[bool, typer.Option("--progress/--no-progress")] = True,
    codex_model: Annotated[str | None, typer.Option("--codex-model")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    options = VideoPipelineOptions(
        source=source,
        library_root=root,
        platform=platform,
        owner=owner,
        title=title,
        authorized=authorized,
        download=download,
        max_height=max_height,
        max_filesize_mb=max_filesize_mb,
        cookies_from_browser=cookies_from_browser,
        asr_provider=asr_provider,
        asr_model=asr_model,
        language=language,
        max_upload_mb=max_upload_mb,
        chunk_audio=chunk_audio,
        chunk_seconds=chunk_seconds,
        every_seconds=every_seconds,
        max_frames=max_frames,
        vision=vision,
        vision_model=vision_model,
        short_form=short_form,
        short_max_seconds=short_max_seconds,
        shot_detection=shot_detection,
        shot_threshold=shot_threshold,
        frame_notes=frame_notes,
        frame_mode=frame_mode,
        frame_notes_fps=frame_notes_fps,
        motion_relations=motion_relations,
        domain=domain,
        codex_model=codex_model,
        force=force,
    )
    if show_progress:
        context, manifest_path = run_video_pipeline_with_live_progress(options)
    else:
        context, manifest_path = run_video_pipeline(options)
    status_path = manifest_path.with_suffix(".status.json")
    console.print(f"created pipeline manifest at {manifest_path}")
    if status_path.exists():
        console.print(f"created pipeline status at {status_path}")
    if context.live_html_path:
        console.print(f"created live pipeline DAG HTML at {context.live_html_path}")
    if context.html_path:
        console.print(f"created standalone video DAG HTML at {context.html_path}")
    if context.semantics_path:
        console.print(f"created video semantics at {context.semantics_path}")
    if context.finance_signals_path:
        console.print(f"created finance signals at {context.finance_signals_path}")
    if context.cost_path:
        console.print(f"created cost report at {context.cost_path}")
    if context.cost_ledger_path:
        console.print(f"created cost ledger at {context.cost_ledger_path}")
    if context.short_profile_path:
        console.print(f"created short profile at {context.short_profile_path}")
    if context.shots_path:
        console.print(f"created shots artifact at {context.shots_path}")
    if context.frame_notes_path:
        console.print(f"created frame notes at {context.frame_notes_path}")
    if context.motion_relations_path:
        console.print(f"created motion relations at {context.motion_relations_path}")


def run_video_pipeline_with_live_progress(options: VideoPipelineOptions):
    rows: dict[str, dict[str, object]] = {}
    planned_steps: list[str] = []

    def callback(event: dict[str, object]) -> None:
        nonlocal planned_steps
        event_type = event.get("event")
        if event_type == "run_started":
            planned_steps = [str(step) for step in event.get("planned_steps", [])]
            rows.clear()
            for step in planned_steps:
                rows[step] = {
                    "step": step,
                    "status": "pending",
                    "duration_seconds": None,
                    "artifact_paths": [],
                    "cost_delta": None,
                }
        elif event_type in {"step_started", "step_finished"}:
            step = event.get("step")
            if isinstance(step, dict):
                rows[str(step["step"])] = step
        live.update(build_pipeline_progress_table(rows, planned_steps))

    options.progress_callback = callback
    with Live(build_pipeline_progress_table(rows, planned_steps), console=console, refresh_per_second=4) as live:
        return run_video_pipeline(options)


def build_pipeline_progress_table(rows: dict[str, dict[str, object]], planned_steps: list[str]) -> Table:
    table = Table(title="Video pipeline progress", expand=True)
    table.add_column("Step", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Duration", justify="right", no_wrap=True)
    table.add_column("Artifacts")
    table.add_column("Cost")
    for step in planned_steps:
        row = rows.get(step, {"step": step, "status": "pending"})
        table.add_row(
            step,
            status_label(str(row.get("status") or "pending")),
            format_duration(row.get("duration_seconds")),
            format_artifacts(row.get("artifact_paths")),
            format_cost(row.get("cost_delta")),
        )
    return table


def status_label(status: str) -> str:
    styles = {
        "pending": "[dim]pending[/dim]",
        "running": "[yellow]running[/yellow]",
        "completed": "[green]completed[/green]",
        "skipped": "[cyan]skipped[/cyan]",
        "failed": "[red]failed[/red]",
    }
    return styles.get(status, status)


def format_duration(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.1f}s"
    except (TypeError, ValueError):
        return "-"


def format_artifacts(value: object) -> str:
    if not isinstance(value, list) or not value:
        return ""
    names = [Path(str(path)).name for path in value[:2]]
    suffix = f" +{len(value) - 2}" if len(value) > 2 else ""
    return ", ".join(names) + suffix


def format_cost(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    totals = value.get("totals")
    if not isinstance(totals, dict) or not totals:
        return ""
    return ", ".join(f"{amount} {currency}" for currency, amount in totals.items())


@app.command("distill-note")
def distill_note(
    note_path: Annotated[Path, typer.Argument(help="Transcript or note markdown file.")],
    owner: Annotated[str, typer.Option("--owner")],
    topic: Annotated[str, typer.Option("--topic")],
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    text = note_path.read_text(encoding="utf-8")
    first_lines = [line.strip("- #") for line in text.splitlines() if line.strip()][:5]
    methodology = Methodology(
        id=slugify(f"{owner}-{topic}"),
        title=f"{owner} - {topic}",
        owner=owner,
        topic=topic,
        core_ideas=first_lines,
        agent_checks=["是否有明确适用场景？", "是否能转成可执行步骤？", "是否有反例或失效条件？"],
    )
    path = save_methodology(root, methodology)
    console.print(f"created draft methodology at {path}")


@app.command("import-book-note")
def import_book_note(
    note_path: Annotated[Path, typer.Argument(help="Local markdown/text note path.")],
    author: Annotated[str, typer.Option("--author")],
    title: Annotated[str, typer.Option("--title")],
    location: Annotated[str | None, typer.Option("--location")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    output_path = book_note_output_path(library_root=root, author=author, title=title)
    write_book_note(
        output_path,
        source_path=note_path,
        author=author,
        title=title,
        location=location,
    )
    console.print(f"created book note at {output_path}")


@app.command("analyze-book-note")
def analyze_book_note(
    note_path: Annotated[Path, typer.Argument(help="Path to *.book-note.md or a note file.")],
    author: Annotated[str, typer.Option("--author")],
    title: Annotated[str, typer.Option("--title")],
    topic: Annotated[str | None, typer.Option("--topic")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    output_path = book_semantics_output_path(library_root=root, author=author, title=title)
    write_book_semantics(
        output_path,
        note_path=note_path,
        author=author,
        title=title,
        topic=topic,
    )
    console.print(f"created book semantics at {output_path}")


@app.command("aggregate-topic")
def aggregate_topic(
    semantics_paths: Annotated[list[Path], typer.Argument(help="Book/video semantics files.")],
    topic: Annotated[str, typer.Option("--topic")],
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    output_path = topic_profile_output_path(library_root=root, topic=topic)
    write_topic_profile(output_path, topic=topic, semantics_paths=semantics_paths)
    console.print(f"created topic profile at {output_path}")


@app.command("transcribe-media")
def transcribe_media(
    media_path: Annotated[Path, typer.Argument(help="Downloaded video/audio file.")],
    provider: Annotated[str, typer.Option("--provider")] = DEFAULT_ASR_PROVIDER,
    model: Annotated[str | None, typer.Option("--model")] = None,
    language: Annotated[str | None, typer.Option("--language")] = None,
    title: Annotated[str | None, typer.Option("--title")] = None,
    prompt: Annotated[str | None, typer.Option("--prompt")] = None,
    max_upload_mb: Annotated[int | None, typer.Option("--max-upload-mb")] = None,
    chunk_audio: Annotated[bool, typer.Option("--chunk/--no-chunk")] = True,
    chunk_seconds: Annotated[
        int | None,
        typer.Option("--chunk-seconds", min=60, help="Override ASR chunk duration."),
    ] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    resolved_model = model or default_model_for_provider(provider)
    resolved_max_upload_mb = max_upload_mb or default_max_upload_mb_for_provider(provider)
    audio_path = extract_audio(media_path, root)
    text, chunks = transcribe_audio_with_optional_chunks(
        audio_path,
        provider=provider,
        model=resolved_model,
        language=language,
        prompt=prompt,
        max_upload_mb=resolved_max_upload_mb,
        chunk_audio=chunk_audio,
        chunk_seconds=chunk_seconds,
    )
    output_path = transcript_output_path(library_root=root, media_path=media_path, title=title)
    write_transcript_markdown(
        output_path,
        text=text,
        media_path=media_path,
        audio_path=audio_path,
        provider=provider,
        model=resolved_model,
        title=title,
        language=language,
        chunks=chunks,
    )
    console.print(f"extracted audio at {audio_path}")
    if chunks:
        console.print(f"transcribed {len(chunks)} audio chunks")
    console.print(f"created transcript at {output_path}")


@app.command("extract-frames")
def extract_frames_cmd(
    media_path: Annotated[Path, typer.Argument(help="Downloaded video file.")],
    every_seconds: Annotated[
        int,
        typer.Option("--every-seconds", min=1, help="Sample one frame every N seconds."),
    ] = 5,
    max_frames: Annotated[
        int,
        typer.Option("--max-frames", min=1, help="Maximum frames to extract."),
    ] = 12,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    frame_dir = extract_frames(
        media_path,
        root,
        every_seconds=every_seconds,
        max_frames=max_frames,
    )
    console.print(f"created frames at {frame_dir}")
    console.print(f"saved manifest at {frame_dir / 'frames.json'}")


@app.command("profile-short-video")
def profile_short_video(
    media_path: Annotated[Path, typer.Argument(help="Downloaded video file.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    platform: Annotated[str | None, typer.Option("--platform")] = None,
    short_max_seconds: Annotated[float, typer.Option("--short-max-seconds", min=1)] = DEFAULT_SHORT_MAX_SECONDS,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    resolved_title = title or media_path.stem
    profile = build_short_video_profile(
        media_path=media_path,
        title=resolved_title,
        platform=platform,
        short_max_seconds=short_max_seconds,
    )
    output_path = short_profile_output_path(library_root=root, title=resolved_title)
    write_short_video_profile(output_path, profile)
    console.print(f"created short profile at {output_path}")
    console.print(
        "short profile: "
        f"duration={profile.get('duration_seconds')}s, "
        f"fps={profile.get('fps')}, "
        f"vertical={profile.get('is_vertical')}, "
        f"is_short_form={profile.get('is_short_form')}"
    )


@app.command("detect-shots")
def detect_shots(
    media_path: Annotated[Path, typer.Argument(help="Downloaded video file.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    profile_path: Annotated[Path | None, typer.Option("--profile")] = None,
    threshold: Annotated[float, typer.Option("--threshold", min=0.01, max=1.0)] = DEFAULT_SCENE_THRESHOLD,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    resolved_title = title or media_path.stem
    if profile_path and profile_path.exists():
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    else:
        profile = build_short_video_profile(
            media_path=media_path,
            title=resolved_title,
            platform=None,
        )
    artifact = build_shots_artifact(
        media_path=media_path,
        title=resolved_title,
        profile=profile,
        library_root=root,
        threshold=threshold,
    )
    output_path = shots_output_path(library_root=root, title=resolved_title)
    write_shots_artifact(output_path, artifact)
    console.print(f"created shots artifact at {output_path}")
    console.print(f"shots: {len(artifact['shots'])}")


@app.command("build-frame-notes")
def build_frame_notes_cmd(
    media_path: Annotated[Path, typer.Argument(help="Downloaded video file.")],
    profile_path: Annotated[Path, typer.Option("--profile")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    shots_path_arg: Annotated[Path | None, typer.Option("--shots")] = None,
    frame_mode: Annotated[str, typer.Option("--frame-mode", help="shot-keyframes, fps, or every-frame.")] = "shot-keyframes",
    fps: Annotated[float, typer.Option("--fps", min=0.1)] = 1.0,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    resolved_title = title or media_path.stem
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    shots_artifact = (
        json.loads(shots_path_arg.read_text(encoding="utf-8"))
        if shots_path_arg and shots_path_arg.exists()
        else None
    )
    notes = build_frame_notes(
        media_path=media_path,
        title=resolved_title,
        profile=profile,
        shots_artifact=shots_artifact,
        library_root=root,
        frame_mode=frame_mode,
        fps=fps,
    )
    output_path = frame_notes_output_path(library_root=root, title=resolved_title)
    write_frame_notes(output_path, notes)
    console.print(f"created frame notes at {output_path}")
    console.print(f"frames: {len(notes)}")


@app.command("build-motion-relations")
def build_motion_relations_cmd(
    title: Annotated[str, typer.Option("--title", help="Video title for the motion relation artifact.")],
    profile_path: Annotated[Path, typer.Option("--profile")],
    frame_notes_path: Annotated[Path, typer.Option("--frame-notes")],
    shots_path_arg: Annotated[Path | None, typer.Option("--shots")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    frame_notes = load_frame_notes(frame_notes_path)
    shots_artifact = (
        json.loads(shots_path_arg.read_text(encoding="utf-8"))
        if shots_path_arg and shots_path_arg.exists()
        else None
    )
    artifact = build_motion_relations_artifact(
        title=title,
        profile=profile,
        shots_artifact=shots_artifact,
        frame_notes=frame_notes,
    )
    output_path = motion_relations_output_path(library_root=root, title=title)
    write_motion_relations_artifact(output_path, artifact)
    console.print(f"created motion relations at {output_path}")
    console.print(f"relations: {len(artifact['relations'])}")
    console.print(f"provider: {artifact['provider']}")


@app.command("analyze-frames")
def analyze_frames(
    frame_dir: Annotated[Path, typer.Argument(help="Directory containing frame_*.jpg files.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    model: Annotated[str, typer.Option("--model")] = DEFAULT_QWEN_VL_MODEL,
    prompt: Annotated[str | None, typer.Option("--prompt")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    frame_paths = load_frame_paths(frame_dir)
    if not frame_paths:
        raise typer.BadParameter("No frame_*.jpg files found in the frame directory.")

    result = analyze_frames_with_qwen_vl_result(frame_paths, model=model, prompt=prompt)
    output_path = visual_notes_output_path(library_root=root, source_path=frame_dir, title=title)
    write_visual_notes_markdown(
        output_path,
        analysis=result.analysis,
        frame_dir=frame_dir,
        frame_paths=frame_paths,
        provider="dashscope",
        model=model,
        title=title,
    )
    report_title = title or frame_dir.name
    cost_path = video_cost_output_path(library_root=root, title=report_title)
    cost_item = build_qwen_vl_cost_item(
        title=report_title,
        model=model,
        usage=result.usage,
        artifact_path=output_path,
        frame_count=len(frame_paths),
    )
    write_video_cost_report(
        cost_path,
        title=report_title,
        items=[cost_item, reserved_codex_cost_item()],
    )
    console.print(f"analyzed {len(frame_paths)} frames with {model}")
    console.print(f"created visual notes at {output_path}")
    console.print(f"created cost report at {cost_path}")
    console.print(
        "qwen-vl tokens: "
        f"input={result.usage.input_tokens}, output={result.usage.output_tokens}, "
        f"total={result.usage.total_tokens}"
    )
    console.print(
        "qwen-vl estimated cost: "
        f"{cost_item['estimated_cost']['amount']} {cost_item['estimated_cost']['currency']}"
    )


@app.command("build-cost-ledger")
def build_cost_ledger_cmd(
    title: Annotated[str, typer.Option("--title", help="Title for the ledger artifact.")],
    cost_report: Annotated[
        list[Path] | None,
        typer.Option("--cost-report", help="Input *.cost.json or *.ledger.json artifact."),
    ] = None,
    scope: Annotated[str, typer.Option("--scope")] = "video",
    reserve_asr: Annotated[bool, typer.Option("--reserve-asr/--no-reserve-asr")] = True,
    reserve_codex: Annotated[bool, typer.Option("--reserve-codex/--no-reserve-codex")] = True,
    reserve_search: Annotated[bool, typer.Option("--reserve-search/--no-reserve-search")] = True,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    reserved_items = []
    if reserve_asr:
        reserved_items.append(
            reserved_cost_item(kind="asr", provider="unknown", operation="transcribe-media")
        )
    if reserve_codex:
        reserved_items.append(reserved_codex_cost_item())
    if reserve_search:
        reserved_items.append(
            reserved_cost_item(kind="search", provider="unknown", operation="verify-claims")
        )
    ledger = build_cost_ledger(
        title=title,
        cost_report_paths=cost_report or [],
        scope=scope,
        reserved_items=reserved_items,
    )
    output_path = cost_ledger_output_path(library_root=root, title=title)
    write_cost_ledger(output_path, ledger)
    console.print(f"created cost ledger at {output_path}")
    console.print(f"totals: {ledger['totals']}")


@app.command("summarize-transcript")
def summarize_transcript(
    transcript_path: Annotated[Path, typer.Argument(help="Transcript markdown file.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    owner: Annotated[str | None, typer.Option("--owner")] = None,
    platform: Annotated[str | None, typer.Option("--platform")] = None,
    domain: Annotated[str | None, typer.Option("--domain", help="Optional domain lens, e.g. finance.")] = None,
    visual_notes: Annotated[
        Path | None,
        typer.Option("--visual-notes", help="Optional visual notes markdown from analyze-frames."),
    ] = None,
    skill_path: Annotated[Path, typer.Option("--skill-path")] = DEFAULT_SKILL_PATH,
    codex_model: Annotated[str | None, typer.Option("--codex-model")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    output_path = summary_output_path(
        library_root=root,
        transcript_path=transcript_path,
        title=title,
    )
    if dry_run:
        output_path = output_path.with_suffix(".prompt.md")
    run_codex_summary(
        transcript_path=transcript_path,
        output_path=output_path,
        skill_path=skill_path,
        title=title,
        owner=owner,
        platform=platform,
        domain=domain,
        visual_notes_path=visual_notes,
        model=codex_model,
        cwd=Path.cwd(),
        dry_run=dry_run,
    )
    console.print(f"created {'prompt' if dry_run else 'summary'} at {output_path}")


@app.command("analyze-video-semantics")
def analyze_video_semantics(
    transcript_path: Annotated[Path, typer.Argument(help="Transcript markdown file.")],
    visual_notes: Annotated[
        Path | None,
        typer.Option("--visual-notes", help="Optional visual notes markdown from analyze-frames."),
    ] = None,
    title: Annotated[str | None, typer.Option("--title")] = None,
    owner: Annotated[str | None, typer.Option("--owner")] = None,
    platform: Annotated[str | None, typer.Option("--platform")] = None,
    domain: Annotated[str | None, typer.Option("--domain", help="Optional domain lens, e.g. finance.")] = None,
    skill_path: Annotated[Path, typer.Option("--skill-path")] = DEFAULT_VIDEO_SEMANTICS_SKILL_PATH,
    codex_model: Annotated[str | None, typer.Option("--codex-model")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    output_path = video_semantics_output_path(
        library_root=root,
        transcript_path=transcript_path,
        title=title,
    )
    if dry_run:
        output_path = output_path.with_suffix(".prompt.md")
    run_video_semantics_analysis(
        transcript_path=transcript_path,
        output_path=output_path,
        skill_path=skill_path,
        visual_notes_path=visual_notes,
        title=title,
        owner=owner,
        platform=platform,
        domain=domain,
        model=codex_model,
        cwd=Path.cwd(),
        dry_run=dry_run,
    )
    console.print(f"created {'prompt' if dry_run else 'video semantics'} at {output_path}")


@app.command("extract-finance-signals")
def extract_finance_signals(
    semantics_path: Annotated[Path, typer.Argument(help="Video semantics markdown file.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    owner: Annotated[str | None, typer.Option("--owner")] = None,
    platform: Annotated[str | None, typer.Option("--platform")] = None,
    codex_model: Annotated[str | None, typer.Option("--codex-model")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    resolved_title = title or semantics_path.stem.removesuffix(".video-semantics")
    output_path = finance_signals_output_path(library_root=root, title=resolved_title)
    if dry_run:
        output_path = output_path.with_suffix(".prompt.md")
    run_finance_signals_extraction(
        semantics_path=semantics_path,
        output_path=output_path,
        title=resolved_title,
        owner=owner,
        platform=platform,
        model=codex_model,
        cwd=Path.cwd(),
        dry_run=dry_run,
    )
    console.print(f"created {'prompt' if dry_run else 'finance signals'} at {output_path}")


@app.command("build-finance-digest")
def build_finance_digest(
    owner: Annotated[str, typer.Option("--owner", help="Creator, UP, or author.")],
    platform: Annotated[str | None, typer.Option("--platform")] = None,
    signal_path: Annotated[
        list[Path] | None,
        typer.Option("--signal", help="Explicit *.finance-signals.json path. Can be repeated."),
    ] = None,
    published_after: Annotated[
        datetime | None,
        typer.Option("--published-after", help="Only include records published at or after this date."),
    ] = None,
    published_before: Annotated[
        datetime | None,
        typer.Option("--published-before", help="Only include records published before this date."),
    ] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    paths = signal_path or find_finance_signal_files(library_root=root, owner=owner)
    if not paths:
        raise typer.BadParameter(f"No finance signal files found for owner: {owner}")
    artifact = build_finance_digest_artifact(
        signal_paths=paths,
        owner=owner,
        platform=platform,
        published_after=published_after,
        published_before=published_before,
    )
    output_path = finance_digest_output_path(
        library_root=root,
        owner=owner,
        published_after=published_after,
        published_before=published_before,
    )
    write_finance_digest_artifact(output_path, artifact)
    console.print(f"created finance digest at {output_path}")
    console.print(f"videos: {artifact['videos_analyzed']}, recommendations: {artifact['totals']['recommendations']}")


@app.command("enrich-finance-prices")
def enrich_finance_prices(
    digest_path: Annotated[Path, typer.Argument(help="Path to *.finance-digest.json.")],
    ticker_map: Annotated[
        list[str],
        typer.Option("--ticker-map", help="Instrument to ticker mapping, e.g. --ticker-map AI=nvda.us."),
    ],
    benchmark_ticker: Annotated[str | None, typer.Option("--benchmark")] = None,
    provider: Annotated[str, typer.Option("--provider")] = "stooq",
    output_path: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    digest = json.loads(digest_path.read_text(encoding="utf-8"))
    mapping = parse_ticker_map(ticker_map)
    enriched = enrich_finance_digest_with_prices(
        digest,
        ticker_map=mapping,
        benchmark_ticker=benchmark_ticker,
        provider=provider,
    )
    resolved_output = output_path or priced_finance_digest_output_path(digest_path=digest_path)
    write_finance_digest_artifact(resolved_output, enriched)
    console.print(f"created priced finance digest at {resolved_output}")
    console.print(f"priced recommendations: {enriched['totals'].get('priced_recommendations', 0)}")


def parse_ticker_map(values: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise typer.BadParameter(f"Invalid --ticker-map value: {value}. Expected NAME=TICKER.")
        name, ticker = value.split("=", 1)
        mapping[name] = ticker
        mapping[name.casefold()] = ticker
    return mapping


@app.command("build-timeline")
def build_timeline(
    title: Annotated[str, typer.Option("--title", help="Video title for the timeline artifact.")],
    transcript_path: Annotated[Path | None, typer.Option("--transcript")] = None,
    frame_dir: Annotated[Path | None, typer.Option("--frames")] = None,
    visual_notes: Annotated[Path | None, typer.Option("--visual-notes")] = None,
    semantics_path: Annotated[Path | None, typer.Option("--semantics")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    artifact = build_timeline_artifact(
        title=title,
        transcript_path=transcript_path,
        frame_dir=frame_dir,
        visual_notes_path=visual_notes,
        semantics_path=semantics_path,
    )
    output_path = timeline_output_path(
        library_root=root,
        title=title,
        transcript_path=transcript_path,
    )
    write_timeline_artifact(output_path, artifact)
    console.print(f"created timeline artifact at {output_path}")
    console.print(f"events: {len(artifact['events'])}, uncertainties: {len(artifact['uncertainties'])}")


@app.command("extract-claims")
def extract_claims(
    semantics_path: Annotated[Path, typer.Argument(help="Video semantics markdown file.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    artifact = build_claims_artifact(semantics_path=semantics_path, title=title)
    output_path = claims_output_path(
        library_root=root,
        title=title,
        semantics_path=semantics_path,
    )
    write_claims_artifact(output_path, artifact)
    console.print(f"created claims artifact at {output_path}")
    console.print(f"claims: {len(artifact['claims'])}")


@app.command("verify-claims")
def verify_claims(
    claims_path: Annotated[Path, typer.Argument(help="Path to *.claims.json.")],
    evidence_url: Annotated[
        list[str] | None,
        typer.Option("--evidence-url", help="External source URL to record for verification."),
    ] = None,
    fetch_sources: Annotated[bool, typer.Option("--fetch-sources/--no-fetch-sources")] = True,
    title: Annotated[str | None, typer.Option("--title")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    artifact = build_verified_claims_artifact(
        claims_path=claims_path,
        evidence_urls=evidence_url or [],
        fetch_sources=fetch_sources,
    )
    output_path = verified_claims_output_path(
        library_root=root,
        claims_path=claims_path,
        title=title,
    )
    write_verified_claims_artifact(output_path, artifact)
    console.print(f"created verified claims artifact at {output_path}")
    console.print(f"claims: {len(artifact['claims'])}, sources: {len(artifact['sources'])}")


@app.command("aggregate-owner")
def aggregate_owner(
    owner: Annotated[str, typer.Option("--owner", help="Creator, UP, or author to aggregate.")],
    platform: Annotated[str | None, typer.Option("--platform")] = None,
    domain: Annotated[str | None, typer.Option("--domain", help="Optional domain lens, e.g. finance.")] = None,
    semantics_dir: Annotated[
        Path | None,
        typer.Option("--semantics-dir", help="Override directory containing *.video-semantics.md."),
    ] = None,
    skill_path: Annotated[Path, typer.Option("--skill-path")] = DEFAULT_CREATOR_PROFILE_SKILL_PATH,
    min_videos: Annotated[int, typer.Option("--min-videos", min=1)] = DEFAULT_MIN_CREATOR_PROFILE_VIDEOS,
    codex_model: Annotated[str | None, typer.Option("--codex-model")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    semantics_paths = find_video_semantics_files(
        library_root=root,
        owner=owner,
        semantics_dir=semantics_dir,
    )
    if not semantics_paths:
        raise typer.BadParameter(f"No video semantics files found for owner: {owner}")
    try:
        validate_creator_profile_video_count(semantics_paths, min_videos=min_videos)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error

    output_path = creator_profile_output_path(library_root=root, owner=owner)
    if dry_run:
        output_path = output_path.with_suffix(".prompt.md")
    run_creator_profile_aggregation(
        semantics_paths=semantics_paths,
        output_path=output_path,
        skill_path=skill_path,
        owner=owner,
        platform=platform,
        domain=domain,
        model=codex_model,
        cwd=Path.cwd(),
        dry_run=dry_run,
    )
    if not dry_run:
        validation = validate_creator_profile(output_path, owner=owner)
        validation_path = creator_profile_validation_output_path(library_root=root, owner=owner)
        write_creator_profile_validation(validation_path, validation)
        console.print(f"created creator profile validation at {validation_path}")
        console.print(f"validation status: {validation['status']}")
    console.print(f"aggregated {len(semantics_paths)} video semantics files")
    console.print(f"created {'prompt' if dry_run else 'creator profile'} at {output_path}")


@app.command("validate-creator-profile")
def validate_creator_profile_cmd(
    profile_path: Annotated[Path, typer.Argument(help="Path to *.creator-profile.md.")],
    owner: Annotated[str | None, typer.Option("--owner")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    resolved_owner = owner or profile_path.stem.removesuffix(".creator-profile")
    report = validate_creator_profile(profile_path, owner=resolved_owner)
    output_path = creator_profile_validation_output_path(library_root=root, owner=resolved_owner)
    write_creator_profile_validation(output_path, report)
    console.print(f"created creator profile validation at {output_path}")
    console.print(f"status: {report['status']}, findings: {len(report['findings'])}")


@app.command("build-creator-dag")
def build_creator_dag(
    owner: Annotated[str, typer.Option("--owner", help="Creator, UP, or author to graph.")],
    semantics_dir: Annotated[Path | None, typer.Option("--semantics-dir")] = None,
    creator_profile: Annotated[Path | None, typer.Option("--creator-profile")] = None,
    export_html: Annotated[bool, typer.Option("--export-html/--no-export-html")] = True,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    semantics_paths = find_video_semantics_files(
        library_root=root,
        owner=owner,
        semantics_dir=semantics_dir,
    )
    if not semantics_paths:
        raise typer.BadParameter(f"No video semantics files found for owner: {owner}")
    assets = find_creator_asset_paths(library_root=root, owner=owner)
    graph = build_creator_dag_graph(
        owner=owner,
        semantics_paths=semantics_paths,
        library_root=root,
        creator_profile_path=creator_profile or assets["creator_profile_path"],
        skill_paths=assets["skill_paths"],
        check_paths=assets["check_paths"],
        validation_path=assets["validation_path"],
        cost_ledger_path=assets["cost_ledger_path"],
    )
    output_path = creator_dag_output_path(library_root=root, owner=owner)
    write_creator_dag_graph(output_path, graph)
    console.print(f"created creator DAG graph at {output_path}")
    if export_html:
        html_path = creator_dag_html_output_path(graph_path=output_path)
        export_video_dag_html(
            graph_path=output_path,
            output_path=html_path,
            asset_base=relative_asset_base(output_path=html_path, repo_root=Path.cwd()),
        )
        console.print(f"created standalone creator DAG HTML at {html_path}")


@app.command("generate-agent-assets")
def generate_agent_assets(
    profile_path: Annotated[Path, typer.Argument(help="Creator profile markdown file.")],
    owner: Annotated[str | None, typer.Option("--owner")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    resolved_owner = owner or profile_path.stem.removesuffix(".creator-profile")
    assets = build_agent_assets_from_creator_profile(
        profile_path=profile_path,
        owner=resolved_owner,
    )
    paths = write_agent_assets(
        library_root=root,
        owner=resolved_owner,
        assets=assets,
    )
    console.print(f"created skill draft at {paths['skill']}")
    console.print(f"created pre-check at {paths['pre_check']}")
    console.print(f"created post-task reflection at {paths['post_task_reflection']}")
    console.print(f"created agent asset review at {agent_asset_review_output_path(library_root=root, owner=resolved_owner)}")


@app.command("review-agent-assets")
def review_agent_assets(
    owner: Annotated[str, typer.Option("--owner", help="Creator, UP, or author.")],
    status: Annotated[str, typer.Option("--status", help="draft, reviewed, installed, or deprecated.")],
    asset_path: Annotated[
        list[Path] | None,
        typer.Option("--asset", help="Only update selected asset path. Repeat for multiple assets."),
    ] = None,
    reviewer: Annotated[str | None, typer.Option("--reviewer")] = None,
    note: Annotated[list[str] | None, typer.Option("--note")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    review_path = agent_asset_review_output_path(library_root=root, owner=owner)
    if not review_path.exists():
        assets = find_creator_asset_paths(library_root=root, owner=owner)
        skill_paths = list(assets["skill_paths"])
        check_paths = list(assets["check_paths"])
        asset_paths = {
            "skill": skill_paths[0] if skill_paths else None,
            "pre_check": next((path for path in check_paths if "pre-check" in path.name), None),
            "post_task_reflection": next(
                (path for path in check_paths if "post-task-reflection" in path.name),
                None,
            ),
        }
        review = build_agent_asset_review(
            owner=owner,
            asset_paths={key: path for key, path in asset_paths.items() if path is not None},
        )
        write_agent_asset_review(review_path, review)
    review = update_agent_asset_review(
        review_path=review_path,
        status=status,
        asset_paths=asset_path or [],
        reviewer=reviewer,
        notes=note or [],
    )
    write_agent_asset_review(review_path, review)
    console.print(f"updated agent asset review at {review_path}")
    console.print(f"status: {review['status']}, assets: {len(review.get('assets', []))}")


@app.command("record-reflection")
def record_reflection(
    owner: Annotated[str, typer.Option("--owner", help="Creator, UP, or author.")],
    task: Annotated[str, typer.Option("--task", help="Task where the asset was used.")],
    outcome: Annotated[str, typer.Option("--outcome", help="Observed outcome.")],
    asset_path: Annotated[Path | None, typer.Option("--asset")] = None,
    worked: Annotated[list[str] | None, typer.Option("--worked")] = None,
    failed: Annotated[list[str] | None, typer.Option("--failed")] = None,
    revise: Annotated[list[str] | None, typer.Option("--revise")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    path = append_reflection_record(
        library_root=root,
        record=ReflectionRecord(
            owner=owner,
            task=task,
            asset_path=asset_path,
            outcome=outcome,
            worked=worked or [],
            failed=failed or [],
            revise=revise or [],
        ),
    )
    console.print(f"recorded reflection at {path}")


@app.command("suggest-revisions")
def suggest_revisions(
    owner: Annotated[str, typer.Option("--owner", help="Creator, UP, or author.")],
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    path = write_revision_suggestions(library_root=root, owner=owner)
    console.print(f"created revision suggestions at {path}")


@app.command("build-video-dag")
def build_video_dag(
    title: Annotated[str, typer.Option("--title", help="Video title for the graph artifact.")],
    owner: Annotated[str | None, typer.Option("--owner")] = None,
    platform: Annotated[str | None, typer.Option("--platform")] = None,
    source_path: Annotated[Path | None, typer.Option("--source-path")] = None,
    audio_path: Annotated[Path | None, typer.Option("--audio")] = None,
    transcript_path: Annotated[Path | None, typer.Option("--transcript")] = None,
    frame_dir: Annotated[Path | None, typer.Option("--frames")] = None,
    visual_notes: Annotated[Path | None, typer.Option("--visual-notes")] = None,
    semantics_path: Annotated[Path | None, typer.Option("--semantics")] = None,
    finance_signals: Annotated[Path | None, typer.Option("--finance-signals")] = None,
    timeline_path: Annotated[Path | None, typer.Option("--timeline")] = None,
    claims_path: Annotated[Path | None, typer.Option("--claims")] = None,
    cost_path: Annotated[Path | None, typer.Option("--cost")] = None,
    creator_profile: Annotated[Path | None, typer.Option("--creator-profile")] = None,
    short_profile: Annotated[Path | None, typer.Option("--short-profile")] = None,
    shots_path: Annotated[Path | None, typer.Option("--shots")] = None,
    frame_notes_path: Annotated[Path | None, typer.Option("--frame-notes")] = None,
    motion_relations_path: Annotated[Path | None, typer.Option("--motion-relations")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    artifacts = resolve_video_dag_artifacts(
        library_root=root,
        title=title,
        source_path=source_path,
        audio_path=audio_path,
        transcript_path=transcript_path,
        frame_dir=frame_dir,
        visual_notes_path=visual_notes,
        semantics_path=semantics_path,
        finance_signals_path=finance_signals,
        timeline_path=timeline_path,
        claims_path=claims_path,
        cost_path=cost_path,
        creator_profile_path=creator_profile,
        short_profile_path=short_profile,
        shots_path=shots_path,
        frame_notes_path=frame_notes_path,
        motion_relations_path=motion_relations_path,
    )
    graph = build_video_dag_graph(
        title=title,
        owner=owner,
        platform=platform,
        source_path=artifacts["source_path"],
        audio_path=artifacts["audio_path"],
        transcript_path=artifacts["transcript_path"],
        frame_dir=artifacts["frame_dir"],
        visual_notes_path=artifacts["visual_notes_path"],
        semantics_path=artifacts["semantics_path"],
        finance_signals_path=artifacts["finance_signals_path"],
        timeline_path=artifacts["timeline_path"],
        claims_path=artifacts["claims_path"],
        cost_path=artifacts["cost_path"],
        creator_profile_path=artifacts["creator_profile_path"],
        short_profile_path=artifacts["short_profile_path"],
        shots_path=artifacts["shots_path"],
        frame_notes_path=artifacts["frame_notes_path"],
        motion_relations_path=artifacts["motion_relations_path"],
    )
    output_path = video_dag_output_path(library_root=root, title=title)
    write_video_dag_graph(output_path, graph)
    html_path = video_dag_html_output_path(graph_path=output_path)
    export_video_dag_html(
        graph_path=output_path,
        output_path=html_path,
        asset_base=relative_asset_base(output_path=html_path, repo_root=Path.cwd()),
    )
    graph_url = f"{(Path.cwd() / 'tools/video-dag-canvas.html').as_uri()}?graph={quote('../' + str(output_path))}"
    console.print(f"created video DAG graph at {output_path}")
    console.print(f"created standalone video DAG HTML at {html_path}")
    console.print("open the standalone HTML for review; use serve-video-dag only for debugging")
    console.print(f"graph URL: {graph_url}")


@app.command("serve-video-dag")
def serve_video_dag_cmd(
    graph_path: Annotated[Path, typer.Argument(help="Path to *.video-dag.json.")],
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", min=0)] = 8765,
    open_browser: Annotated[bool, typer.Option("--open/--no-open")] = True,
) -> None:
    serve_video_dag(
        graph_path=graph_path,
        repo_root=Path.cwd(),
        host=host,
        port=port,
        open_browser=open_browser,
    )


@app.command("export-video-dag-html")
def export_video_dag_html_cmd(
    graph_path: Annotated[Path, typer.Argument(help="Path to *.video-dag.json.")],
    output_path: Annotated[Path | None, typer.Option("--output")] = None,
    asset_base: Annotated[
        str | None,
        typer.Option("--asset-base", help="Relative base used to resolve library media paths."),
    ] = None,
) -> None:
    resolved_output = output_path or video_dag_html_output_path(graph_path=graph_path)
    resolved_asset_base = asset_base or relative_asset_base(
        output_path=resolved_output,
        repo_root=Path.cwd(),
    )
    path = export_video_dag_html(
        graph_path=graph_path,
        output_path=resolved_output,
        asset_base=resolved_asset_base,
    )
    console.print(f"created standalone video DAG HTML at {path}")
    console.print(f"asset base: {resolved_asset_base}")
