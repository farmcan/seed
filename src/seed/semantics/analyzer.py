from __future__ import annotations

import subprocess
from pathlib import Path

from seed.library import init_library, slugify
from seed.summarizers.codex_runner import build_codex_exec_command
from seed.transcripts import read_transcript_text
from seed.vision.notes import read_visual_notes_text


DEFAULT_VIDEO_SEMANTICS_SKILL_PATH = Path("skills/video-semantics-analyzer/SKILL.md")


def video_semantics_output_path(
    *,
    library_root: Path,
    transcript_path: Path,
    title: str | None = None,
) -> Path:
    init_library(library_root)
    name = slugify(title or transcript_path.stem.removesuffix(".transcript"))
    return library_root / "semantics" / f"{name}.video-semantics.md"


def build_video_semantics_prompt(
    *,
    transcript_path: Path,
    skill_path: Path,
    visual_notes_path: Path | None = None,
    title: str | None = None,
    owner: str | None = None,
    platform: str | None = None,
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

    return f"""Use the following video semantics skill to fuse transcript and visual notes into a reusable semantic artifact.

Return only the final Markdown artifact. Do not modify files.

Metadata:
- Title: {title or transcript_path.stem}
- Owner: {owner or "unknown"}
- Platform: {platform or "unknown"}
- Transcript path: {transcript_path}
- Visual notes path: {visual_notes_path or "none"}

<skill>
{skill}
</skill>

<transcript>
{transcript}
</transcript>
{visual_section}
"""


def run_video_semantics_analysis(
    *,
    transcript_path: Path,
    output_path: Path,
    skill_path: Path = DEFAULT_VIDEO_SEMANTICS_SKILL_PATH,
    visual_notes_path: Path | None = None,
    title: str | None = None,
    owner: str | None = None,
    platform: str | None = None,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_video_semantics_prompt(
        transcript_path=transcript_path,
        skill_path=skill_path,
        visual_notes_path=visual_notes_path,
        title=title,
        owner=owner,
        platform=platform,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        output_path.write_text(prompt, encoding="utf-8")
        return output_path

    command = build_codex_exec_command(
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
    )
    subprocess.run(command, input=prompt, text=True, check=True)
    return output_path
