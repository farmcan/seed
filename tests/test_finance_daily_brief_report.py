import json

from typer.testing import CliRunner

from seed.cli import app
from seed.reports.finance_daily import (
    build_finance_daily_brief_artifact,
    build_finance_daily_brief_html,
)


def test_build_finance_daily_brief_groups_creators_and_consensus():
    digest_one = {
        "kind": "finance_digest",
        "owner": "UP A",
        "platform": "bilibili",
        "videos_analyzed": 2,
        "viewpoint_events": [
            {
                "event_id": "a-1",
                "video_title": "AI capex",
                "instrument": "NVDA",
                "ticker": "NVDA.US",
                "action": "watch",
                "direction": "bullish",
                "horizon": "medium",
                "conviction": "high",
                "entry_condition": "Watch AI capex and margins.",
                "risk_flags": ["valuation"],
                "evidence_refs": ["T1"],
            }
        ],
        "methodology_signals": [
            {
                "method": "catalyst checklist",
                "decision_rule": "Only upgrade conviction after capex confirmation.",
                "failure_modes": ["valuation compression"],
                "evidence_refs": ["T1"],
            }
        ],
        "risk_flags": ["valuation"],
        "evidence_gaps": ["Need latest earnings transcript."],
    }
    digest_two = {
        "kind": "finance_digest",
        "owner": "UP B",
        "platform": "youtube",
        "videos_analyzed": 1,
        "viewpoint_events": [
            {
                "event_id": "b-1",
                "video_title": "Semis cycle",
                "instrument": "NVDA",
                "ticker": "NVDA.US",
                "action": "reduce",
                "direction": "bearish",
                "horizon": "short",
                "conviction": "medium",
                "entry_condition": "Wait for valuation reset.",
                "risk_flags": ["crowded trade"],
                "evidence_refs": ["T2"],
            }
        ],
    }

    artifact = build_finance_daily_brief_artifact(
        [digest_one, digest_two],
        title="Daily",
        report_date="2026-05-31",
    )
    html = build_finance_daily_brief_html(artifact)

    assert artifact["totals"]["creators"] == 2
    assert artifact["totals"]["viewpoint_events"] == 2
    assert artifact["consensus_rows"][0]["consensus"] == "conflict"
    assert artifact["methodology_rows"][0]["method"] == "catalyst checklist"
    assert "UP A" in html
    assert "UP B" in html
    assert "conflict" in html
    assert "Only upgrade conviction" in html


def test_build_finance_daily_brief_cli_writes_json_and_html(tmp_path):
    digest_path = tmp_path / "demo.finance-digest.json"
    digest_path.write_text(
        json.dumps(
            {
                "kind": "finance_digest",
                "owner": "demo",
                "platform": "bilibili",
                "videos_analyzed": 1,
                "viewpoint_events": [
                    {
                        "event_id": "one",
                        "video_title": "Market",
                        "instrument": "AI",
                        "action": "watch",
                        "direction": "mixed",
                        "conviction": "low",
                        "evidence_refs": ["T1"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "build-finance-daily-brief",
            str(digest_path),
            "--report-date",
            "2026-05-31",
            "--root",
            str(tmp_path / "library"),
        ],
    )

    assert result.exit_code == 0
    artifact_path = tmp_path / "library" / "distilled" / "2026-05-31.finance-creator-daily-brief.json"
    html_path = tmp_path / "library" / "reports" / "2026-05-31.finance-creator-daily-brief.html"
    assert artifact_path.exists()
    assert html_path.exists()
    assert "demo" in html_path.read_text(encoding="utf-8")
