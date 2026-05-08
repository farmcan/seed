from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from seed.asr.providers import (
    DEFAULT_ASR_PROVIDER,
    default_max_upload_mb_for_provider,
    default_model_for_provider,
    transcribe_audio,
)
from seed.library import init_library, save_methodology, save_source_record, slugify
from seed.media import extract_audio, ensure_upload_size
from seed.models import Methodology, Platform, SourceRecord
from seed.sources.yt_dlp_adapter import download_url
from seed.summarizers.codex_runner import (
    DEFAULT_SKILL_PATH,
    run_codex_summary,
    summary_output_path,
)
from seed.transcripts import transcript_output_path, write_transcript_markdown


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
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    resolved_model = model or default_model_for_provider(provider)
    resolved_max_upload_mb = max_upload_mb or default_max_upload_mb_for_provider(provider)
    audio_path = extract_audio(media_path, root)
    ensure_upload_size(audio_path, max_upload_mb=resolved_max_upload_mb)
    text = transcribe_audio(
        audio_path,
        provider=provider,
        model=resolved_model,
        language=language,
        prompt=prompt,
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
    )
    console.print(f"extracted audio at {audio_path}")
    console.print(f"created transcript at {output_path}")


@app.command("summarize-transcript")
def summarize_transcript(
    transcript_path: Annotated[Path, typer.Argument(help="Transcript markdown file.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    owner: Annotated[str | None, typer.Option("--owner")] = None,
    platform: Annotated[str | None, typer.Option("--platform")] = None,
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
        model=codex_model,
        cwd=Path.cwd(),
        dry_run=dry_run,
    )
    console.print(f"created {'prompt' if dry_run else 'summary'} at {output_path}")
