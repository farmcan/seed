from __future__ import annotations

import json

from seed.cross_compare import build_cross_up_compare_payload, build_cross_up_compare_html


def _write_text(path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_compare_up_payload_uses_profile_validation_manifest_and_ledger(tmp_path):
    root = tmp_path / "library"
    owner = "demo-owner"
    slug = "demo-owner"

    _write_text(
        root / "distilled" / f"{slug}.creator-profile.md",
        """---
owner: demo-owner
---

## Metadata
- Videos Analyzed: 5
- Confidence: medium

## Recurring Methods
- Method: hook-first storytelling
- Method: pattern extraction

## Agent Skills
- Skill name: editing breakdown

## Evidence Gaps
- No transcript for segment A
""",
    )
    _write_json(
        root / "distilled" / f"{slug}.creator-profile.validation.json",
        {
            "status": "passed",
            "findings": [],
        },
    )
    _write_text(
        root / "runs" / f"{slug}.creator-pipeline.yaml",
        """video_runs:
  - status: completed
    video_title: Demo 1
  - status: failed
    video_title: Demo 2
""",
    )
    _write_json(
        root / "costs" / f"{slug}-creator.ledger.json",
        {"totals": {"USD": 0.1234}},
    )

    payload = build_cross_up_compare_payload(
        owners=[owner],
        platform="bilibili",
        root=root,
    )
    assert len(payload.owners) == 1
    row = payload.owners[0]
    assert row.owner == owner
    assert row.validation_status == "passed"
    assert row.videos_in_profile == 5
    assert row.video_runs_completed == 1
    assert row.video_runs_total == 2
    assert row.video_cost_totals["USD"] == 0.1234
    assert row.method_count == 2
    assert row.skill_count == 1


def test_compare_up_html_mentions_missing_and_exists_artifacts(tmp_path):
    root = tmp_path / "library"
    owner_exist = "demo-owner"
    owner_empty = "empty-owner"

    _write_text(
        root / "distilled" / f"{owner_exist}.creator-profile.md",
        """## Metadata\n- Videos Analyzed: 2\n""",
    )
    _write_text(
        root / "runs" / f"{owner_empty}.creator-pipeline.yaml",
        "video_runs: []",
    )

    payload = build_cross_up_compare_payload(
        owners=[owner_exist, owner_empty],
        platform="xiaohongshu",
        root=root,
    )
    html = build_cross_up_compare_html(payload)

    assert "demo-owner" in html
    assert "empty-owner" in html
    assert "warning" not in html
    assert "missing" in html
