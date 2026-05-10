from __future__ import annotations

import subprocess
from pathlib import Path

from seed.library import init_library, slugify
from seed.summarizers.codex_runner import build_codex_exec_command


DEFAULT_CREATOR_PROFILE_SKILL_PATH = Path("skills/creator-profile-aggregator/SKILL.md")


def creator_profile_output_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "distilled" / f"{slugify(owner)}.creator-profile.md"


def find_video_semantics_files(
    *,
    library_root: Path,
    owner: str,
    semantics_dir: Path | None = None,
) -> list[Path]:
    directory = semantics_dir or library_root / "semantics"
    if not directory.exists():
        return []
    paths = sorted(directory.glob("*.video-semantics.md"))
    return [path for path in paths if semantics_matches_owner(path.read_text(encoding="utf-8"), owner)]


def semantics_matches_owner(text: str, owner: str) -> bool:
    target = owner.casefold()
    for line in text.splitlines():
        normalized = line.strip().casefold()
        if normalized.startswith("- owner:") and normalized.removeprefix("- owner:").strip() == target:
            return True
        if normalized.startswith("owner:") and normalized.removeprefix("owner:").strip() == target:
            return True
    return False


def build_creator_profile_prompt(
    *,
    semantics_paths: list[Path],
    skill_path: Path,
    owner: str,
    platform: str | None = None,
) -> str:
    skill = skill_path.read_text(encoding="utf-8")
    semantics_sections = "\n".join(
        f"""<video_semantics path="{path}">
{path.read_text(encoding="utf-8").strip()}
</video_semantics>"""
        for path in semantics_paths
    )
    return f"""Use the following creator profile aggregation skill to synthesize multiple video semantics artifacts.

Return only the final Markdown creator profile. Do not modify files.

Metadata:
- Owner: {owner}
- Platform: {platform or "unknown"}
- Video semantics count: {len(semantics_paths)}

<skill>
{skill}
</skill>

{semantics_sections}
"""


def run_creator_profile_aggregation(
    *,
    semantics_paths: list[Path],
    output_path: Path,
    skill_path: Path = DEFAULT_CREATOR_PROFILE_SKILL_PATH,
    owner: str,
    platform: str | None = None,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    if not semantics_paths:
        raise ValueError("At least one video semantics file is required")

    prompt = build_creator_profile_prompt(
        semantics_paths=semantics_paths,
        skill_path=skill_path,
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
