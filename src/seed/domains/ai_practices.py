from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from seed.agents.codex import run_codex_prompt
from seed.library import init_library, slugify
from seed.skill_refs import read_video_analysis_lenses


AI_PRACTICES_DOMAIN = "ai-practices"


def ai_practice_signals_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "semantics" / f"{slugify(title)}.ai-practice-signals.json"


def ai_practice_digest_output_path(
    *,
    library_root: Path,
    person: str,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> Path:
    init_library(library_root)
    window = ai_practice_window_slug(
        published_after=published_after,
        published_before=published_before,
    )
    return library_root / "distilled" / f"{slugify(person)}.{window}.ai-practice-digest.json"


def ai_practice_window_slug(
    *,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> str:
    if not published_after and not published_before:
        return "all"
    after = date_slug(published_after) if published_after else "start"
    before = date_slug(published_before) if published_before else "now"
    return f"{after}-to-{before}"


def date_slug(value: datetime | None) -> str:
    if value is None:
        return "none"
    resolved = value if value.tzinfo else value.replace(tzinfo=UTC)
    return resolved.astimezone(UTC).strftime("%Y%m%d")


def build_ai_practice_signals_prompt(
    *,
    semantics_path: Path,
    title: str | None = None,
    person: str | None = None,
    platform: str | None = None,
) -> str:
    semantics = semantics_path.read_text(encoding="utf-8")
    lenses = read_video_analysis_lenses(domains=[AI_PRACTICES_DOMAIN])
    generated_at = datetime.now(UTC).isoformat()
    return f"""Extract AI-practices domain signals from this video semantics artifact.

Return only valid JSON. Do not wrap it in Markdown. Do not modify files.

Focus on how the person actually uses AI, what they believe this AI era changes, which capabilities they recommend building, and which concrete experiments can be applied to a person's workflow or to the Seed project.

Use only evidence available in the video semantics artifact and its evidence references. If a practice, tool, capability, timestamp, or evidence reference is missing, use null or an empty list instead of guessing.

Metadata:
- Title: {title or semantics_path.stem}
- Person: {person or "unknown"}
- Platform: {platform or "unknown"}
- Generated at: {generated_at}
- Semantics path: {semantics_path}

<analysis_lenses>
{lenses}
</analysis_lenses>

JSON schema:
{{
  "version": 1,
  "kind": "ai_practice_signals",
  "domain": "ai-practices",
  "title": string,
  "person": string,
  "owner": string,
  "platform": string,
  "generated_at": string,
  "basis_path": string,
  "ai_usage_summary": string,
  "practice_events": [
    {{
      "event_id": string,
      "practice": string,
      "workflow_stage": string | null,
      "task_type": string | null,
      "tools": [string],
      "inputs": [string],
      "outputs": [string],
      "validation_method": string | null,
      "failure_modes": [string],
      "evidence_refs": [string],
      "timestamp_start": string | null,
      "timestamp_end": string | null,
      "uncertainty": string | null
    }}
  ],
  "belief_events": [
    {{
      "belief_id": string,
      "claim": string,
      "topic": string | null,
      "recommendation": string | null,
      "time_horizon": string | null,
      "rationale": string,
      "evidence_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "capability_signals": [
    {{
      "capability": string,
      "description": string,
      "why_it_matters": string,
      "how_to_practice": string | null,
      "evidence_refs": [string],
      "uncertainty": string | null
    }}
  ],
  "tooling_patterns": [
    {{
      "tool_or_pattern": string,
      "use_case": string,
      "setup_notes": string | null,
      "guardrails": [string],
      "evidence_refs": [string]
    }}
  ],
  "personal_application_candidates": [
    {{
      "candidate": string,
      "why_relevant": string,
      "first_experiment": string,
      "effort": "low" | "medium" | "high" | "unknown",
      "risk": string | null,
      "evidence_refs": [string]
    }}
  ],
  "project_application_candidates": [
    {{
      "candidate": string,
      "seed_project_area": string,
      "expected_value": string,
      "first_experiment": string,
      "dependencies": [string],
      "risk": string | null,
      "evidence_refs": [string]
    }}
  ],
  "evidence_gaps": [string],
  "open_questions": [string]
}}

<video_semantics>
{semantics}
</video_semantics>
"""


def run_ai_practice_signals_extraction(
    *,
    semantics_path: Path,
    output_path: Path,
    title: str | None = None,
    person: str | None = None,
    platform: str | None = None,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    prompt = build_ai_practice_signals_prompt(
        semantics_path=semantics_path,
        title=title,
        person=person,
        platform=platform,
    )
    return run_codex_prompt(
        prompt=prompt,
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
        dry_run=dry_run,
    )


def load_ai_practice_signals(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_ai_practice_signal_files(*, library_root: Path, person: str | None = None) -> list[Path]:
    semantics_dir = library_root / "semantics"
    if not semantics_dir.exists():
        return []
    paths = sorted(semantics_dir.glob("*.ai-practice-signals.json"))
    if person is None:
        return paths
    return [
        path
        for path in paths
        if ai_practice_signal_matches_person(load_ai_practice_signals(path), person)
    ]


def ai_practice_signal_matches_person(signals: dict[str, Any], person: str) -> bool:
    candidates = [
        signals.get("person"),
        signals.get("owner"),
        signals.get("creator"),
    ]
    return any(str(candidate or "").casefold() == person.casefold() for candidate in candidates)


def build_ai_practice_digest_artifact(
    *,
    signal_paths: list[Path],
    person: str,
    platform: str | None = None,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    video_metadata_by_title: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metadata = video_metadata_by_title or {}
    records = [
        build_ai_practice_digest_record(path, metadata_by_title=metadata)
        for path in signal_paths
        if path.exists()
    ]
    records = [
        record
        for record in records
        if record_matches_window(
            record,
            published_after=published_after,
            published_before=published_before,
        )
    ]
    practice_events = flatten_record_items(records, "practice_events")
    belief_events = flatten_record_items(records, "belief_events")
    personal_candidates = flatten_record_items(records, "personal_application_candidates")
    project_candidates = flatten_record_items(records, "project_application_candidates")
    capability_signals = summarize_named_items(
        [item for record in records for item in record["capability_signals"]],
        name_key="capability",
    )
    tooling_patterns = summarize_named_items(
        [item for record in records for item in record["tooling_patterns"]],
        name_key="tool_or_pattern",
    )
    return {
        "version": 1,
        "kind": "ai_practice_digest",
        "domain": AI_PRACTICES_DOMAIN,
        "person": person,
        "platform": platform or infer_platform(records),
        "generated_at": datetime.now(UTC).isoformat(),
        "window": {
            "published_after": normalize_datetime(published_after),
            "published_before": normalize_datetime(published_before),
        },
        "videos_analyzed": len(records),
        "signal_paths": [record["signal_path"] for record in records],
        "totals": {
            "practice_events": len(practice_events),
            "belief_events": len(belief_events),
            "capability_signals": len(capability_signals),
            "tooling_patterns": len(tooling_patterns),
            "personal_application_candidates": len(personal_candidates),
            "project_application_candidates": len(project_candidates),
        },
        "practice_events": practice_events,
        "belief_events": belief_events,
        "capability_signals": capability_signals,
        "tooling_patterns": tooling_patterns,
        "personal_application_candidates": personal_candidates,
        "project_application_candidates": project_candidates,
        "evidence_gaps": sorted({gap for record in records for gap in record["evidence_gaps"]}),
        "open_questions": sorted({question for record in records for question in record["open_questions"]}),
        "video_records": records,
    }


def build_ai_practice_digest_record(
    path: Path,
    *,
    metadata_by_title: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    signals = load_ai_practice_signals(path)
    title = str(signals.get("title") or path.stem.removesuffix(".ai-practice-signals"))
    metadata = metadata_by_title.get(title, {})
    return {
        "title": title,
        "person": signals.get("person") or signals.get("owner"),
        "owner": signals.get("owner") or signals.get("person"),
        "platform": signals.get("platform"),
        "published_at": metadata.get("published_at"),
        "url": metadata.get("url"),
        "video_id": metadata.get("video_id"),
        "signal_path": str(path),
        "ai_usage_summary": signals.get("ai_usage_summary"),
        "practice_events": signals.get("practice_events") or [],
        "belief_events": signals.get("belief_events") or [],
        "capability_signals": signals.get("capability_signals") or [],
        "tooling_patterns": signals.get("tooling_patterns") or [],
        "personal_application_candidates": signals.get("personal_application_candidates") or [],
        "project_application_candidates": signals.get("project_application_candidates") or [],
        "evidence_gaps": signals.get("evidence_gaps") or [],
        "open_questions": signals.get("open_questions") or [],
    }


def flatten_record_items(records: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return [
        {
            **item,
            "video_title": record["title"],
            "signal_path": record["signal_path"],
            "published_at": record.get("published_at"),
        }
        for record in records
        for item in record[key]
        if isinstance(item, dict)
    ]


def record_matches_window(
    record: dict[str, Any],
    *,
    published_after: datetime | None,
    published_before: datetime | None,
) -> bool:
    if published_after is None and published_before is None:
        return True
    published_at = parse_datetime(record.get("published_at"))
    if published_at is None:
        return False
    after = ensure_utc(published_after)
    before = ensure_utc(published_before)
    if after and published_at < after:
        return False
    if before and published_at >= before:
        return False
    return True


def summarize_named_items(items: list[dict[str, Any]], *, name_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in items:
        name = str(item.get(name_key) or "unknown")
        key = name.casefold()
        current = grouped.setdefault(key, {name_key: name, "mentions": 0, "examples": []})
        current["mentions"] += 1
        if len(current["examples"]) < 5:
            current["examples"].append(item)
    return sorted(grouped.values(), key=lambda value: (-int(value["mentions"]), str(value[name_key])))


def infer_platform(records: list[dict[str, Any]]) -> str | None:
    platforms = [record.get("platform") for record in records if record.get("platform")]
    return str(platforms[0]) if platforms else None


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return ensure_utc(value)
    try:
        return ensure_utc(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
    except ValueError:
        return None


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def normalize_datetime(value: datetime | None) -> str | None:
    resolved = ensure_utc(value)
    return resolved.isoformat() if resolved else None


def write_ai_practice_digest_artifact(path: Path, artifact: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
