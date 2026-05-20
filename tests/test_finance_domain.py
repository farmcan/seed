import json
from datetime import UTC, datetime

from seed.domains.finance import (
    build_finance_digest_artifact,
    build_market_data_record,
    enrich_finance_digest_with_news_context,
    enrich_finance_digest_with_prices,
    finance_digest_output_path,
    news_context_finance_digest_output_path,
    parse_stooq_daily_csv,
    parse_yahoo_chart_json,
    write_finance_digest_artifact,
)


def test_build_finance_digest_artifact_groups_signals(tmp_path):
    first = tmp_path / "one.finance-signals.json"
    second = tmp_path / "two.finance-signals.json"
    first.write_text(
        json.dumps(
            {
                "title": "One",
                "owner": "demo",
                "platform": "bilibili",
                "stance_summary": "watching AI",
                "instruments": [{"name": "AI"}],
                "recommendations": [{"instrument": "AI", "action": "watch"}],
                "macro_theses": [{"thesis": "liquidity matters"}],
                "methodology_signals": [{"method": "event catalyst"}],
                "risk_flags": ["not financial advice"],
                "evidence_gaps": ["missing price data"],
            }
        ),
        encoding="utf-8",
    )
    second.write_text(
        json.dumps(
            {
                "title": "Two",
                "owner": "demo",
                "platform": "bilibili",
                "instruments": [{"name": "AI"}],
                "recommendations": [{"instrument": "AI", "action": "hold"}],
                "methodology_signals": [{"method": "event catalyst"}],
                "risk_flags": [],
                "evidence_gaps": [],
            }
        ),
        encoding="utf-8",
    )

    artifact = build_finance_digest_artifact(
        signal_paths=[first, second],
        owner="demo",
        published_after=datetime(2026, 5, 10, tzinfo=UTC),
        published_before=datetime(2026, 5, 14, tzinfo=UTC),
        video_metadata_by_title={
            "One": {"published_at": "2026-05-12T00:00:00+00:00"},
            "Two": {"published_at": "2026-05-01T00:00:00+00:00"},
        },
    )

    assert artifact["videos_analyzed"] == 1
    assert artifact["totals"]["recommendations"] == 1
    assert artifact["totals"]["viewpoint_events"] == 1
    assert artifact["instruments"][0]["name"] == "AI"
    assert artifact["instruments"][0]["mentions"] == 1
    assert artifact["methodology_signals"][0]["method"] == "event catalyst"
    assert artifact["risk_flags"] == ["not financial advice"]
    assert artifact["viewpoint_events"][0]["event_id"].startswith("one-ai-")


def test_finance_digest_output_path_and_write(tmp_path):
    path = finance_digest_output_path(
        library_root=tmp_path,
        owner="王财经",
        published_after=datetime(2026, 5, 4, tzinfo=UTC),
        published_before=datetime(2026, 5, 14, tzinfo=UTC),
    )
    write_finance_digest_artifact(path, {"kind": "finance_digest"})

    assert path == tmp_path / "distilled" / "王财经.20260504-to-20260514.finance-digest.json"
    assert json.loads(path.read_text(encoding="utf-8"))["kind"] == "finance_digest"


def test_parse_stooq_daily_csv_and_market_data_record():
    history = parse_stooq_daily_csv(
        """Date,Open,High,Low,Close,Volume
2026-05-11,10,11,9,10,100
2026-05-12,10,12,10,12,100
"""
    )
    record = build_market_data_record(
        ticker="demo.us",
        published_at=datetime(2026, 5, 12, 12, tzinfo=UTC),
        history=history,
        benchmark_ticker=None,
        benchmark_history=[],
        provider="stooq",
    )

    assert record["status"] == "priced"
    assert history[0]["open"] == 10
    assert history[0]["high"] == 11
    assert history[0]["low"] == 9
    assert history[0]["volume"] == 100
    assert record["published_close"] == 12
    assert record["latest_close"] == 12
    assert record["return_pct"] == 0.0


def test_parse_yahoo_chart_json():
    history = parse_yahoo_chart_json(
        json.dumps(
            {
                "chart": {
                    "result": [
                        {
                            "timestamp": [1779177600, 1779264000],
                            "indicators": {
                                "quote": [
                                    {
                                        "open": [30.6, 30.8],
                                        "high": [31.0, 31.2],
                                        "low": [30.3, 30.5],
                                        "close": [30.64, None],
                                        "volume": [89701722, 0],
                                    }
                                ]
                            },
                        }
                    ]
                }
            }
        )
    )

    assert history == [
        {
            "date": "2026-05-19",
            "open": 30.6,
            "high": 31.0,
            "low": 30.3,
            "close": 30.64,
            "volume": 89701722,
        }
    ]


def test_enrich_finance_digest_with_prices(monkeypatch):
    digest = {
        "kind": "finance_digest",
        "recommendations": [{"instrument": "AI", "video_title": "One"}],
        "viewpoint_events": [
            {
                "event_id": "one-ai-1",
                "instrument": "AI",
                "video_title": "One",
                "action": "watch",
            }
        ],
        "video_records": [{"title": "One", "published_at": "2026-05-11T00:00:00+00:00"}],
        "totals": {"recommendations": 1, "viewpoint_events": 1},
    }

    def fake_history(ticker):
        return [
            {"date": "2026-05-10", "close": 10.0},
            {"date": "2026-05-12", "close": 12.0},
        ]

    monkeypatch.setattr("seed.domains.finance.fetch_stooq_daily_history", fake_history)

    enriched = enrich_finance_digest_with_prices(
        digest,
        ticker_map={"AI": "demo.us", "ai": "demo.us"},
        benchmark_ticker=None,
    )

    market_data = enriched["recommendations"][0]["market_data"]
    assert enriched["kind"] == "priced_finance_digest"
    assert market_data["status"] == "priced"
    assert market_data["return_pct"] == 20.0
    assert enriched["totals"]["priced_recommendations"] == 1
    assert enriched["totals"]["priced_viewpoint_events"] == 1
    outcomes = enriched["viewpoint_events"][0]["event_outcomes"]
    assert outcomes["status"] == "priced"
    assert outcomes["horizons"]["1D"]["status"] == "priced"
    assert outcomes["horizons"]["1D"]["asset_return"] == 20.0
    assert outcomes["latest"]["status"] == "priced"


def test_enrich_finance_digest_with_news_context(tmp_path):
    news_digest = tmp_path / "ai.news-digest.json"
    news_digest.write_text(
        json.dumps(
            {
                "kind": "news_facts_digest",
                "topic": "AI supply chain",
                "facts": [
                    {
                        "fact_id": "f1",
                        "statement": "Nvidia reported strong datacenter demand.",
                        "status": "reported",
                        "entities": ["Nvidia", "AI"],
                        "source_urls": ["https://example.test/nvda"],
                        "source_titles": ["Example"],
                    }
                ],
                "industry_impacts": [
                    {
                        "industry": "AI",
                        "mechanism": "Datacenter demand may affect chip suppliers.",
                        "possible_direction": "mixed",
                        "affected_entities": ["Nvidia"],
                        "fact_refs": ["f1"],
                    }
                ],
                "market_relevance": [
                    {
                        "asset_or_sector": "AI",
                        "relevance": "Relevant to AI hardware equities.",
                        "fact_refs": ["f1"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    digest = {
        "kind": "finance_digest",
        "viewpoint_events": [
            {
                "event_id": "one-ai-1",
                "instrument": "AI",
                "ticker": "NVDA.US",
                "video_title": "One",
                "action": "watch",
            }
        ],
        "totals": {"viewpoint_events": 1},
    }

    enriched = enrich_finance_digest_with_news_context(
        digest,
        news_digest_paths=[news_digest],
    )

    event_context = enriched["viewpoint_events"][0]["news_context"][0]
    assert enriched["kind"] == "finance_digest_with_news_context"
    assert enriched["totals"]["events_with_news_context"] == 1
    assert event_context["fact_refs"] == ["f1"]
    assert event_context["source_urls"] == ["https://example.test/nvda"]
    assert news_context_finance_digest_output_path(
        digest_path=tmp_path / "demo.finance-digest.json"
    ) == tmp_path / "demo.finance-digest.news-context.json"
