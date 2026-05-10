from __future__ import annotations

from pathlib import Path

from seed.agents.codex import run_codex_prompt
from seed.library import init_library, slugify
from seed.transcripts import read_transcript_text
from seed.vision.notes import read_visual_notes_text


DEFAULT_SKILL_PATH = Path("skills/video-note-summarizer/SKILL.md")


def summary_output_path(
    *,
    library_root: Path,
    transcript_path: Path,
    title: str | None = None,
) -> Path:
    init_library(library_root)
    name = slugify(title or transcript_path.stem.removesuffix(".transcript"))
    return library_root / "notes" / f"{name}.summary.md"


def build_summary_prompt(
    *,
    transcript_path: Path,
    skill_path: Path,
    title: str | None = None,
    owner: str | None = None,
    platform: str | None = None,
    visual_notes_path: Path | None = None,
) -> str:
    transcript = read_transcript_text(transcript_path)
    skill = skill_path.read_text(encoding="utf-8")
    visual_section = ""
    if visual_notes_path:
        visual_notes = read_visual_notes_text(visual_notes_path)
        visual_section = f"""
<visual_notes path="{visual_notes_path}">
{visual_notes}
</visual_notes>
"""
    return f"""Use the following video summarization skill to summarize the transcript.

If visual notes are provided, combine the transcript and visual notes. Return only the final Markdown summary. Do not modify files.

Metadata:
- Title: {title or transcript_path.stem}
- Owner: {owner or "unknown"}
- Platform: {platform or "unknown"}
- Transcript path: {transcript_path}

<skill>
{skill}
</skill>

<transcript>
{transcript}
</transcript>
{visual_section}
"""


def run_codex_summary(
    *,
    transcript_path: Path,
    output_path: Path,
    skill_path: Path = DEFAULT_SKILL_PATH,
    title: str | None = None,
    owner: str | None = None,
    platform: str | None = None,
    visual_notes_path: Path | None = None,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_summary_prompt(
        transcript_path=transcript_path,
        skill_path=skill_path,
        title=title,
        owner=owner,
        platform=platform,
        visual_notes_path=visual_notes_path,
    )
    return run_codex_prompt(
        prompt=prompt,
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
        dry_run=dry_run,
    )
