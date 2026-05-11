from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify
from seed.markdown import find_markdown_field, read_markdown_body

AGENT_ASSET_REVIEW_STATUSES = {"draft", "reviewed", "installed", "deprecated"}


def skill_output_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "skills" / slugify(owner) / "SKILL.md"


def precheck_output_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "checks" / f"{slugify(owner)}.pre-check.md"


def reflection_check_output_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "checks" / f"{slugify(owner)}.post-task-reflection.md"


def agent_asset_review_output_path(*, library_root: Path, owner: str) -> Path:
    init_library(library_root)
    return library_root / "checks" / f"{slugify(owner)}.agent-assets.review.json"


def build_agent_assets_from_creator_profile(
    *,
    profile_path: Path,
    owner: str | None = None,
) -> dict[str, str]:
    raw_text = profile_path.read_text(encoding="utf-8")
    body = read_markdown_body(profile_path)
    resolved_owner = owner or find_markdown_field(raw_text, "owner") or profile_path.stem
    summary = _section_text(body, "Creator Summary") or "Use this profile as a provisional creator methodology reference."
    skills = _skill_candidates(_section_text(body, "Agent Skills"))
    pre_checks = _section_bullets(_section_text(body, "Pre-Checks"))
    reflections = _section_bullets(_section_text(body, "Post-Task Reflection"))

    return {
        "skill": _render_skill(
            owner=resolved_owner,
            summary=summary,
            skills=skills,
            pre_checks=pre_checks,
            reflections=reflections,
            profile_path=profile_path,
        ),
        "pre_check": _render_checklist(
            title=f"{resolved_owner} Pre-Check",
            owner=resolved_owner,
            profile_path=profile_path,
            items=pre_checks or ["确认这个 creator profile 是否适用于当前任务。"],
        ),
        "post_task_reflection": _render_checklist(
            title=f"{resolved_owner} Post-Task Reflection",
            owner=resolved_owner,
            profile_path=profile_path,
            items=reflections or ["记录本次使用 creator 方法后的效果和偏差。"],
        ),
    }


def write_agent_assets(
    *,
    library_root: Path,
    owner: str,
    assets: dict[str, str],
) -> dict[str, Path]:
    skill_path = skill_output_path(library_root=library_root, owner=owner)
    precheck_path = precheck_output_path(library_root=library_root, owner=owner)
    reflection_path = reflection_check_output_path(library_root=library_root, owner=owner)
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    precheck_path.parent.mkdir(parents=True, exist_ok=True)
    reflection_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(assets["skill"], encoding="utf-8")
    precheck_path.write_text(assets["pre_check"], encoding="utf-8")
    reflection_path.write_text(assets["post_task_reflection"], encoding="utf-8")
    paths = {
        "skill": skill_path,
        "pre_check": precheck_path,
        "post_task_reflection": reflection_path,
    }
    review = build_agent_asset_review(owner=owner, asset_paths=paths, status="draft")
    write_agent_asset_review(agent_asset_review_output_path(library_root=library_root, owner=owner), review)
    return paths


def build_agent_asset_review(
    *,
    owner: str,
    asset_paths: dict[str, Path],
    status: str = "draft",
    reviewer: str | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    validate_review_status(status)
    now = datetime.now(UTC).isoformat()
    return {
        "owner": owner,
        "status": status,
        "created_at": now,
        "updated_at": now,
        "reviewer": reviewer,
        "notes": notes or [],
        "assets": [
            {
                "type": asset_type,
                "path": str(path),
                "status": status,
                "reviewed_at": now if status != "draft" else None,
                "reviewer": reviewer,
                "notes": notes or [],
            }
            for asset_type, path in asset_paths.items()
        ],
    }


def write_agent_asset_review(path: Path, review: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def update_agent_asset_review(
    *,
    review_path: Path,
    status: str,
    asset_paths: list[Path] | None = None,
    reviewer: str | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    validate_review_status(status)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    now = datetime.now(UTC).isoformat()
    selected = {str(path) for path in asset_paths or []}
    for asset in review.get("assets", []):
        if selected and asset.get("path") not in selected:
            continue
        asset["status"] = status
        asset["reviewed_at"] = now if status != "draft" else None
        asset["reviewer"] = reviewer or asset.get("reviewer")
        asset["notes"] = [*(asset.get("notes") or []), *(notes or [])]
    statuses = {asset.get("status") for asset in review.get("assets", [])}
    review["status"] = status if len(statuses) == 1 else "mixed"
    review["updated_at"] = now
    review["reviewer"] = reviewer or review.get("reviewer")
    review["notes"] = [*(review.get("notes") or []), *(notes or [])]
    return review


def validate_review_status(status: str) -> None:
    if status not in AGENT_ASSET_REVIEW_STATUSES:
        allowed = ", ".join(sorted(AGENT_ASSET_REVIEW_STATUSES))
        raise ValueError(f"Unsupported review status: {status}. Allowed: {allowed}")


def _render_skill(
    *,
    owner: str,
    summary: str,
    skills: list[dict[str, str]],
    pre_checks: list[str],
    reflections: list[str],
    profile_path: Path,
) -> str:
    primary_skill = skills[0] if skills else {}
    skill_name = slugify(primary_skill.get("name") or f"{owner} methodology")
    description = primary_skill.get("trigger") or f"Apply reviewed methodology distilled from {owner} creator profile."
    procedure = primary_skill.get("procedure") or summary
    sections = [
        "---",
        f"name: {skill_name}",
        f"description: {description}",
        "---",
        "",
        f"# {owner} Methodology Skill",
        "",
        "## Source",
        "",
        f"- Creator profile: `{profile_path}`",
        f"- Generated at: {datetime.now(UTC).isoformat()}",
        "- Status: draft, requires human review before installation.",
        "",
        "## Summary",
        "",
        summary.strip(),
        "",
        "## Procedure",
        "",
        procedure.strip(),
        "",
        "## Candidate Skills",
        "",
    ]
    if skills:
        for skill in skills:
            sections.extend(
                [
                    f"- Skill name: {skill.get('name') or 'unknown'}",
                    f"  Trigger: {skill.get('trigger') or 'unknown'}",
                    f"  Procedure: {skill.get('procedure') or 'unknown'}",
                    f"  Inputs: {skill.get('inputs') or 'unknown'}",
                    f"  Outputs: {skill.get('outputs') or 'unknown'}",
                ]
            )
    else:
        sections.append("- No structured skill candidates found in the creator profile.")

    sections.extend(["", "## Pre-Checks", ""])
    sections.extend(f"- {item}" for item in pre_checks or ["Confirm fit with the current task."])
    sections.extend(["", "## Post-Task Reflection", ""])
    sections.extend(f"- {item}" for item in reflections or ["Record what worked, failed, and should change."])
    sections.append("")
    return "\n".join(sections)


def _render_checklist(
    *,
    title: str,
    owner: str,
    profile_path: Path,
    items: list[str],
) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Owner: {owner}",
        f"- Creator profile: `{profile_path}`",
        f"- Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Checklist",
        "",
    ]
    lines.extend(f"- [ ] {item}" for item in items)
    lines.append("")
    return "\n".join(lines)


def _section_text(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.M | re.S,
    )
    return match.group("body").strip() if match else ""


def _section_bullets(section: str) -> list[str]:
    items = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:])
    return items


def _skill_candidates(section: str) -> list[dict[str, str]]:
    if not section:
        return []
    candidates: list[dict[str, str]] = []
    current: dict[str, str] = {}
    key_map = {
        "Skill name": "name",
        "Trigger": "trigger",
        "Procedure": "procedure",
        "Inputs": "inputs",
        "Outputs": "outputs",
    }
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        content = stripped[2:]
        if ":" not in content:
            continue
        key, value = [part.strip() for part in content.split(":", 1)]
        mapped_key = key_map.get(key)
        if not mapped_key:
            continue
        if mapped_key == "name" and current:
            candidates.append(current)
            current = {}
        current[mapped_key] = value
    if current:
        candidates.append(current)
    return candidates
