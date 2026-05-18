import json

from seed.cli import build_finance_outlook_report
from seed.reports.finance_outlook import (
    build_finance_outlook_report_html,
    finance_outlook_output_path,
    finance_outlook_payload_output_path,
    build_finance_outlook_payload,
    build_finance_outlook_outputs_for_owner,
    find_owner_finance_outlook_report_paths,
)


def test_build_finance_outlook_payload_and_html(tmp_path):
    digest_path = tmp_path / "demo.finance-digest.news-context.json"
    digest = {
        "kind": "finance_digest_with_news_context",
        "owner": "demo",
        "platform": "bilibili",
        "viewpoint_events": [
            {
                "event_id": "demo-1",
                "instrument": "AI",
                "action": "watch",
                "direction": "bullish",
                "conviction": "medium",
                "risk_flags": ["valuation"],
                "evidence_refs": ["T1"],
                "event_outcomes": {
                    "status": "priced",
                    "latest": {"asset_return": 3.2, "max_drawdown": -1.1},
                    "horizons": {
                        "1D": {"asset_return": 2.0},
                        "5D": {"asset_return": -1.5},
                    },
                },
                "news_context": [{"source_gaps": ["缺口1"], "open_questions": ["问题1"]}],
            },
            {
                "event_id": "demo-2",
                "instrument": "semiconductor",
                "action": "watch",
                "direction": "neutral",
                "conviction": "high",
                "risk_flags": ["policy_uncertainty"],
                "evidence_refs": [],
                "event_outcomes": {
                    "status": "priced",
                    "latest": {"asset_return": -2.4, "max_drawdown": -2.2},
                    "horizons": {
                        "1D": {"asset_return": -0.5},
                    },
                },
            },
        ],
        "macro_theses": [{"thesis": "AIGC 软件采用率继续抬升。"}],
        "open_questions": ["宏观问题"],
        "source_gaps": ["尚缺财报验证"],
        "methodology_signals": [],
    }
    digest_path.write_text(json.dumps(digest, ensure_ascii=False), encoding="utf-8")

    payload = build_finance_outlook_payload(digest, digest_path=digest_path)
    html = build_finance_outlook_report_html(payload)

    assert payload["totals"]["events"] == 2
    assert payload["totals"]["priced_events"] == 2
    assert "demo - 财经观点前瞻研判" in html
    assert payload["asset_rollups"][0]["asset_id"] == "AI"
    assert finance_outlook_output_path(
        library_root=tmp_path,
        digest_path=digest_path,
    ) == tmp_path / "reports" / "demo.finance-outlook-report.html"
    assert finance_outlook_payload_output_path(
        library_root=tmp_path,
        digest_path=digest_path,
    ) == tmp_path / "distilled" / "demo.finance-outlook.json"


def test_build_finance_outlook_outputs_for_owner(tmp_path):
    digest_path = tmp_path / "distilled" / "demo-owner.finance-digest.news-context.json"
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(
        json.dumps(
            {
                "kind": "finance_digest_with_news_context",
                "owner": "demo-owner",
                "platform": "bilibili",
                "viewpoint_events": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    outputs = build_finance_outlook_outputs_for_owner(
        library_root=tmp_path,
        owner="demo-owner",
    )
    assert set(path.name for path in outputs) == {
        "demo-owner.finance-outlook.json",
        "demo-owner.finance-outlook-report.html",
    }
    assert (tmp_path / "distilled" / "demo-owner.finance-outlook.json").exists()
    assert (tmp_path / "reports" / "demo-owner.finance-outlook-report.html").exists()


def test_finance_outlook_command_builds_payload_and_report(tmp_path):
    digest_path = tmp_path / "distilled" / "demo.finance-digest.json"
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(
        json.dumps(
            {
                "kind": "finance_digest",
                "owner": "demo",
                "platform": "bilibili",
                "viewpoint_events": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    build_finance_outlook_report(
        digest_path=digest_path,
        output=tmp_path / "custom-report.html",
        payload_output=tmp_path / "custom-payload.json",
        root=tmp_path,
    )

    assert (tmp_path / "custom-report.html").exists()
    assert (tmp_path / "custom-payload.json").exists()


def test_find_owner_finance_outlook_report_paths(tmp_path):
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "demo.finance-news-report.html").write_text("news", encoding="utf-8")
    (tmp_path / "reports" / "demo.finance-outlook-report.html").write_text("outlook", encoding="utf-8")

    assert find_owner_finance_outlook_report_paths(
        library_root=tmp_path,
        owner="demo",
    ) == [tmp_path / "reports" / "demo.finance-outlook-report.html"]
