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


def test_build_finance_outlook_payload_and_html(tmp_path, monkeypatch):
    monkeypatch.setattr("seed.reports.finance_outlook.fetch_yahoo_chart_history", lambda *args, **kwargs: [])
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
        "company_assets": {
            "logo": {
                "title": "Demo logo",
                "url": "https://example.test/logo.png",
                "source_title": "Demo IR visual assets",
                "source_url": "https://example.test/brand",
                "license_note": "official demo source",
            },
            "product_images": [
                {
                    "title": "Demo product",
                    "url": "https://example.test/product.jpg",
                    "caption": "核心产品样例",
                    "source_title": "Demo product page",
                    "source_url": "https://example.test/product",
                }
            ],
            "product_names": ["Demo Cloud", "Demo AI"],
            "usage_note": "视觉资产仅用于报告识别。",
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
        "market_context": {
            "current_price": 20.0,
            "as_of": "2026-05-19 16:00 HKT",
            "day_change_pct": -0.5,
            "one_week_return_pct": -2.0,
            "one_month_return_pct": -5.0,
            "fifty_two_week_low": 16.0,
            "fifty_two_week_high": 40.0,
            "analyst_target_average": 30.0,
            "analyst_target_median": 28.0,
            "analyst_target_average_upside_pct": 50.0,
            "analyst_target_low": 18.0,
            "analyst_target_high": 44.0,
            "analyst_sample_size": 12,
            "analyst_consensus_rating": "BUY",
            "price_source_note": "当前价来自 market-source，属于二级行情数据。",
            "data_quality_notes": ["客户级交付前需要用交易所或付费行情源复核。"],
            "source_refs": [{"title": "market-source", "url": "https://example.test"}],
            "next_events": [{"date": "2026-05-26", "event": "earnings"}],
            "historical_events": [
                {
                    "date": "2026-05-15",
                    "event": "Demo product launch",
                    "category": "product",
                    "relevance": "用于测试历史事件标注。",
                    "source_title": "Demo source",
                    "source_url": "https://example.test/event",
                }
            ],
            "historical_prices": [
                {"date": "May 15", "open": 19.0, "high": 20.0, "low": 18.0, "close": 19.5},
                {"date": "May 18", "open": 19.5, "high": 21.0, "low": 19.0, "close": 20.0},
            ],
        },
        "market_scenarios": {
            "anchor_price": 20.0,
            "anchor_price_date": "2026-05-19",
            "method": "market_valuation_context",
            "base_case": {
                "target_price": 30.0,
                "confidence": 0.7,
                "method": "analyst average target",
                "evidence_refs": ["market-source", "https://example.test/target"],
            },
            "upside_case": {
                "target_price": 40.0,
                "confidence": 0.6,
                "method": "52-week high",
                "evidence_refs": ["market-source"],
            },
            "downside_case": {
                "target_price": 18.0,
                "confidence": 0.6,
                "method": "analyst low target",
                "evidence_refs": ["market-source"],
            },
        },
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
    assert payload["company_assets"]["logo"]["title"] == "Demo logo"
    assert payload["company_assets"]["products"][0]["title"] == "Demo product"
    assert payload["scenarios"]["status"] == "ok"
    assert payload["scenarios"]["method"] == "market_valuation_context"
    assert payload["scenarios"]["base_case"]["status"] == "estimated"
    assert payload["scenarios"]["base_case"]["returns"] == 50.0
    assert payload["scenarios"]["upside_case"]["returns"] == 100.0
    assert payload["scenarios"]["downside_case"]["returns"] == -10.0
    assert payload["consensus_diagnostics"]["status"] == "ok"
    assert payload["consensus_diagnostics"]["returns"]["high"] == 120.0
    assert payload["consensus_diagnostics"]["dispersion_pct"] == 130.0
    assert payload["consensus_diagnostics"]["conflict_level"] == "high"
    assert payload["research_methodology"]["overall_score"] > 0
    assert payload["research_methodology"]["coverage"]
    assert payload["market_context"]["historical_price_coverage"]["meets_three_year_minimum"] is False
    assert payload["user_value"]["cards"]
    assert "普通用户" in " ".join(payload["user_value"]["audience"])
    assert payload["totals"]["overall_upside"] == 100.0
    assert payload["totals"]["overall_downside"] == -10.0
    assert payload["asset_rollups"][0]["target_prices"]["upside_target"] is not None
    assert payload["asset_rollups"][1]["target_prices"]["downside_target"] is not None
    assert "AI Coding（如 Claude Code、Cursor、Copilot 等）" in " ".join(payload["aicoding_signals"])
    assert payload["aicoding_signals"]
    assert "AI 代码工具替代压力" in payload["risk_flags"]
    assert "demo - 财经观点前瞻研判" in html
    assert "公司与产品识别" in html
    assert "Demo logo" in html
    assert "Demo product" in html
    assert "https://example.test/brand" in html
    assert "https://example.test/product" in html
    assert "时间覆盖" in html
    assert "同类公司（事实输入）" in html
    assert "AI Coding 结构性变量（软件护城河）" in html
    assert "目标价位草案（市场/事件口径）" in html
    assert "上行目标" in html
    assert "市场锚点（真实检索口径）" in html
    assert "数据口径与保存" in html
    assert "成熟研报方法论映射" in html
    assert "用户视角：这份报告有什么价值" in html
    assert "普通用户" in html
    assert "不提供买入/卖出指令" in html
    assert "一致预期与目标价分歧" in html
    assert "数据覆盖度 / 交付自检" in html
    assert "目标价跨度" in html
    assert "高分歧" in html
    assert "CFA equity valuation" in html
    assert "FinRobot report pipeline" in html
    assert "当前价来自 market-source" in html
    assert "情景锚点（市场/估值口径）" in html
    assert "历史 K 线 + 关键时间点 + 情景路径" in html
    assert "历史 K 线覆盖" in html
    assert "历史 K 线不足 3 年" in html
    assert "finance-kline-chart" in html
    assert "lightweight-charts-5.2.0.standalone.production.js" in html
    assert "TradingView Lightweight Charts" in html
    assert "finance-chart-data" in html
    assert "createPriceLine" in html
    assert "createLineSeries" in html
    assert "createSeriesMarkers" in html
    assert "scenarioPaths" in html
    assert "eventMarkers" in html
    assert "historicalEventMarkers" in html
    assert "futureProjectionPointCount" in html
    assert "chart-time-rail" in html
    assert "同轴事件时间线" in html
    assert "rail-future-event" in html
    assert "chart-event-history" in html
    assert "Demo product launch" in html
    assert "https://example.test/event" in html
    assert "finance-event-timeline" in html
    assert "情景路径（非K线）" in html
    assert "earnings" in html
    assert "目标价区（非K线）" in html
    assert "目标价水平范式" in html
    assert "不是未来每日K线" in html
    assert '<a href="https://example.test/target" target="_blank" rel="noopener noreferrer">' in html
    assert '<a href="https://example.test" target="_blank" rel="noopener noreferrer">market-source</a>' in html
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
