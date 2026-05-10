from __future__ import annotations

from pathlib import Path
from typing import Annotated
from urllib.parse import quote

import typer
from rich.console import Console

from seed.asr.providers import (
    DEFAULT_ASR_PROVIDER,
    default_max_upload_mb_for_provider,
    default_model_for_provider,
)
from seed.asr.chunked import transcribe_audio_with_optional_chunks
from seed.creator_ingest import ingest_creator_videos as ingest_creator_videos_from_list
from seed.graphs.video_dag import build_video_dag_graph, video_dag_output_path, write_video_dag_graph
from seed.library import (
    init_library,
    save_creator_video_list,
    save_methodology,
    save_source_record,
    slugify,
)
from seed.media import extract_audio
from seed.models import Methodology, Platform, SourceRecord
from seed.semantics.analyzer import (
    DEFAULT_VIDEO_SEMANTICS_SKILL_PATH,
    run_video_semantics_analysis,
    video_semantics_output_path,
)
from seed.semantics.aggregator import (
    DEFAULT_CREATOR_PROFILE_SKILL_PATH,
    creator_profile_output_path,
    find_video_semantics_files,
    run_creator_profile_aggregation,
)
from seed.sources.creator_videos import fetch_creator_video_list
from seed.sources.yt_dlp_adapter import download_url
from seed.summarizers.codex_runner import (
    DEFAULT_SKILL_PATH,
    run_codex_summary,
    summary_output_path,
)
from seed.transcripts import transcript_output_path, write_transcript_markdown
from seed.vision.frames import extract_frames, load_frame_paths
from seed.vision.notes import visual_notes_output_path, write_visual_notes_markdown
from seed.vision.qwen_vl_provider import DEFAULT_QWEN_VL_MODEL, analyze_frames_with_qwen_vl


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
    )
    path = save_source_record(root, record)
    console.print(f"recorded source at {path}")
    if result and result.raw_path:
        console.print(f"downloaded media at {result.raw_path}")
    if result and result.metadata_path:
        console.print(f"saved metadata at {result.metadata_path}")


@app.command("fetch-creator-videos")
def fetch_creator_videos(
    owner_name: Annotated[str, typer.Argument(help="Creator, UP, or author name to search.")],
    platform: Annotated[Platform, typer.Option("--platform")],
    limit: Annotated[int, typer.Option("--limit", min=1, max=50)] = 20,
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

    analysis = analyze_frames_with_qwen_vl(frame_paths, model=model, prompt=prompt)
    output_path = visual_notes_output_path(library_root=root, source_path=frame_dir, title=title)
    write_visual_notes_markdown(
        output_path,
        analysis=analysis,
        frame_dir=frame_dir,
        frame_paths=frame_paths,
        provider="dashscope",
        model=model,
        title=title,
    )
    console.print(f"analyzed {len(frame_paths)} frames with {model}")
    console.print(f"created visual notes at {output_path}")


@app.command("summarize-transcript")
def summarize_transcript(
    transcript_path: Annotated[Path, typer.Argument(help="Transcript markdown file.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    owner: Annotated[str | None, typer.Option("--owner")] = None,
    platform: Annotated[str | None, typer.Option("--platform")] = None,
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
        model=codex_model,
        cwd=Path.cwd(),
        dry_run=dry_run,
    )
    console.print(f"created {'prompt' if dry_run else 'video semantics'} at {output_path}")


@app.command("aggregate-owner")
def aggregate_owner(
    owner: Annotated[str, typer.Option("--owner", help="Creator, UP, or author to aggregate.")],
    platform: Annotated[str | None, typer.Option("--platform")] = None,
    semantics_dir: Annotated[
        Path | None,
        typer.Option("--semantics-dir", help="Override directory containing *.video-semantics.md."),
    ] = None,
    skill_path: Annotated[Path, typer.Option("--skill-path")] = DEFAULT_CREATOR_PROFILE_SKILL_PATH,
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

    output_path = creator_profile_output_path(library_root=root, owner=owner)
    if dry_run:
        output_path = output_path.with_suffix(".prompt.md")
    run_creator_profile_aggregation(
        semantics_paths=semantics_paths,
        output_path=output_path,
        skill_path=skill_path,
        owner=owner,
        platform=platform,
        model=codex_model,
        cwd=Path.cwd(),
        dry_run=dry_run,
    )
    console.print(f"aggregated {len(semantics_paths)} video semantics files")
    console.print(f"created {'prompt' if dry_run else 'creator profile'} at {output_path}")


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
    creator_profile: Annotated[Path | None, typer.Option("--creator-profile")] = None,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    graph = build_video_dag_graph(
        title=title,
        owner=owner,
        platform=platform,
        source_path=source_path,
        audio_path=audio_path,
        transcript_path=transcript_path,
        frame_dir=frame_dir,
        visual_notes_path=visual_notes,
        semantics_path=semantics_path,
        creator_profile_path=creator_profile,
    )
    output_path = video_dag_output_path(library_root=root, title=title)
    write_video_dag_graph(output_path, graph)
    graph_url = f"{(Path.cwd() / 'tools/video-dag-canvas.html').as_uri()}?graph={quote('../' + str(output_path))}"
    console.print(f"created video DAG graph at {output_path}")
    console.print("open tools/video-dag-canvas.html and import the graph JSON")
    console.print(f"graph URL: {graph_url}")
