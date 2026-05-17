from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from seed.library import init_library, slugify
from seed.markdown import read_markdown_body
from seed.semantics.aggregator import find_video_semantics_files
from seed.semantics.validation import creator_profile_validation_output_path


PROFILE_SECTION_ORDER = [
    "Recurring Methods",
    "Verbal Language Patterns",
    "Visual Language Patterns",
    "Video Structure Patterns",
    "Agent Skills",
    "Evidence Gaps",
]


@dataclass
class OwnerCompareRow:
    owner: str
    platform: str
    profile_path: Path
    validation_path: Path
    manifest_path: Path | None
    ledger_path: Path | None
    metadata: dict[str, str] = field(default_factory=dict)
    method_count: int = 0
    skill_count: int = 0
    missing_evidence_count: int = 0
    validation_status: str = "missing"
    validation_findings: int = 0
    videos_in_profile: int = 0
    video_runs_total: int = 0
    video_runs_completed: int = 0
    video_cost_totals: dict[str, float] = field(default_factory=dict)
    video_titles: list[str] = field(default_factory=list)


@dataclass
class CrossUpComparePayload:
    generated_at: str
    platform: str
    owners: list[OwnerCompareRow]


def compare_report_output_path(*, library_root: Path, title: str) -> Path:
    init_library(library_root)
    return library_root / "reports" / f"{slugify(title)}.up-comparison.html"


def build_cross_up_compare_payload(
    *,
    owners: list[str],
    platform: str,
    root: Path,
) -> CrossUpComparePayload:
    rows = [_collect_owner_row(owner=owner, platform=platform, root=root) for owner in owners]
    return CrossUpComparePayload(
        generated_at=datetime.now(UTC).isoformat(),
        platform=platform,
        owners=rows,
    )


def _collect_owner_row(owner: str, platform: str, root: Path) -> OwnerCompareRow:
    slug = slugify(owner)
    profile_path = root / "distilled" / f"{slug}.creator-profile.md"
    validation_path = creator_profile_validation_output_path(library_root=root, owner=owner)
    manifest_path = root / "runs" / f"{slug}.creator-pipeline.yaml"
    ledger_path = _resolve_ledger_path(root=root, owner=owner)
    metadata = _parse_profile_metadata(profile_path)
    sections = _parse_profile_sections(profile_path)
    validation_status = "missing"
    findings_count = 0
    if validation_path.exists():
        validation = _load_json(validation_path)
        if isinstance(validation, dict):
            validation_status = str(validation.get("status", "unknown"))
            findings = validation.get("findings", [])
            if isinstance(findings, list):
                findings_count = len(findings)
    video_runs_total = 0
    video_runs_completed = 0
    video_titles: list[str] = []
    if manifest_path.exists():
        manifest = _load_yaml_like(manifest_path)
        if isinstance(manifest, dict):
            video_runs = manifest.get("video_runs", [])
            if isinstance(video_runs, list):
                video_runs_total = len(video_runs)
                video_runs_completed = len(
                    [run for run in video_runs if isinstance(run, dict) and run.get("status") == "completed"]
                )
                for run in video_runs:
                    if run.get("video_title"):
                        video_titles.append(str(run["video_title"]))
    if not video_titles:
        video_titles = _find_owner_video_titles(library_root=root, owner=owner)
    cost_totals: dict[str, float] = {}
    if ledger_path and ledger_path.exists():
        ledger = _load_json(ledger_path)
        totals = ledger.get("totals", {})
        if isinstance(totals, dict):
            cost_totals = {str(k): float(v) for k, v in totals.items() if _is_number(v)}
    videos_in_profile = _to_int(metadata.get("videos analyzed", metadata.get("video count")))
    if videos_in_profile <= 0:
        videos_in_profile = _to_int(metadata.get("videos_analyzed"))
    return OwnerCompareRow(
        owner=owner,
        platform=platform,
        profile_path=profile_path,
        validation_path=validation_path,
        manifest_path=manifest_path,
        ledger_path=ledger_path,
        metadata=metadata,
        method_count=sections.get("method_count", 0),
        skill_count=sections.get("skill_count", 0),
        missing_evidence_count=sections.get("missing_evidence_count", 0),
        validation_status=validation_status,
        validation_findings=findings_count,
        videos_in_profile=videos_in_profile,
        video_runs_total=video_runs_total,
        video_runs_completed=video_runs_completed,
        video_cost_totals=cost_totals,
        video_titles=video_titles,
    )


def _resolve_ledger_path(*, root: Path, owner: str) -> Path | None:
    candidate = root / "costs" / f"{slugify(owner)}-creator.ledger.json"
    if candidate.exists():
        return candidate
    legacy = root / "costs" / f"{slugify(owner)}.creator.ledger.json"
    if legacy.exists():
        return legacy
    return None


def _find_owner_video_titles(*, library_root: Path, owner: str) -> list[str]:
    titles: list[str] = []
    for path in find_video_semantics_files(library_root=library_root, owner=owner):
        title = _extract_field_from_markdown(path, "title")
        if title:
            titles.append(title)
    return sorted(set(titles))


def _parse_profile_metadata(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    in_metadata = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Metadata":
            in_metadata = True
            continue
        if not in_metadata:
            continue
        if stripped.startswith("## "):
            break
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        metadata[key.strip().lower()] = value.strip()
    return metadata


def _parse_profile_sections(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {
        "method_count": 0,
        "skill_count": 0,
        "missing_evidence_count": 0,
    }
    if not path.exists():
        return counts
    lines = read_markdown_body(path).splitlines()
    section = ""
    current_skill = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            section = stripped.removeprefix("## ").strip()
            continue
        if section == "Recurring Methods" and stripped.startswith("- Method:"):
            counts["method_count"] += 1
            continue
        if section == "Agent Skills" and stripped.startswith("- Skill name:"):
            counts["skill_count"] += 1
            current_skill = 0
            continue
        if section == "Evidence Gaps":
            if stripped.startswith("- "):
                counts["missing_evidence_count"] += 1
            continue
        if section in PROFILE_SECTION_ORDER:
            if re.search(r"\[T\d+\]|\[V\d+\]|\[F\d+\]", stripped):
                current_skill += 1
    if current_skill == 0:
        counts["missing_evidence_count"] = max(counts["missing_evidence_count"], 0)
    return counts


def _extract_field_from_markdown(path: Path, field: str) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    prefix = f"- {field}:"
    for line in text.splitlines():
        normalized = line.strip()
        if normalized.startswith(prefix):
            return normalized.split(":", 1)[1].strip()
    return ""


def _load_yaml_like(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError:
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _to_int(value: str | None) -> int:
    if not value:
        return 0
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else 0


def _is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def build_cross_up_compare_html(payload: CrossUpComparePayload) -> str:
    rows = payload.owners
    header_columns = [
        "Owner",
        "Platform",
        "Videos In Profile",
        "Video Runs",
        "Validation",
        "Warnings",
        "Method Count",
        "Skill Count",
        "Cost (USD)",
        "Artifacts",
    ]
    row_html = "\n".join(_owner_row_to_html(owner) for owner in rows)
    ranking_rows = _build_top_lineup_rows(rows)
    ranking_html = "\n".join(_rank_row_to_html(item) for item in ranking_rows)
    total_cost = _format_currency(_sum_usd(rows))
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>UP 横向对比报告</title>
    <style>
      :root {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        color: #1f2937;
      }}
      body {{ margin: 20px; background: #f8fafc; }}
      .card {{ background: #fff; border: 1px solid #d8e2ef; border-radius: 8px; padding: 16px; margin: 12px 0; }}
      h1 {{ margin: 4px 0 12px 0; }}
      .muted {{ color: #6b7280; font-size: 12px; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
      th, td {{ border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; font-size: 14px; vertical-align: top; }}
      thead th {{ background: #f1f5f9; position: sticky; top: 0; }}
      tr:hover {{ background: #f9fbff; }}
      .badge {{
        display: inline-block; padding: 2px 8px; border-radius: 999px;
        border: 1px solid #cbd5e1; font-size: 12px;
      }}
      .good {{ background: #ecfdf5; color: #166534; border-color: #a7f3d0; }}
      .warn {{ background: #fffbeb; color: #92400e; border-color: #fde68a; }}
      .bad {{ background: #fef2f2; color: #991b1b; border-color: #fecaca; }}
      .rank {{ display: flex; gap: 12px; align-items: center; margin: 8px 0; flex-wrap: wrap; }}
      .rank-item {{ min-width: 220px; background: #f8fafc; border: 1px dashed #bfdbfe; border-radius: 8px; padding: 8px 10px; }}
      .small {{ font-size: 12px; line-height: 1.5; }}
      ul {{ margin: 0 0 0 16px; padding: 0; }}
      code {{ background: #f1f5f9; padding: 1px 4px; border-radius: 4px; }}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>UP 横向对比报告</h1>
      <div class="muted">平台：{html.escape(payload.platform)} ｜ 生成时间：{html.escape(payload.generated_at)}</div>
      <div class="muted">总计（美元）：{html.escape(total_cost)}</div>
    </div>
    <div class="card">
      <h2>Top-Down 速览</h2>
      <div class="rank">
        {ranking_html or "<span class=small>暂无足够数据，建议先补齐 creator profile 与 cost ledger。</span>"}
      </div>
    </div>
    <div class="card">
      <h2>UP 详情对比</h2>
      <table>
        <thead>
          <tr>
            {''.join(f'<th>{html.escape(col)}</th>' for col in header_columns)}
          </tr>
        </thead>
        <tbody>
          {row_html}
        </tbody>
      </table>
    </div>
    <div class="card small">
      <h2>说明</h2>
      <ul>
        <li>方法与 Skill 的计数来自 creator profile 的内容块（如 <code>Recurring Methods</code>、<code>Agent Skills</code>）。</li>
        <li>Validation 来源于 <code>creator-profile.validation.json</code>，用于提示证据引用缺口。</li>
        <li>Cost 汇总优先使用 creator ledger；如无则尝试读取相关 video ledger 归并。</li>
      </ul>
    </div>
  </body>
</html>"""


def _format_currency(value: float) -> str:
    return f"{value:,.8f} USD"


def _sum_usd(rows: list[OwnerCompareRow]) -> float:
    total = 0.0
    for row in rows:
        total += float(row.video_cost_totals.get("USD", 0.0))
    return total


def _status_badge(status: str, findings: int) -> str:
    if status == "passed" and findings == 0:
        return '<span class="badge good">passed</span>'
    if status in {"warnings", "warning"}:
        return f'<span class="badge warn">warnings ({findings})</span>'
    if status == "missing":
        return '<span class="badge bad">missing</span>'
    return f'<span class="badge">{html.escape(status)}</span>'


def _owner_row_to_html(owner: OwnerCompareRow) -> str:
    artifact_paths = _build_artifact_links(owner)
    cost_text = _format_currency(owner.video_cost_totals.get("USD", 0.0))
    confidence = owner.metadata.get("confidence", "-")
    return f"""
      <tr>
        <td><strong>{html.escape(owner.owner)}</strong><br/><span class="small">{html.escape(confidence)}</span></td>
        <td>{html.escape(owner.platform)}</td>
        <td>{owner.videos_in_profile or 0}</td>
        <td>{owner.video_runs_completed}/{owner.video_runs_total}</td>
        <td>{_status_badge(owner.validation_status, owner.validation_findings)}</td>
        <td>{owner.validation_findings}</td>
        <td>{owner.method_count}</td>
        <td>{owner.skill_count}</td>
        <td>{html.escape(cost_text)}</td>
        <td>{artifact_paths}</td>
      </tr>"""


def _build_artifact_links(owner: OwnerCompareRow) -> str:
    links: list[str] = []
    if owner.profile_path.exists():
        links.append(_mk_link(owner.profile_path, "creator-profile"))
    if owner.validation_path.exists():
        links.append(_mk_link(owner.validation_path, "validation"))
    if owner.manifest_path and owner.manifest_path.exists():
        links.append(_mk_link(owner.manifest_path, "creator-manifest"))
    if owner.ledger_path and owner.ledger_path.exists():
        links.append(_mk_link(owner.ledger_path, "creator-ledger"))
    if owner.video_titles:
        videos = ", ".join(html.escape(t) for t in owner.video_titles[:3])
        links.append(f"<span class=muted>videos: {videos}</span>")
        if len(owner.video_titles) > 3:
            links.append(
                f"<span class=muted>+{len(owner.video_titles) - 3} 更多</span>"
            )
    return "<br/>".join(links) if links else "<span class=muted>artifact missing</span>"


def _mk_link(path: Path, label: str) -> str:
    escaped = html.escape(str(path))
    return f'<a href="{escaped}" target="_blank">{label}</a>'


def _build_top_lineup_rows(rows: list[OwnerCompareRow]) -> list[tuple[str, str, str]]:
    if not rows:
        return []
    sorted_by_cost = sorted(rows, key=lambda item: item.video_cost_totals.get("USD", 0.0), reverse=True)
    by_methods = sorted(rows, key=lambda item: item.method_count, reverse=True)
    by_video_count = sorted(rows, key=lambda item: item.videos_in_profile, reverse=True)
    return [
        ("成本最高", sorted_by_cost[0].owner, _format_currency(sorted_by_cost[0].video_cost_totals.get("USD", 0.0))),
        ("方法点数", by_methods[0].owner, str(by_methods[0].method_count)),
        ("视频样本量", by_video_count[0].owner, str(by_video_count[0].videos_in_profile)),
    ]


def _rank_row_to_html(item: tuple[str, str, str]) -> str:
    metric, owner, value = item
    return (
        f'<div class="rank-item">'
        f'<div><strong>{html.escape(metric)}</strong></div>'
        f'<div>{html.escape(owner)} · {html.escape(value)}</div>'
        f"</div>"
    )

