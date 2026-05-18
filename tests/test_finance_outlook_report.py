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
        "peer_context": {
            "target_asset": "demo-target",
            "target_ticker": "DEMO",
            "industry": "软件服务",
            "peers": [
                {"name": "peer-a", "ticker": "PEER", "relation": "对标", "note": "规模接近"},
                {"name": "peer-b", "relation": "供应链"},
            ],
        },
        "viewpoint_events": [
            {
                "event_id": "demo-1",
                "instrument": "AI",
                "action": "watch",
                "direction": "bullish",
                "conviction": "medium",
                "risk_flags": ["valuation"],
                "summary": "讨论了 Claude Code 与团队交付效率。",
                "evidence_refs": ["T1"],
                "published_at": "2026-05-01T09:00:00+00:00",
                "event_outcomes": {
                    "status": "priced",
                    "latest": {
                        "status": "priced",
                        "asset_return": 3.2,
                        "max_drawdown": -1.1,
                        "published_price_date": "2026-05-01",
                        "latest_price_date": "2026-05-02",
                        "published_close": 10.0,
                        "latest_close": 11.0,
                    },
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
                "published_at": "2026-05-10T12:00:00+00:00",
                "event_outcomes": {
                    "status": "priced",
                    "latest": {
                        "status": "priced",
                        "asset_return": -2.4,
                        "max_drawdown": -2.2,
                        "published_price_date": "2026-05-10",
                        "latest_price_date": "2026-05-11",
                        "published_close": 12.0,
                        "latest_close": 11.6,
                    },
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
    assert payload["time_coverage"]["status"] == "available"
    assert payload["time_coverage"]["events_with_time"] == 2
    assert payload["peer_context"]["target_ticker"] == "DEMO"
    assert payload["scenarios"]["status"] == "ok"
    assert payload["scenarios"]["base_case"]["status"] == "observed"
    assert payload["scenarios"]["base_case"]["event_count"] == 2
    assert payload["scenarios"]["upside_case"]["event_count"] >= 1
    assert payload["scenarios"]["downside_case"]["event_count"] >= 1
    assert payload["asset_rollups"][0]["target_prices"]["upside_target"] is not None
    assert payload["asset_rollups"][1]["target_prices"]["downside_target"] is not None
    assert "AI Coding（如 Claude Code、Cursor、Copilot 等）" in " ".join(payload["aicoding_signals"])
    assert payload["aicoding_signals"]
    assert "AI 代码工具替代压力" in payload["risk_flags"]
    assert "demo - 财经观点前瞻研判" in html
    assert "时间覆盖" in html
    assert "同类公司（事实输入）" in html
    assert "AI Coding 结构性变量（软件护城河）" in html
    assert "目标价位草案（基于价格后验）" in html
    assert "上行目标" in html
    assert "情景锚点（事件级）" in html
    assert "基准情景" in html
    assert "上行情景" in html
    assert "下行情景" in html
    assert payload["asset_rollups"][0]["asset_id"] == "AI"
    assert finance_outlook_output_path(
        library_root=tmp_path,
        digest_path=digest_path,
    ) == tmp_path / "reports" / "demo.finance-outlook-report.html"
    assert finance_outlook_payload_output_path(
        library_root=tmp_path,
        digest_path=digest_path,
    ) == tmp_path / "distilled" / "demo.finance-outlook.json"
    assert finance_outlook_output_path(
        library_root=tmp_path,
        digest_path=tmp_path / "demo.finance-outlook.json",
    ) == tmp_path / "reports" / "demo.finance-outlook-report.html"


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


def test_build_finance_outlook_outputs_for_owner_prefers_valid_finance_digest(tmp_path):
    (tmp_path / "distilled").mkdir(parents=True, exist_ok=True)
    (tmp_path / "distilled" / "demo-owner.finance-digest.priced.news-context.json").write_text(
        json.dumps(
            {
                "kind": "finance_digest",
                "owner": "demo-owner",
                "platform": "bilibili",
                "viewpoint_events": [
                    {
                        "event_id": "from-digest",
                        "instrument": "MEITU",
                        "action": "watch",
                        "direction": "bullish",
                        "event_outcomes": {
                            "status": "priced",
                            "latest": {"status": "priced", "asset_return": 4.0, "max_drawdown": -1.0},
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "distilled" / "demo-owner.finance-outlook.json").write_text(
        json.dumps(
            {
                "kind": "finance_outlook",
                "owner": "demo-owner",
                "platform": "bilibili",
                "source_digest_path": str(tmp_path / "legacy-source.finance-digest.json"),
                "viewpoint_events": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "legacy-source.finance-digest.json").write_text(
        json.dumps(
            {
                "kind": "finance_digest",
                "owner": "demo-owner",
                "platform": "bilibili",
                "viewpoint_events": [
                    {
                        "event_id": "from-legacy",
                        "instrument": "MEITU",
                        "action": "watch",
                        "direction": "neutral",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    outputs = build_finance_outlook_outputs_for_owner(
        library_root=tmp_path,
        owner="demo-owner",
    )
    payload_path = tmp_path / "distilled" / "demo-owner.finance-outlook.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert any(path.name.endswith(".finance-outlook.json") for path in outputs)
    assert payload["totals"]["events"] == 1


def test_build_finance_outlook_payload_falls_back_to_source_digest(tmp_path):
    source_digest_path = tmp_path / "source.finance-digest.news-context.json"
    source_digest_path.write_text(
        json.dumps(
            {
                "kind": "finance_digest",
                "owner": "demo",
                "platform": "bilibili",
                "viewpoint_events": [
                    {
                        "event_id": "source-1",
                        "instrument": "MEITU",
                        "action": "watch",
                        "direction": "bullish",
                        "event_outcomes": {
                            "status": "priced",
                            "latest": {"status": "priced", "asset_return": 4.0, "max_drawdown": -1.0},
                        },
                    },
                ],
                "peer_context": {
                    "target_asset": "美图公司",
                    "target_ticker": "MEITU",
                    "industry": "软件",
                },
                "first_principles": {
                    "business_model": "工具订阅化",
                },
                "open_questions": ["source q"],
                "source_gaps": ["source gap"],
                "methodology_signals": ["source methodology"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    digest = {
        "kind": "finance_digest",
        "owner": "demo",
        "platform": "bilibili",
        "viewpoint_events": [],
        "source_digest_path": str(source_digest_path),
    }

    payload = build_finance_outlook_payload(digest)

    assert payload["totals"]["events"] == 1
    assert payload["peer_context"]["target_asset"] == "美图公司"
    assert payload["first_principles"]["business_model"] == "工具订阅化"
    assert payload["open_questions"] == ["source q"]
    assert payload["source_gaps"] == ["source gap"]
    assert payload["methodology_signals"] == ["source methodology"]


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
